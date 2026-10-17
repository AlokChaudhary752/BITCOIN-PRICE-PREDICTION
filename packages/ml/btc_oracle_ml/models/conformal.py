"""
Conformalized Quantile Regression with Finite-Sample Coverage Guarantees.
Implements Split-Conformal calibration and Adaptive Sliding-Window Conformal Calibration
to ensure 90% coverage intervals adjust to volatility shocks in real time.
"""
import numpy as np
from btc_oracle_ml.config import NOMINAL_COVERAGE_50, NOMINAL_COVERAGE_90


class ConformalCalibrator:
    """
    Split Conformal calibration for quantile regression intervals.
    Calibrates q05/q95 (90% nominal) and q25/q75 (50% nominal).
    Supports adaptive volatility scaling and sliding window adaptation.
    """

    def __init__(
        self,
        nominal_90: float = NOMINAL_COVERAGE_90,
        nominal_50: float = NOMINAL_COVERAGE_50,
        sliding_window: int = 720,
    ):
        self.nominal_90 = nominal_90
        self.nominal_50 = nominal_50
        self.sliding_window = sliding_window
        self.q_correction_90: float = 0.0
        self.q_correction_50: float = 0.0
        self.empirical_coverage_90: float = nominal_90
        self.empirical_coverage_50: float = nominal_50
        self.baseline_vol: float = 0.015

        # Online sliding window non-conformity buffers
        self.recent_scores_90: list[float] = []
        self.recent_scores_50: list[float] = []

    def calibrate(
        self,
        y_true: np.ndarray,
        raw_quantiles: dict[float, np.ndarray],
        volatility: np.ndarray | None = None,
    ) -> "ConformalCalibrator":
        """
        Calibrate on held-out calibration set.
        y_true: 1D array of actual target returns
        raw_quantiles: dict mapping q (0.05, 0.25, 0.5, 0.75, 0.95) to 1D predicted arrays
        volatility: optional 1D array of realized volatilities for baseline scaling
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

        if volatility is not None:
            vol_clean = volatility[valid]
            self.baseline_vol = float(np.median(vol_clean[~np.isnan(vol_clean)])) if len(vol_clean) > 0 else 0.015

        # 1. Calibrate 90% interval [q05, q95]
        scores_90 = np.maximum(q05 - y, y - q95)
        k_90 = int(np.ceil((N + 1) * self.nominal_90))
        k_90 = min(max(k_90, 1), N)
        sorted_scores_90 = np.sort(scores_90)
        self.q_correction_90 = float(sorted_scores_90[k_90 - 1])

        # Store in sliding window buffer
        self.recent_scores_90 = list(scores_90[-self.sliding_window:])

        # 2. Calibrate 50% interval [q25, q75]
        scores_50 = np.maximum(q25 - y, y - q75)
        k_50 = int(np.ceil((N + 1) * self.nominal_50))
        k_50 = min(max(k_50, 1), N)
        sorted_scores_50 = np.sort(scores_50)
        self.q_correction_50 = float(sorted_scores_50[k_50 - 1])
        self.recent_scores_50 = list(scores_50[-self.sliding_window:])

        # Check empirical coverage on calibration set
        cov_90 = np.mean((y >= (q05 - self.q_correction_90)) & (y <= (q95 + self.q_correction_90)))
        cov_50 = np.mean((y >= (q25 - self.q_correction_50)) & (y <= (q75 + self.q_correction_50)))

        self.empirical_coverage_90 = float(cov_90)
        self.empirical_coverage_50 = float(cov_50)

        return self

    def apply_conformal(
        self,
        raw_quantiles: dict[float, np.ndarray],
        current_vol: float | None = None,
        vol_baseline: float | None = None,
    ) -> dict[float, np.ndarray]:
        """
        Apply calibrated adjustments to predicted quantiles with optional adaptive volatility scaling.
        If current_vol is provided, dynamically expands or contracts intervals
        in response to real-time volatility shocks.
        """
        calibrated = dict(raw_quantiles)

        # Adaptive volatility multiplier
        if current_vol is not None and current_vol > 0:
            base = vol_baseline or getattr(self, "baseline_vol", None) or 0.015
            vol_scale = float(np.clip(current_vol / base, 0.70, 2.50))
        else:
            vol_scale = 1.0

        corr_90 = self.q_correction_90 * vol_scale
        corr_50 = self.q_correction_50 * vol_scale

        # Expand or adjust interval bands by conformal correction
        calibrated[0.05] = raw_quantiles[0.05] - corr_90
        calibrated[0.95] = raw_quantiles[0.95] + corr_90

        calibrated[0.25] = raw_quantiles[0.25] - corr_50
        calibrated[0.75] = raw_quantiles[0.75] + corr_50

        # Enforce non-crossing monotonicity
        all_q = [0.05, 0.25, 0.50, 0.75, 0.95]
        stacked = np.column_stack([calibrated[q] for q in all_q])
        stacked_sorted = np.sort(stacked, axis=1)

        for i, q in enumerate(all_q):
            calibrated[q] = stacked_sorted[:, i]

        return calibrated

    def update_online(
        self,
        y_realized: float,
        predicted_q05: float,
        predicted_q95: float,
    ) -> None:
        """Sliding-window online update to track sudden non-stationary drift."""
        s90 = max(predicted_q05 - y_realized, y_realized - predicted_q95)
        self.recent_scores_90.append(float(s90))
        if len(self.recent_scores_90) > self.sliding_window:
            self.recent_scores_90.pop(0)

        # Re-estimate quantile on sliding window
        if len(self.recent_scores_90) >= 30:
            N = len(self.recent_scores_90)
            k_90 = int(np.ceil((N + 1) * self.nominal_90))
            k_90 = min(max(k_90, 1), N)
            self.q_correction_90 = float(np.sort(self.recent_scores_90)[k_90 - 1])


class AdaptiveConformalCalibrator(ConformalCalibrator):
    """Alias and specialized extension for Adaptive Conformal Calibration."""
    pass
