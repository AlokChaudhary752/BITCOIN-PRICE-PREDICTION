"""
Configuration and constants for BTC Oracle ML Engine.
"""
from pathlib import Path

# Paths
ML_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = ML_PACKAGE_ROOT.parent.parent
DATA_DIR = ML_PACKAGE_ROOT / "data_store"
MODEL_REGISTRY_DIR = ML_PACKAGE_ROOT / "model_registry"
REPORTS_DIR = ML_PACKAGE_ROOT / "reports"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODEL_REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Forecasting Horizons in hours
HORIZONS: dict[str, int] = {
    "1h": 1,
    "4h": 4,
    "24h": 24,
    "7d": 168,
    "30d": 720,
}

# Quantiles for probabilistic distribution
QUANTILES: list[float] = [0.05, 0.25, 0.50, 0.75, 0.95]

# Nominal target coverage for prediction intervals
NOMINAL_COVERAGE_90: float = 0.90
NOMINAL_COVERAGE_50: float = 0.50

# Market Regimes
REGIME_TRENDING_BULL = "trending_bull"
REGIME_RANGING = "ranging"
REGIME_HIGH_VOLATILITY = "high_volatility"

REGIME_LABELS: dict[int, str] = {
    0: REGIME_RANGING,
    1: REGIME_TRENDING_BULL,
    2: REGIME_HIGH_VOLATILITY,
}

# Public Data Source Endpoints (No API keys required)
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
FEAR_GREED_URL = "https://api.alternative.me/fng/?limit=0&format=json"
MEMPOOL_FEES_URL = "https://mempool.space/api/v1/fees/recommended"
MEMPOOL_BLOCKS_URL = "https://mempool.space/api/v1/blocks"
COINGECKO_GLOBAL_URL = "https://api.coingecko.com/api/v3/global"

# Purged Walk-Forward Evaluation Parameters
WF_TRAIN_WINDOW_HOURS = 24 * 365  # 1 year expanding base
WF_STEP_HOURS = 24 * 30  # Step forward 1 month
WF_PURGE_HOURS = 720  # Max horizon purge gap to avoid overlap leakage
WF_EMBARGO_HOURS = 48  # Post-split embargo to prevent auto-correlation leakage
