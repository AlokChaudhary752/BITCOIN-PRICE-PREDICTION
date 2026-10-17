"""
Unit test for Conformal Quantile Calibration.
Acceptance Check: Interval coverage is within 3 points of nominal (87% - 93% for nominal 90%).
"""
import numpy as np
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


def test_adaptive_conformal_volatility_scaling():
    from btc_oracle_ml.models.conformal import AdaptiveConformalCalibrator

    N = 500
    y_true = np.random.normal(0, 0.02, N)
    raw_quantiles = {
        0.05: np.full(N, -0.03),
        0.25: np.full(N, -0.01),
        0.50: np.full(N, 0.0),
        0.75: np.full(N, 0.01),
        0.95: np.full(N, 0.03),
    }

    calibrator = AdaptiveConformalCalibrator(nominal_90=0.90, nominal_50=0.50)
    calibrator.calibrate(y_true, raw_quantiles)

    # 1. Baseline application
    base_cal = calibrator.apply_conformal(raw_quantiles, current_vol=0.015, vol_baseline=0.015)
    base_width = base_cal[0.95] - base_cal[0.05]

    # 2. Shock application (volatility spikes to 0.030)
    shock_cal = calibrator.apply_conformal(raw_quantiles, current_vol=0.030, vol_baseline=0.015)
    shock_width = shock_cal[0.95] - shock_cal[0.05]

    # Interval must adaptively expand under volatility shock
    assert (shock_width > base_width).all(), "Adaptive conformal failed to expand under volatility shock!"

    # Verify non-crossing monotonicity
    for q_arr in shock_cal.values():
        assert not np.isnan(q_arr).any()
    assert (shock_cal[0.05] <= shock_cal[0.25]).all()
    assert (shock_cal[0.25] <= shock_cal[0.50]).all()
    assert (shock_cal[0.50] <= shock_cal[0.75]).all()
    assert (shock_cal[0.75] <= shock_cal[0.95]).all()
