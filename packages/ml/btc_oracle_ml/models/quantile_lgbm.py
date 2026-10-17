"""
Multi-Quantile LightGBM Regression Engine.
Predicts calibrated quantiles (q05, q25, q50, q75, q95) per horizon with non-crossing guarantees.
"""
import logging

import lightgbm as lgb
import numpy as np
import pandas as pd
from btc_oracle_ml.config import QUANTILES

logger = logging.getLogger(__name__)


class QuantileLGBM:
    """Trains and serves quantile regression models for a single horizon."""

    def __init__(
        self,
        horizon_name: str,
        quantiles: list[float] | None = None,
        random_state: int = 42,
    ):
        self.horizon_name = horizon_name
        self.quantiles = quantiles or QUANTILES
        self.random_state = random_state
        self.models: dict[float, lgb.LGBMRegressor] = {}
        self.feature_names_: list[str] = []

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        val_X: pd.DataFrame | None = None,
        val_y: pd.Series | None = None,
    ) -> "QuantileLGBM":
        """Fit a separate model for each quantile objective."""
        self.feature_names_ = list(X.columns)

        # Drop any remaining NaNs in training pair
        valid_mask = ~(y.isna() | np.isinf(y))
        X_clean = X[valid_mask]
        y_clean = y[valid_mask]

        for q in self.quantiles:
            model = lgb.LGBMRegressor(
                objective="quantile",
                alpha=q,
                n_estimators=120,
                learning_rate=0.04,
                num_leaves=31,
                min_child_samples=50,
                subsample=0.85,
                colsample_bytree=0.85,
                random_state=self.random_state,
                verbose=-1,
                n_jobs=-1,
            )
            model.fit(X_clean, y_clean)
            self.models[q] = model

        return self

    def predict_quantiles(self, X: pd.DataFrame) -> dict[float, np.ndarray]:
        """
        Predict quantiles and enforce non-crossing monotonicity:
        q05 <= q25 <= q50 <= q75 <= q95.
        """
        raw_preds = np.zeros((len(X), len(self.quantiles)))
        for i, q in enumerate(self.quantiles):
            model = self.models[q]
            X_in = X
            if isinstance(X, pd.DataFrame):
                if hasattr(model, "booster_") and model.booster_ is not None:
                    booster_cols = model.booster_.feature_name()
                    if booster_cols and all(c in X.columns for c in booster_cols):
                        X_in = X[booster_cols]
                elif hasattr(model, "feature_name_") and model.feature_name_:
                    cols = [c for c in model.feature_name_ if c in X.columns]
                    if len(cols) == len(model.feature_name_):
                        X_in = X[cols]

            raw_preds[:, i] = model.predict(X_in)

        # Monotonic sorting along the quantile axis to prevent quantile crossing
        sorted_preds = np.sort(raw_preds, axis=1)

        result: dict[float, np.ndarray] = {}
        for i, q in enumerate(self.quantiles):
            result[q] = sorted_preds[:, i]

        return result
