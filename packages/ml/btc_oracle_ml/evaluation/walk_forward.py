"""
Purged and Embargoed Walk-Forward Cross-Validation.
Guarantees zero target leakage and prevents serial correlation bias across train/test splits.
"""
import logging
from typing import Dict, List, Any
import numpy as np
import pandas as pd

from btc_oracle_ml.config import (
    HORIZONS,
    WF_TRAIN_WINDOW_HOURS,
    WF_STEP_HOURS,
    WF_EMBARGO_HOURS,
)
from btc_oracle_ml.models.quantile_lgbm import QuantileLGBM
from btc_oracle_ml.models.sequence_gru import SequenceGRUModel
from btc_oracle_ml.models.conformal import ConformalCalibrator
from btc_oracle_ml.evaluation.metrics import evaluate_forecasts

logger = logging.getLogger(__name__)


class WalkForwardValidator:
    """Expanding-window walk-forward evaluator with purge and embargo gaps."""

    def __init__(
        self,
        train_window_hours: int = WF_TRAIN_WINDOW_HOURS,
        step_hours: int = WF_STEP_HOURS,
        embargo_hours: int = WF_EMBARGO_HOURS,
    ):
        self.train_window = train_window_hours
        self.step = step_hours
        self.embargo = embargo_hours

    def run_walk_forward(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        prices: pd.Series,
        horizon_name: str,
        n_folds: int = 4,
    ) -> Dict[str, Any]:
        """
        Executes purged & embargoed walk-forward evaluation.
        """
        horizon_hours = HORIZONS[horizon_name]
        total_len = len(X)
        fold_results: List[Dict[str, Any]] = []

        all_y_true: List[float] = []
        all_pred_q: Dict[float, List[float]] = {0.05: [], 0.25: [], 0.50: [], 0.75: [], 0.95: []}
        all_curr_prices: List[float] = []
        all_actual_prices: List[float] = []

        # Determine start index for first test fold
        test_start_idx = total_len - (n_folds * self.step)
        if test_start_idx < self.train_window:
            test_start_idx = self.train_window

        logger.info(f"Running Walk-Forward validation for horizon={horizon_name} across {n_folds} folds...")

        for fold in range(n_folds):
            train_end = test_start_idx + (fold * self.step)
            test_start = train_end + self.embargo
            test_end = min(test_start + self.step, total_len)

            if test_start >= total_len or test_end <= test_start:
                break

            # Purge training set: remove last `horizon_hours` of training to avoid overlapping labels
            purged_train_end = max(0, train_end - horizon_hours)

            X_train = X.iloc[:purged_train_end]
            y_train = y.iloc[:purged_train_end]

            X_test = X.iloc[test_start:test_end]
            y_test = y.iloc[test_start:test_end]
            p_test = prices.iloc[test_start:test_end]

            # Future actual prices: Close_{t+h} = Close_t * exp(y)
            actual_future_p = p_test * np.exp(y_test)

            # Fit Quantile LightGBM on train fold
            lgbm = QuantileLGBM(horizon_name=horizon_name)
            lgbm.fit(X_train, y_train)

            # Split calibration fold (last 20% of train) for conformal calibration
            cal_split = int(len(X_train) * 0.8)
            X_cal = X_train.iloc[cal_split:]
            y_cal = y_train.iloc[cal_split:]

            raw_cal_preds = lgbm.predict_quantiles(X_cal)
            calibrator = ConformalCalibrator()
            calibrator.calibrate(y_cal.values, raw_cal_preds)

            # Predict on test fold
            raw_test_preds = lgbm.predict_quantiles(X_test)
            calibrated_test_preds = calibrator.apply_conformal(raw_test_preds)

            # Accumulate predictions
            valid_mask = ~(y_test.isna() | np.isinf(y_test))
            all_y_true.extend(y_test[valid_mask].tolist())
            all_curr_prices.extend(p_test[valid_mask].tolist())
            all_actual_prices.extend(actual_future_p[valid_mask].tolist())

            for q in [0.05, 0.25, 0.50, 0.75, 0.95]:
                all_pred_q[q].extend(calibrated_test_preds[q][valid_mask].tolist())

            fold_eval = evaluate_forecasts(
                y_true=y_test.values,
                predicted_quantiles=calibrated_test_preds,
                current_prices=p_test.values,
                future_actual_prices=actual_future_p.values,
            )
            fold_results.append({
                "fold": fold + 1,
                "train_samples": len(X_train),
                "test_samples": len(X_test),
                "mae": fold_eval["model"]["mae"],
                "dir_acc": fold_eval["model"]["directional_accuracy_pct"],
                "coverage_90": fold_eval["model"]["empirical_coverage_90_pct"],
            })

        # Aggregate overall out-of-sample metrics
        agg_preds = {q: np.array(vals) for q, vals in all_pred_q.items()}
        overall_eval = evaluate_forecasts(
            y_true=np.array(all_y_true),
            predicted_quantiles=agg_preds,
            current_prices=np.array(all_curr_prices),
            future_actual_prices=np.array(all_actual_prices),
        )

        return {
            "horizon": horizon_name,
            "overall": overall_eval,
            "folds": fold_results,
        }
