"""
Security, Argon2 Hashing, JWT Token Rotation, and RBAC.
Enforces institutional security: token family reuse revocation, httpOnly cookies, Argon2.
"""
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.config import settings
from apps.api.src.database import get_db
from apps.api.src.models import AuditLog, RefreshToken, User

ph = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# ==========================================
# ARGON2 PASSWORD HASHING
# ==========================================

def hash_password(password: str) -> str:
    """Hash password using Argon2id."""
    return ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against Argon2id hash."""
    try:
        return ph.verify(hashed, password)
    except (VerifyMismatchError, Exception):
        return False


# ==========================================
# JWT ACCESS & REFRESH TOKENS
# ==========================================

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create short-lived JWT access token (15 mins)."""
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def generate_refresh_token() -> str:
    """Generate high-entropy random refresh token."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Compute SHA-256 hash of token for safe DB storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def issue_token_family(user_id: str, db: AsyncSession) -> tuple[str, str]:
    """Issue a new access token and a root refresh token in a new token family."""
    access_token = create_access_token({"sub": user_id})
    raw_refresh = generate_refresh_token()
    family_id = secrets.token_hex(16)
    token_hash = hash_token(raw_refresh)
    expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    token_rec = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        family_id=family_id,
        is_revoked=False,
        expires_at=expires_at,
    )
    db.add(token_rec)
    await db.commit()

    return access_token, raw_refresh


async def rotate_refresh_token(raw_token: str, db: AsyncSession, request: Request) -> tuple[str, str, str]:
    """
    Rotate refresh token with Token Family Reuse Detection.
    If a previously revoked token is presented, revoke the entire token family immediately.
    Returns: (new_access_token, new_raw_refresh, user_id)
    """
    tok_hash = hash_token(raw_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == tok_hash)
    res = await db.execute(stmt)
    token_rec = res.scalars().first()

    if not token_rec:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    # REUSE DETECTION: Token was already revoked!
    if token_rec.is_revoked:
        # Revoke entire token family to defend against stolen tokens
        revoke_family_stmt = (
            select(RefreshToken).where(RefreshToken.family_id == token_rec.family_id)
        )
        fam_res = await db.execute(revoke_family_stmt)
        for t in fam_res.scalars().all():
            t.is_revoked = True

        # Log security breach in audit
        audit = AuditLog(
            user_id=token_rec.user_id,
            action="SECURITY_BREACH_REFRESH_TOKEN_REUSE",
            ip_address=request.client.host if request.client else None,
            details=f"Token reuse attempt detected on family {token_rec.family_id}. Family revoked.",
        )
        db.add(audit)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Security breach detected: Refresh token reuse. Entire session revoked.",
        )

    # Check expiration
    now = datetime.now(UTC)
    if token_rec.expires_at.replace(tzinfo=UTC) < now:
        token_rec.is_revoked = True
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired.",
        )

    # Mark current token as revoked (used)
    token_rec.is_revoked = True

    # Issue child token in same family
    new_raw_refresh = generate_refresh_token()
    new_hash = hash_token(new_raw_refresh)
    new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    child_rec = RefreshToken(
        user_id=token_rec.user_id,
        token_hash=new_hash,
        family_id=token_rec.family_id,
        is_revoked=False,
        expires_at=new_expires_at,
    )
    db.add(child_rec)
    await db.commit()

    new_access_token = create_access_token({"sub": token_rec.user_id})
    return new_access_token, new_raw_refresh, token_rec.user_id


# ==========================================
# AUTH DEPENDENCIES & RBAC
# ==========================================

async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency returning authenticated user from Bearer token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject.")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials.")

    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account inactive or missing.")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """RBAC: requires admin role."""
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator privileges required.")
    return user
