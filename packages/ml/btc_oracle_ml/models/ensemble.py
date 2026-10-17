"""
Regime-Conditioned Ensemble and Agreement Engine.
Synthesizes LightGBM and PyTorch GRU quantile outputs with cross-model dispersion metrics.
"""
from typing import Any

import numpy as np
import pandas as pd
from btc_oracle_ml.config import (
    QUANTILES,
    REGIME_HIGH_VOLATILITY,
    REGIME_TRENDING_BULL,
)
from btc_oracle_ml.models.conformal import ConformalCalibrator
from btc_oracle_ml.models.quantile_lgbm import QuantileLGBM
from btc_oracle_ml.models.sequence_gru import SequenceGRUModel


class RegimeEnsemble:
    """Combines Quantile LGBM, Sequence GRU, and Conformal Calibration."""

    def __init__(
        self,
        horizon_name: str,
        lgbm_model: QuantileLGBM,
        gru_model: SequenceGRUModel,
        calibrator: ConformalCalibrator,
    ):
        self.horizon_name = horizon_name
        self.lgbm = lgbm_model
        self.gru = gru_model
        self.calibrator = calibrator

    def predict_probabilistic(
        self,
        X_sample: pd.DataFrame,
        current_price: float,
        regime_label: str,
        current_vol: float,
        vol_95th_percentile: float,
    ) -> dict[str, Any]:
        """
        Produce institutional probabilistic forecast:
        - Quantile prices: q05, q25, q50, q75, q95
        - Model agreement score (0..100%)
        - Probability of positive return P(Up)
        - Risk score (1..10)
        - AI Signal (Strong Buy, Buy, Neutral, Sell, Strong Sell)
        - Confidence badge ("High", "Moderate", "Low confidence")
        """
        # Predict with LGBM
        lgbm_q = self.lgbm.predict_quantiles(X_sample)
        # Predict with GRU
        gru_q = self.gru.predict_quantiles(X_sample)

        # Dynamic regime weighting
        if regime_label == REGIME_HIGH_VOLATILITY:
            w_lgb, w_gru = 0.45, 0.55
        elif regime_label == REGIME_TRENDING_BULL:
            w_lgb, w_gru = 0.65, 0.35
        else:
            w_lgb, w_gru = 0.60, 0.40

        # Weighted raw return quantiles
        raw_combined_q: dict[float, np.ndarray] = {}
        for q in QUANTILES:
            raw_combined_q[q] = (w_lgb * lgbm_q[q]) + (w_gru * gru_q[q])

        # Apply conformal calibration for guaranteed coverage
        calibrated_q = self.calibrator.apply_conformal(raw_combined_q)

        # Cross-model dispersion & agreement score
        lgb_med = float(lgbm_q[0.50][-1])
        gru_med = float(gru_q[0.50][-1])
        vol_baseline = max(current_vol, 0.005)
        dispersion = abs(lgb_med - gru_med)
        # Agreement: 1.0 when identical, decays as dispersion grows relative to volatility
        agreement_score = float(np.clip(1.0 - (dispersion / (2.5 * vol_baseline)), 0.15, 0.99))

        # Check for Low Confidence trigger
        is_vol_extreme = current_vol >= vol_95th_percentile
        is_dispersion_high = agreement_score < 0.60
        low_confidence = is_vol_extreme or is_dispersion_high

        if low_confidence:
            confidence_level = "Low confidence"
        elif agreement_score >= 0.85:
            confidence_level = "High confidence"
        else:
            confidence_level = "Moderate confidence"

        # Extract latest point estimates
        ret_q05 = float(calibrated_q[0.05][-1])
        ret_q25 = float(calibrated_q[0.25][-1])
        ret_q50 = float(calibrated_q[0.50][-1])
        ret_q75 = float(calibrated_q[0.75][-1])
        ret_q95 = float(calibrated_q[0.95][-1])

        # Convert return quantiles to dollar prices
        price_q05 = round(current_price * np.exp(ret_q05), 2)
        price_q25 = round(current_price * np.exp(ret_q25), 2)
        price_q50 = round(current_price * np.exp(ret_q50), 2)
        price_q75 = round(current_price * np.exp(ret_q75), 2)
        price_q95 = round(current_price * np.exp(ret_q95), 2)

        # Probability of positive price move P(Up): from normal fit of quantiles
        iqr = ret_q75 - ret_q25
        est_sigma = max(iqr / 1.349, 1e-5)
        # Z-score for return > 0
        z_zero = (0.0 - ret_q50) / est_sigma
        # P(Z > z_zero) = 1 - Phi(z_zero)
        from scipy.stats import norm
        prob_up = float(np.clip(1.0 - norm.cdf(z_zero), 0.01, 0.99))

        # Expected percentage return
        expected_return_pct = round(ret_q50 * 100.0, 3)

        # Risk score from 1 (lowest) to 10 (highest risk)
        vol_risk = (current_vol / max(vol_95th_percentile, 0.02)) * 6.0
        spread_risk = ((price_q95 - price_q05) / current_price) * 4.0
        risk_score = int(np.clip(round(vol_risk + spread_risk), 1, 10))

        # AI 5-tier Signal
        if prob_up >= 0.70 and expected_return_pct > 1.0:
            signal = "Strong Buy"
            signal_level = 5
        elif prob_up >= 0.56 and expected_return_pct > 0.1:
            signal = "Buy"
            signal_level = 4
        elif prob_up <= 0.32 and expected_return_pct < -1.0:
            signal = "Strong Sell"
            signal_level = 1
        elif prob_up <= 0.44 and expected_return_pct < -0.1:
            signal = "Sell"
            signal_level = 2
        else:
            signal = "Hold / Neutral"
            signal_level = 3

        return {
            "horizon": self.horizon_name,
            "current_price": current_price,
            "point_forecast": price_q50,
            "expected_return_pct": expected_return_pct,
            "prob_up": round(prob_up, 4),
            "agreement_score": round(agreement_score * 100.0, 1),
            "risk_score": risk_score,
            "signal": signal,
            "signal_level": signal_level,
            "confidence_level": confidence_level,
            "low_confidence_flag": low_confidence,
            "interval_50": {
                "lower": price_q25,
                "upper": price_q75,
                "nominal_coverage": 0.50,
                "empirical_coverage": round(self.calibrator.empirical_coverage_50, 3),
            },
            "interval_90": {
                "lower": price_q05,
                "upper": price_q95,
                "nominal_coverage": 0.90,
                "empirical_coverage": round(self.calibrator.empirical_coverage_90, 3),
            },
            "quantiles": {
                "q05": price_q05,
                "q25": price_q25,
                "q50": price_q50,
                "q75": price_q75,
                "q95": price_q95,
            },
            "per_model_median": {
                "lgbm": round(current_price * np.exp(lgb_med), 2),
                "gru": round(current_price * np.exp(gru_med), 2),
            },
        }
