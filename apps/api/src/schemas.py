"""
Pydantic v2 API Request and Response Schemas.
Full typing for TypeScript OpenAPI generation.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ==========================================
# AUTH SCHEMAS
# ==========================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False
    totp_code: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    two_factor_enabled: bool
    created_at: datetime


class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code_uri: str
    recovery_codes: List[str]


class TwoFactorVerifyRequest(BaseModel):
    code: str


# ==========================================
# MARKET SCHEMAS
# ==========================================

class LivePriceResponse(BaseModel):
    symbol: str = "BTCUSDT"
    price: float
    change_24h_pct: float
    high_24h: float
    low_24h: float
    volume_24h: float
    realized_volatility: float
    timestamp: datetime


class CandleItem(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketHistoryResponse(BaseModel):
    symbol: str = "BTCUSDT"
    interval: str
    count: int
    candles: List[CandleItem]


class OrderBookLevel(BaseModel):
    price: float
    quantity: float


class OrderBookResponse(BaseModel):
    symbol: str = "BTCUSDT"
    timestamp: datetime
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    imbalance_ratio: float


class OnChainMetricsResponse(BaseModel):
    fastest_fee: float
    half_hour_fee: float
    hour_fee: float
    minimum_fee: float
    taker_buy_ratio: float
    volume_momentum_24h: float
    average_trade_size: float


# ==========================================
# FORECAST SCHEMAS
# ==========================================

class IntervalBand(BaseModel):
    lower: float
    upper: float
    nominal_coverage: float
    empirical_coverage: float


class QuantilesDict(BaseModel):
    q05: float
    q25: float
    q50: float
    q75: float
    q95: float


class HorizonForecast(BaseModel):
    horizon: str
    current_price: float
    point_forecast: float
    expected_return_pct: float
    prob_up: float
    agreement_score: float
    risk_score: int
    signal: str
    signal_level: int
    confidence_level: str
    low_confidence_flag: bool
    interval_50: IntervalBand
    interval_90: IntervalBand
    quantiles: QuantilesDict
    per_model_median: Dict[str, float]


class MarketRegime(BaseModel):
    label: str
    confidence: float
    probabilities: Dict[str, float]


class DriverImpact(BaseModel):
    feature: str
    description: str
    value: float
    shap_value: float
    abs_impact: float
    direction: str


class PredictionExplanation(BaseModel):
    narrative: str
    top_drivers: List[DriverImpact]


class PredictionResponse(BaseModel):
    version: str
    timestamp: datetime
    current_price: float
    market_regime: MarketRegime
    primary_signal: Dict[str, Any]
    horizons: Dict[str, HorizonForecast]
    explanation: PredictionExplanation


class PredictionHistoryItem(BaseModel):
    id: str
    timestamp: datetime
    horizon: str
    current_price: float
    point_forecast: float
    actual_price: Optional[float]
    abs_error: Optional[float]
    is_scored: bool
    signal: str
    model_version: str


# ==========================================
# ANALYSIS & BACKTEST SCHEMAS
# ==========================================

class BacktestRequest(BaseModel):
    initial_capital: float = Field(default=100000.0, ge=1000.0)
    fee_rate: float = Field(default=0.0006, ge=0.0)  # 6 bps taker fee
    slippage: float = Field(default=0.0004, ge=0.0)  # 4 bps slippage
    stop_loss_pct: float = Field(default=0.02, ge=0.005)
    risk_per_trade_pct: float = Field(default=0.02, ge=0.005)
    confidence_threshold: float = Field(default=65.0, ge=50.0)
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class EquityPoint(BaseModel):
    timestamp: datetime
    strategy_equity: float
    benchmark_equity: float
    drawdown_pct: float


class BacktestTradeLog(BaseModel):
    entry_time: datetime
    exit_time: datetime
    side: str
    entry_price: float
    exit_price: float
    return_pct: float
    pnl: float
    reason: str


class BacktestResponse(BaseModel):
    initial_capital: float
    final_equity: float
    total_return_pct: float
    benchmark_return_pct: float
    cagr_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    profit_factor: float
    total_trades: int
    equity_curve: List[EquityPoint]
    trades: List[BacktestTradeLog]


# ==========================================
# USER & PORTFOLIO SCHEMAS
# ==========================================

class AlertCreate(BaseModel):
    alert_type: str  # 'price' | 'signal' | 'regime'
    condition: str  # 'above' | 'below' | 'change'
    threshold: Optional[float] = None
    target_value: Optional[str] = None


class AlertResponse(BaseModel):
    id: str
    alert_type: str
    condition: str
    threshold: Optional[float]
    target_value: Optional[str]
    is_active: bool
    triggered_at: Optional[datetime]
    created_at: datetime


class PaperTradeCreate(BaseModel):
    side: str  # 'BUY' | 'SELL'
    amount: float = Field(gt=0.0)


class PaperTradeResponse(BaseModel):
    id: str
    side: str
    price: float
    amount: float
    value: float
    fee: float
    pnl: float
    timestamp: datetime


class PaperPortfolioResponse(BaseModel):
    id: str
    initial_capital: float
    cash: float
    btc_balance: float
    total_equity: float
    realized_pnl: float
    current_btc_price: float
    unrealized_pnl: float
    recent_trades: List[PaperTradeResponse]
