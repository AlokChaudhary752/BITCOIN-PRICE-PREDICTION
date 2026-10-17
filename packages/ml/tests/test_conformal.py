"""
Unit test for Conformal Quantile Calibration.
Acceptance Check: Interval coverage is within 3 points of nominal (87% - 93% for nominal 90%).
"""
import numpy as np
import pytest

from btc_oracle_ml.models.conformal import ConformalCalibrator


def test_conformal_coverage_within_tolerance():
    np.random.seed(42)
    N = 1000
    y_true = np.random.normal(0, 0.02, N)

    # Simulated under-covered raw predictions (e.g. only covering 82%)
    raw_quantiles = {
        0.05: np.full(N, -0.026),
        0.25: np.full(N, -0.012),
        0.50: np.full(N, 0.0),
        0.75: np.full(N, 0.012),
        0.95: np.full(N, 0.026),
    }

    calibrator = ConformalCalibrator(nominal_90=0.90, nominal_50=0.50)
    calibrator.calibrate(y_true[:500], {q: v[:500] for q, v in raw_quantiles.items()})

    # Test on held-out test split
    test_calibrated = calibrator.apply_conformal({q: v[500:] for q, v in raw_quantiles.items()})
    y_test = y_true[500:]

    cov_90 = np.mean((y_test >= test_calibrated[0.05]) & (y_test <= test_calibrated[0.95]))
    cov_diff_90 = abs(cov_90 - 0.90)

    # Acceptance criterion: Interval coverage is within 3 points of nominal (<= 0.03)
    assert cov_diff_90 <= 0.03, f"Conformal coverage delta {cov_diff_90:.4f} exceeds 0.03 (3 percentage points)!"
