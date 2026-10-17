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


def test_microstructure_and_macro_features(sample_ohlcv):
    from btc_oracle_ml.features.macro import (
        compute_fractional_differentiation,
        compute_garch_residuals,
        compute_macro_correlations,
    )
    from btc_oracle_ml.features.microstructure import (
        compute_cumulative_volume_delta,
        compute_order_flow_imbalance,
    )
    from btc_oracle_ml.features.pipeline import FeaturePipeline
    from btc_oracle_ml.features.volatility import compute_log_returns

    taker_buy = sample_ohlcv["taker_buy_base_volume"]
    taker_sell = sample_ohlcv["volume"] - taker_buy
    ofi, ofi_z = compute_order_flow_imbalance(taker_buy, taker_sell, window=12)
    assert len(ofi) == len(sample_ohlcv)
    assert not ofi_z.isna().all()

    cvd_momo, cvd_accel = compute_cumulative_volume_delta(taker_buy, taker_sell, window=12)
    assert len(cvd_momo) == len(sample_ohlcv)
    assert (cvd_momo >= -1.0).all() and (cvd_momo <= 1.0).all()

    rets = compute_log_returns(sample_ohlcv["close"], 1)
    cond_vol, std_res, vol_cluster = compute_garch_residuals(rets)
    assert (cond_vol > 0).all()
    assert len(std_res) == len(sample_ohlcv)

    sp_corr, dxy_corr = compute_macro_correlations(rets, window=24)
    assert len(sp_corr) == len(sample_ohlcv)
    assert len(dxy_corr) == len(sample_ohlcv)

    fd = compute_fractional_differentiation(sample_ohlcv["close"], d=0.40)
    assert len(fd) == len(sample_ohlcv)

    # Test full pipeline integration
    pipeline = FeaturePipeline()
    X, y_dict = pipeline.transform(sample_ohlcv)
    for expected_col in [
        "ofi_zscore",
        "cvd_momo_24h",
        "garch_conditional_vol",
        "garch_std_residuals",
        "garch_vol_cluster_ratio",
        "macro_sp500_corr",
        "macro_dxy_corr",
        "close_frac_diff",
    ]:
        assert expected_col in X.columns
        assert not X[expected_col].isna().any()
