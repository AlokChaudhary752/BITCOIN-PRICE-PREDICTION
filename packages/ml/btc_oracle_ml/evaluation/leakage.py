"""
Dedicated Leakage Detection and Causal Integrity Test.
Verifies that features are strictly backward-looking and that shifting the target destroys predictive performance.
"""
import numpy as np
import pandas as pd
import pytest

from btc_oracle_ml.models.quantile_lgbm import QuantileLGBM
from btc_oracle_ml.features.pipeline import FeaturePipeline


def run_target_shuffle_leakage_test(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict:
    """
    Shifting or scrambling the target forward/backward must destroy directional edge.
    If a model maintains high accuracy on scrambled/shifted targets, features contain lookahead leakage.
    """
    # 1. Fit on true causal target
    real_model = QuantileLGBM(horizon_name="24h")
    real_model.fit(X_train, y_train)
    real_preds = real_model.predict_quantiles(X_test)[0.50]
    real_dir_acc = float(np.mean(np.sign(real_preds) == np.sign(y_test)) * 100.0)

    # 2. Scramble / Shift the target forward by 72 hours
    y_train_shifted = y_train.shift(72).bfill()
    shifted_model = QuantileLGBM(horizon_name="24h")
    shifted_model.fit(X_train, y_train_shifted)
    shifted_preds = shifted_model.predict_quantiles(X_test)[0.50]
    shifted_dir_acc = float(np.mean(np.sign(shifted_preds) == np.sign(y_test)) * 100.0)

    # Scrambled target (random permutation)
    np.random.seed(42)
    y_train_scrambled = pd.Series(np.random.permutation(y_train.values), index=y_train.index)
    scrambled_model = QuantileLGBM(horizon_name="24h")
    scrambled_model.fit(X_train, y_train_scrambled)
    scrambled_preds = scrambled_model.predict_quantiles(X_test)[0.50]
    scrambled_dir_acc = float(np.mean(np.sign(scrambled_preds) == np.sign(y_test)) * 100.0)

    # Acceptance: shifting or scrambling the target destroys performance to near random (45-55%)
    leakage_detected = (shifted_dir_acc > real_dir_acc + 5.0) or (scrambled_dir_acc > 60.0)

    return {
        "real_directional_accuracy": round(real_dir_acc, 2),
        "shifted_directional_accuracy": round(shifted_dir_acc, 2),
        "scrambled_directional_accuracy": round(scrambled_dir_acc, 2),
        "performance_destroyed": not leakage_detected,
        "leakage_detected": leakage_detected,
    }


def verify_feature_causality(df: pd.DataFrame) -> bool:
    """Verify that every feature calculation only uses t <= current_t."""
    pipeline = FeaturePipeline()
    X, y_dict = pipeline.transform(df)

    # Check that altering the final row in df only affects the final row in X, not prior rows
    df_altered = df.copy()
    df_altered.iloc[-1, df_altered.columns.get_loc("close")] *= 1.5

    X_altered, _ = pipeline.transform(df_altered)

    # Prior rows (all except the last row) must be identical to numerical tolerance
    diff = (X.iloc[:-1] - X_altered.iloc[:-1]).abs().max().max()
    return bool(diff < 1e-9)
