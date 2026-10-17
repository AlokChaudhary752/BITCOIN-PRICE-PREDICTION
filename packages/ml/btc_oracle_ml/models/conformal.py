"""
Conformalized Quantile Regression with Finite-Sample Coverage Guarantees.
Calibrates empirical prediction intervals to match nominal coverage (50% and 90%).
"""
import numpy as np
from btc_oracle_ml.config import NOMINAL_COVERAGE_50, NOMINAL_COVERAGE_90


class ConformalCalibrator:
    """
    Split Conformal calibration for quantile regression intervals.
    Calibrates q05/q95 (90% nominal) and q25/q75 (50% nominal).
    """

    def __init__(
        self,
        nominal_90: float = NOMINAL_COVERAGE_90,
        nominal_50: float = NOMINAL_COVERAGE_50,
    ):
        self.nominal_90 = nominal_90
        self.nominal_50 = nominal_50
        self.q_correction_90: float = 0.0
        self.q_correction_50: float = 0.0
        self.empirical_coverage_90: float = nominal_90
        self.empirical_coverage_50: float = nominal_50

    def calibrate(
        self,
        y_true: np.ndarray,
        raw_quantiles: dict[float, np.ndarray],
    ) -> "ConformalCalibrator":
        """
        Calibrate on held-out calibration set.
        y_true: 1D array of actual target returns
        raw_quantiles: dict mapping q (0.05, 0.25, 0.5, 0.75, 0.95) to 1D predicted arrays
        """
        valid = ~(np.isnan(y_true) | np.isinf(y_true))
        y = y_true[valid]
        N = len(y)
        if N < 20:
            return self

        q05 = raw_quantiles[0.05][valid]
        q95 = raw_quantiles[0.95][valid]
        q25 = raw_quantiles[0.25][valid]
        q75 = raw_quantiles[0.75][valid]

        # 1. Calibrate 90% interval [q05, q95]
        # Non-conformity score: distance outside the interval
        scores_90 = np.maximum(q05 - y, y - q95)
        # Quantile index with finite sample correction: ceil((N + 1) * alpha) / N
        k_90 = int(np.ceil((N + 1) * self.nominal_90))
        k_90 = min(max(k_90, 1), N)
        sorted_scores_90 = np.sort(scores_90)
        self.q_correction_90 = float(sorted_scores_90[k_90 - 1])

        # 2. Calibrate 50% interval [q25, q75]
        scores_50 = np.maximum(q25 - y, y - q75)
        k_50 = int(np.ceil((N + 1) * self.nominal_50))
        k_50 = min(max(k_50, 1), N)
        sorted_scores_50 = np.sort(scores_50)
        self.q_correction_50 = float(sorted_scores_50[k_50 - 1])

        # Check empirical coverage on calibration set
        cov_90 = np.mean((y >= (q05 - self.q_correction_90)) & (y <= (q95 + self.q_correction_90)))
        cov_50 = np.mean((y >= (q25 - self.q_correction_50)) & (y <= (q75 + self.q_correction_50)))

        self.empirical_coverage_90 = float(cov_90)
        self.empirical_coverage_50 = float(cov_50)

        return self

    def apply_conformal(
        self,
        raw_quantiles: dict[float, np.ndarray],
    ) -> dict[float, np.ndarray]:
        """Apply calibrated adjustments to predicted quantiles."""
        calibrated = dict(raw_quantiles)

        # Expand or adjust interval bands by conformal correction
        calibrated[0.05] = raw_quantiles[0.05] - self.q_correction_90
        calibrated[0.95] = raw_quantiles[0.95] + self.q_correction_90

        calibrated[0.25] = raw_quantiles[0.25] - self.q_correction_50
        calibrated[0.75] = raw_quantiles[0.75] + self.q_correction_50

        # Enforce non-crossing monotonicity
        all_q = [0.05, 0.25, 0.50, 0.75, 0.95]
        stacked = np.column_stack([calibrated[q] for q in all_q])
        stacked_sorted = np.sort(stacked, axis=1)

        for i, q in enumerate(all_q):
            calibrated[q] = stacked_sorted[:, i]

        return calibrated
