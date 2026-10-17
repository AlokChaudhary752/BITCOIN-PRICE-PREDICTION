"""
Regime-Conditional Router and Agreement Engine.
Implements regime-specific model specialization with dynamic weight routing
based on Hidden Markov Model (HMM) posterior probabilities.
"""
from typing import Any

import numpy as np
import pandas as pd
from btc_oracle_ml.config import (
    QUANTILES,
    REGIME_HIGH_VOLATILITY,
    REGIME_RANGING,
    REGIME_TRENDING_BULL,
)
from btc_oracle_ml.models.conformal import ConformalCalibrator
from btc_oracle_ml.models.quantile_lgbm import QuantileLGBM
from btc_oracle_ml.models.sequence_gru import SequenceGRUModel
from scipy.stats import norm


class RegimeConditionalRouter:
    """
    Regime-Conditional Router for Model Specialization.
    Maintains specialized model weights for:
    - Trending Bull: High LightGBM weight (0.70), momentum preservation
    - Ranging: Balanced weights (0.55 LightGBM, 0.45 GRU), oscillator mean reversion
    - High-Volatility Shock: High Attention GRU weight (0.70), tail risk defense
    Dynamically routes and blends predictions based on HMM posterior state probabilities.
    """

    # Regime-specific specialized expert weights
    EXPERT_WEIGHTS = {
        REGIME_RANGING: {"lgb": 0.55, "gru": 0.45},
        REGIME_TRENDING_BULL: {"lgb": 0.70, "gru": 0.30},
        REGIME_HIGH_VOLATILITY: {"lgb": 0.30, "gru": 0.70},
    }

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
        regime_probs: np.ndarray | dict[str, float] | None = None,
        regime_confidence: float = 0.5,
    ) -> dict[str, Any]:
        """
        Produce institutional probabilistic forecast with regime routing:
        - Dynamically switches primary predictor based on HMM posterior probability
        - Adapts conformal intervals using sliding volatility scaling
        - Returns regime_confidence and expected_volatility
        """
        # Predict with Quantile LightGBM
        lgbm_q = self.lgbm.predict_quantiles(X_sample)
        # Predict with Sequence Attention GRU
        gru_q = self.gru.predict_quantiles(X_sample)

        # 1. Regime-Conditional Router: Compute dynamic weights from HMM posteriors
        if regime_probs is not None:
            if isinstance(regime_probs, dict):
                p_ranging = float(regime_probs.get("ranging", 0.33))
                p_bull = float(regime_probs.get("trending_bull", 0.33))
                p_shock = float(regime_probs.get("high_volatility", 0.34))
            elif hasattr(regime_probs, "__len__") and len(regime_probs) >= 3:
                p_ranging = float(regime_probs[0])
                p_bull = float(regime_probs[1])
                p_shock = float(regime_probs[2])
            else:
                p_ranging, p_bull, p_shock = 0.33, 0.33, 0.34

            # Normalize probabilities
            total_p = p_ranging + p_bull + p_shock
            if total_p > 0:
                p_ranging /= total_p
                p_bull /= total_p
                p_shock /= total_p
            else:
                p_ranging, p_bull, p_shock = 0.33, 0.33, 0.34

            # Posterior-weighted expert blending
            w_lgb = (
                (p_ranging * self.EXPERT_WEIGHTS[REGIME_RANGING]["lgb"])
                + (p_bull * self.EXPERT_WEIGHTS[REGIME_TRENDING_BULL]["lgb"])
                + (p_shock * self.EXPERT_WEIGHTS[REGIME_HIGH_VOLATILITY]["lgb"])
            )
            w_gru = 1.0 - w_lgb
        else:
            weights = self.EXPERT_WEIGHTS.get(regime_label, self.EXPERT_WEIGHTS[REGIME_RANGING])
            w_lgb, w_gru = weights["lgb"], weights["gru"]

        # Primary predictor identification
        primary_predictor = "LightGBM" if w_lgb >= w_gru else "AttentionGRU"

        # Weighted raw return quantiles
        raw_combined_q: dict[float, np.ndarray] = {}
        for q in QUANTILES:
            raw_combined_q[q] = (w_lgb * lgbm_q[q]) + (w_gru * gru_q[q])

        # 2. Apply Adaptive Conformal Calibration with real-time volatility shock adjustment
        vol_base = getattr(self.calibrator, "baseline_vol", None) or (vol_95th_percentile * 0.5)
        calibrated_q = self.calibrator.apply_conformal(
            raw_combined_q,
            current_vol=current_vol,
            vol_baseline=vol_base,
        )

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

        # Expected forward volatility (annualized standard deviation from quantile spread)
        iqr = ret_q75 - ret_q25
        est_sigma = max(iqr / 1.349, current_vol, 1e-5)
        expected_volatility = round(float(est_sigma * 100.0), 2)

        # Probability of positive price move P(Up): from normal fit of quantiles
        z_zero = (0.0 - ret_q50) / est_sigma
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
            "regime_confidence": round(float(regime_confidence) * 100.0, 1) if regime_confidence <= 1.0 else round(float(regime_confidence), 1),
            "expected_volatility": expected_volatility,
            "primary_predictor": primary_predictor,
            "expert_weights": {"lgbm": round(w_lgb, 2), "gru": round(w_gru, 2)},
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


# Backward compatibility alias
RegimeEnsemble = RegimeConditionalRouter
