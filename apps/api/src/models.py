"""
SQLAlchemy 2 Data Models.
Institutional audit logs, refresh token families, probabilistic predictions, and portfolios.
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from apps.api.src.database import Base


def get_utc_now():
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(32), default="user", nullable=False)  # 'user' | 'admin'
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    totp_secret = Column(String(64), nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    portfolio = relationship("PaperPortfolio", back_populates="user", uselist=False, cascade="all, delete-orphan")


class RefreshToken(Base):
    """
    Refresh Token with Token Family Tracking.
    Enforces automatic family revocation upon reuse attempt.
    """
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    family_id = Column(String(36), nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")


class Prediction(Base):
    """
    Auditable Live Probabilistic Prediction record.
    Written at issuance, then scored by the background scheduler once actual price realizes.
    """
    __tablename__ = "predictions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)
    horizon = Column(String(16), nullable=False, index=True)  # '1h', '4h', '24h', '7d', '30d'
    current_price = Column(Float, nullable=False)
    point_forecast = Column(Float, nullable=False)
    expected_return_pct = Column(Float, nullable=False)
    prob_up = Column(Float, nullable=False)
    agreement_score = Column(Float, nullable=False)
    risk_score = Column(Integer, nullable=False)
    signal = Column(String(32), nullable=False)
    signal_level = Column(Integer, nullable=False)
    confidence_level = Column(String(32), nullable=False)

    # Prediction intervals
    interval_50_lower = Column(Float, nullable=False)
    interval_50_upper = Column(Float, nullable=False)
    interval_90_lower = Column(Float, nullable=False)
    interval_90_upper = Column(Float, nullable=False)

    # Quantiles
    q05 = Column(Float, nullable=False)
    q25 = Column(Float, nullable=False)
    q50 = Column(Float, nullable=False)
    q75 = Column(Float, nullable=False)
    q95 = Column(Float, nullable=False)

    # Scoring columns (evaluated ex-post)
    actual_price = Column(Float, nullable=True)
    error = Column(Float, nullable=True)  # actual_price - point_forecast
    abs_error = Column(Float, nullable=True)
    pinball_loss = Column(Float, nullable=True)
    is_scored = Column(Boolean, default=False, nullable=False, index=True)
    scored_at = Column(DateTime(timezone=True), nullable=True)

    # Provenance
    model_version = Column(String(32), default="1.0.0", nullable=False)
    dataset_hash = Column(String(64), nullable=True)

    __table_args__ = (
        Index("idx_pred_horizon_time", "horizon", "timestamp"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(32), nullable=False)  # 'price' | 'signal' | 'regime'
    condition = Column(String(32), nullable=False)  # 'above' | 'below' | 'change'
    threshold = Column(Float, nullable=True)
    target_value = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    user = relationship("User", back_populates="alerts")


class PaperPortfolio(Base):
    __tablename__ = "paper_portfolios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    initial_capital = Column(Float, default=100000.0, nullable=False)
    cash = Column(Float, default=100000.0, nullable=False)
    btc_balance = Column(Float, default=0.0, nullable=False)
    total_equity = Column(Float, default=100000.0, nullable=False)
    realized_pnl = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    user = relationship("User", back_populates="portfolio")
    trades = relationship("PaperTrade", back_populates="portfolio", cascade="all, delete-orphan")


class PaperTrade(Base):
    __tablename__ = "paper_trades"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String(36), ForeignKey("paper_portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    side = Column(String(8), nullable=False)  # 'BUY' | 'SELL'
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)  # BTC amount
    fee = Column(Float, default=0.0, nullable=False)
    value = Column(Float, nullable=False)
    pnl = Column(Float, default=0.0, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    portfolio = relationship("PaperPortfolio", back_populates="trades")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True, index=True)
    action = Column(String(64), nullable=False, index=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
