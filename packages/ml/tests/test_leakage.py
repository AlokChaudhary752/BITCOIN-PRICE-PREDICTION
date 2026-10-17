"""
Dedicated Leakage Unit Test.
Requirements: shifting the target forward must destroy performance.
"""
import numpy as np
import pandas as pd
import pytest

from btc_oracle_ml.features.pipeline import FeaturePipeline
from btc_oracle_ml.evaluation.leakage import run_target_shuffle_leakage_test


def test_target_shift_leakage_destruction():
    """Verify that shifting or scrambling targets destroys predictive performance."""
    # Create sample time series
    dates = pd.date_range("2024-01-01", periods=1000, freq="1h", name="timestamp")
    np.random.seed(42)
    ret = np.random.normal(0.0001, 0.008, 1000)
    prices = 40000.0 * np.exp(np.cumsum(ret))

    df = pd.DataFrame(
        {
            "open": prices * 0.999,
            "high": prices * 1.004,
            "low": prices * 0.996,
            "close": prices,
            "volume": np.random.uniform(50, 200, 1000),
            "quote_asset_volume": prices * np.random.uniform(50, 200, 1000),
            "number_of_trades": np.random.randint(100, 500, 1000),
            "taker_buy_base_volume": np.random.uniform(25, 100, 1000),
        },
        index=dates,
    )

    pipeline = FeaturePipeline()
    X, y_dict = pipeline.transform(df)
    y = y_dict["24h"]

    # Split train/test
    split = 700
    X_train, y_train = X.iloc[:split], y.iloc[:split]
    X_test, y_test = X.iloc[split:], y.iloc[split:]

    res = run_target_shuffle_leakage_test(X_train, y_train, X_test, y_test)

    # Shifting the target forward should collapse accuracy to noise (~50%)
    assert res["performance_destroyed"] is True, "Performance was not destroyed when shifting target!"
    assert res["scrambled_directional_accuracy"] <= 60.0, "Model maintained edge on scrambled noise target!"
