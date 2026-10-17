"""
Unit tests for Feature Pipeline and Causal Integrity.
"""
import numpy as np
import pandas as pd
import pytest
from btc_oracle_ml.evaluation.leakage import verify_feature_causality
from btc_oracle_ml.features.indicators import (
    compute_atr,
    compute_bollinger_bands,
    compute_macd,
    compute_rsi,
)
from btc_oracle_ml.features.volatility import (
    garman_klass_volatility,
    parkinson_volatility,
)


@pytest.fixture
def sample_ohlcv():
    dates = pd.date_range("2024-01-01", periods=100, freq="1h", name="timestamp")
    np.random.seed(42)
    prices = 50000.0 * np.exp(np.cumsum(np.random.normal(0, 0.005, 100)))
    df = pd.DataFrame(
        {
            "open": prices * 0.999,
            "high": prices * 1.005,
            "low": prices * 0.995,
            "close": prices,
            "volume": np.random.uniform(10, 100, 100),
            "quote_asset_volume": prices * np.random.uniform(10, 100, 100),
            "number_of_trades": np.random.randint(100, 500, 100),
            "taker_buy_base_volume": np.random.uniform(5, 50, 100),
        },
        index=dates,
    )
    return df


def test_volatility_estimators(sample_ohlcv):
    p_vol = parkinson_volatility(sample_ohlcv["high"], sample_ohlcv["low"], window=12)
    assert len(p_vol) == 100
    assert not np.isnan(p_vol.iloc[-1])
    assert (p_vol.dropna() > 0).all()

    gk_vol = garman_klass_volatility(
        sample_ohlcv["open"],
        sample_ohlcv["high"],
        sample_ohlcv["low"],
        sample_ohlcv["close"],
        window=12,
    )
    assert len(gk_vol) == 100
    assert (gk_vol.dropna() > 0).all()


def test_technical_indicators(sample_ohlcv):
    close = sample_ohlcv["close"]
    rsi = compute_rsi(close, 14)
    assert len(rsi) == 100
    assert (rsi.dropna() >= 0).all() and (rsi.dropna() <= 100).all()

    macd = compute_macd(close)
    assert "macd_hist" in macd.columns
    assert len(macd) == 100

    bb = compute_bollinger_bands(close)
    assert (bb["bb_upper"].dropna() >= bb["bb_lower"].dropna()).all()

    atr = compute_atr(sample_ohlcv["high"], sample_ohlcv["low"], close, 14)
    assert (atr.dropna() > 0).all()


def test_feature_causality_invariance(sample_ohlcv):
    assert verify_feature_causality(sample_ohlcv)
