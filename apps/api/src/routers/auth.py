"""
Authentication Router.
Registration, Argon2 login, rotating refresh tokens with family reuse revocation, and TOTP 2FA.
"""
import secrets
from datetime import UTC, datetime, timedelta

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.config import settings
from apps.api.src.database import get_db
from apps.api.src.models import AuditLog, PaperPortfolio, User
from apps.api.src.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    UserResponse,
)
from apps.api.src.security import (
    get_current_user,
    hash_password,
    issue_token_family,
    rotate_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

REFRESH_COOKIE_NAME = "btc_oracle_refresh"


def set_refresh_cookie(response: Response, raw_token: str):
    """Set secure httpOnly refresh token cookie."""
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=False if settings.ENVIRONMENT == "development" else True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account with Argon2 password hashing."""
    stmt = select(User).where(User.email == req.email.lower())
    res = await db.execute(stmt)
    if res.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")

    # Determine role: first user is admin, otherwise user
    count_stmt = select(User)
    count_res = await db.execute(count_stmt)
    role = "admin" if len(count_res.scalars().all()) == 0 else "user"

    new_user = User(
        email=req.email.lower(),
        password_hash=hash_password(req.password),
        full_name=req.full_name,
        role=role,
        is_active=True,
        is_verified=True,  # Dev auto-verification
    )
    db.add(new_user)
    await db.flush()

    # Initialize paper portfolio with $100k
    portfolio = PaperPortfolio(
        user_id=new_user.id,
        initial_capital=100000.0,
        cash=100000.0,
        btc_balance=0.0,
        total_equity=100000.0,
    )
    db.add(portfolio)

    audit = AuditLog(
        user_id=new_user.id,
        action="USER_REGISTERED",
        details=f"User registered with role {role}",
    )
    db.add(audit)
    await db.commit()

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        is_active=new_user.is_active,
        is_verified=new_user.is_verified,
        two_factor_enabled=bool(new_user.totp_secret),
        created_at=new_user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Login and receive short-lived JWT access token plus rotating httpOnly refresh cookie."""
    stmt = select(User).where(User.email == req.email.lower())
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    # Check lockout
    now = datetime.now(UTC)
    if user.locked_until:
        locked_until_utc = user.locked_until.replace(tzinfo=UTC) if user.locked_until.tzinfo is None else user.locked_until
        if locked_until_utc > now:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Account temporarily locked due to consecutive failed login attempts. Please try again later.",
            )

    if not verify_password(req.password, user.password_hash):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= 5:
            user.locked_until = now + timedelta(minutes=15)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Account locked: 5 consecutive failed attempts. Locked for 15 minutes.",
            )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    # Reset failure counter on success
    user.failed_login_attempts = 0
    user.locked_until = None

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")

    # 2FA Check if enabled
    if user.totp_secret:
        if not req.totp_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="2FA_REQUIRED: Two-factor authentication code required.",
            )
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(req.totp_code, valid_window=1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA code.")

    access_token, raw_refresh = await issue_token_family(user.id, db)
    set_refresh_cookie(response, raw_refresh)

    audit = AuditLog(
        user_id=user.id,
        action="USER_LOGIN_SUCCESS",
        ip_address=request.client.host if request.client else None,
        details="Login successful",
    )
    db.add(audit)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Rotate refresh token. Reads refresh token from httpOnly cookie.
    Enforces automatic family revocation upon reuse attempt.
    """
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        # Check Authorization header fallback
        auth_hdr = request.headers.get("X-Refresh-Token")
        if auth_hdr:
            raw_token = auth_hdr
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token cookie missing.")

    new_access, new_refresh, user_id = await rotate_refresh_token(raw_token, db, request)
    set_refresh_cookie(response, new_refresh)

    return TokenResponse(
        access_token=new_access,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(response: Response):
    """Clear refresh token cookie."""
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Return authenticated user profile."""
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        two_factor_enabled=bool(user.totp_secret),
        created_at=user.created_at,
    )


@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Generate TOTP secret, provisioning URI, and recovery codes."""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user.email, issuer_name="BTC Oracle")
    recovery_codes = [secrets.token_hex(4).upper() for _ in range(8)]

    # Temporary save in user record
    user.totp_secret = secret
    await db.commit()

    return TwoFactorSetupResponse(
        secret=secret,
        qr_code_uri=uri,
        recovery_codes=recovery_codes,
    )


@router.post("/2fa/verify")
async def verify_2fa(
    req: TwoFactorVerifyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify code and activate 2FA."""
    if not user.totp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA setup not initiated.")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(req.code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code.")

    return {"message": "Two-factor authentication verified and enabled."}
