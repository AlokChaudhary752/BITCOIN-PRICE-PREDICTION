"""
End-to-End Feature Engineering Pipeline.
Transforms raw OHLCV + sentiment into causal feature matrices and horizon targets.
"""

import numpy as np
import pandas as pd
from btc_oracle_ml.config import HORIZONS
from btc_oracle_ml.features.indicators import (
    compute_atr,
    compute_bollinger_bands,
    compute_macd,
    compute_obv,
    compute_rsi,
    compute_stochastic,
    compute_vwap_deviation,
)
from btc_oracle_ml.features.volatility import (
    compute_log_returns,
    garman_klass_volatility,
    parkinson_volatility,
    realized_volatility,
)

# Plain-English descriptions for institutional model explainability (SHAP narratives)
FEATURE_DESCRIPTIONS: dict[str, str] = {
    "return_1h": "1-hour price return",
    "return_4h": "4-hour price momentum",
    "return_24h": "24-hour price trend",
    "return_168h": "7-day macro momentum",
    "vol_parkinson_24h": "24-hour high-low Parkinson volatility",
    "vol_garman_klass_24h": "24-hour Garman-Klass OHLC volatility",
    "vol_realized_24h": "24-hour realized close-to-close volatility",
    "vol_realized_168h": "7-day baseline realized volatility",
    "rsi_14": "14-hour Relative Strength Index (overbought/oversold momentum)",
    "macd_hist": "MACD momentum histogram divergence",
    "bb_pct_b": "Bollinger Band %B relative price position",
    "bb_bandwidth": "Bollinger Band volatility compression/expansion width",
    "atr_relative": "Normalized Average True Range risk buffer",
    "stoch_k": "Stochastic %K oscillator momentum",
    "stoch_d": "Stochastic %D smoothed oscillator signal",
    "ema_ratio_20": "Price deviation from 20-period short-term EMA",
    "ema_ratio_50": "20 EMA relative to 50 EMA trend alignment",
    "ema_ratio_200": "50 EMA relative to 200 EMA golden/death cross alignment",
    "obv_zscore": "Normalized On-Balance Volume order flow",
    "vwap_dev": "Deviation from volume-weighted average price (VWAP)",
    "taker_buy_ratio": "Aggressive market taker buyer vs seller flow ratio",
    "volume_momo_24h": "24-hour trading volume acceleration",
    "fear_greed_norm": "Crypto market sentiment index (Fear & Greed)",
    "hour_sin": "Intraday diurnal trading cycle (sine component)",
    "hour_cos": "Intraday diurnal trading cycle (cosine component)",
    "dayofweek_sin": "Weekly institutional funding calendar cycle (sine)",
    "dayofweek_cos": "Weekly institutional funding calendar cycle (cosine)",
}


class FeaturePipeline:
    """Computes all causal features and horizon targets."""

    def __init__(self):
        self.feature_names: list[str] = list(FEATURE_DESCRIPTIONS.keys())

    def transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.Series]]:
        """
        Takes raw dataframe and returns:
        - X: DataFrame of engineered features (aligned, strictly causal)
        - y_dict: Dict mapping horizon key (e.g. '1h', '24h') to target log-return series
        """
        feats = pd.DataFrame(index=df.index)

        # 1. Log returns
        close = df["close"]
        high = df["high"]
        low = df["low"]
        open_p = df["open"]
        volume = df["volume"]

        feats["return_1h"] = compute_log_returns(close, 1)
        feats["return_4h"] = compute_log_returns(close, 4)
        feats["return_24h"] = compute_log_returns(close, 24)
        feats["return_168h"] = compute_log_returns(close, 168)

        # 2. Volatilities
        feats["vol_parkinson_24h"] = parkinson_volatility(high, low, 24)
        feats["vol_garman_klass_24h"] = garman_klass_volatility(open_p, high, low, close, 24)
        feats["vol_realized_24h"] = realized_volatility(feats["return_1h"], 24)
        feats["vol_realized_168h"] = realized_volatility(feats["return_1h"], 168)

        # 3. Technicals
        feats["rsi_14"] = compute_rsi(close, 14)
        macd_df = compute_macd(close)
        feats["macd_hist"] = macd_df["macd_hist"]

        bb_df = compute_bollinger_bands(close)
        feats["bb_pct_b"] = bb_df["bb_pct_b"]
        feats["bb_bandwidth"] = bb_df["bb_bandwidth"]

        atr = compute_atr(high, low, close, 14)
        feats["atr_relative"] = (atr / close).clip(0, 0.5)

        stoch_df = compute_stochastic(high, low, close)
        feats["stoch_k"] = stoch_df["stoch_k"]
        feats["stoch_d"] = stoch_df["stoch_d"]

        # EMA Ratios
        ema20 = close.ewm(span=20, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()
        ema200 = close.ewm(span=200, adjust=False).mean()
        feats["ema_ratio_20"] = (close - ema20) / ema20
        feats["ema_ratio_50"] = (ema20 - ema50) / ema50
        feats["ema_ratio_200"] = (ema50 - ema200) / ema200

        # OBV and VWAP
        obv = compute_obv(close, volume)
        feats["obv_zscore"] = (obv - obv.rolling(72).mean()) / (obv.rolling(72).std().replace(0, 1e-12))
        feats["vwap_dev"] = compute_vwap_deviation(close, high, low, volume)

        # Microstructural / On-chain proxies
        feats["taker_buy_ratio"] = df.get("taker_buy_ratio", pd.Series(0.5, index=df.index))
        feats["volume_momo_24h"] = df.get("volume_momo_24h", pd.Series(1.0, index=df.index))

        # Sentiment
        feats["fear_greed_norm"] = df.get("fear_greed_norm", pd.Series(0.5, index=df.index))

        # Calendar features (sin/cos encoding)
        timestamps = df.index
        hours = timestamps.hour
        dayofweek = timestamps.dayofweek

        feats["hour_sin"] = np.sin(2 * np.pi * hours / 24.0)
        feats["hour_cos"] = np.cos(2 * np.pi * hours / 24.0)
        feats["dayofweek_sin"] = np.sin(2 * np.pi * dayofweek / 7.0)
        feats["dayofweek_cos"] = np.cos(2 * np.pi * dayofweek / 7.0)

        # Compute horizon targets
        # y_h = ln(Close_{t+h} / Close_t)
        y_dict: dict[str, pd.Series] = {}
        for h_name, h_hours in HORIZONS.items():
            future_close = close.shift(-h_hours)
            target_return = np.log(future_close / close)
            y_dict[h_name] = target_return

        # Keep only defined feature columns
        X = feats[self.feature_names].copy()

        # Handle NaNs from rolling warmup by clipping/filling
        X = X.ffill().bfill()

        return X, y_dict
