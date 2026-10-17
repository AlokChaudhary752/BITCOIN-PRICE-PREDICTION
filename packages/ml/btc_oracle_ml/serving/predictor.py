"""
Real-Time Serving and Inference Engine.
Loads registered champion model artifacts and generates live probabilistic forecasts.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import joblib
import pandas as pd
import numpy as np

from btc_oracle_ml.config import (
    MODEL_REGISTRY_DIR,
    HORIZONS,
    REGIME_LABELS,
    REGIME_RANGING,
)
from btc_oracle_ml.features.pipeline import FeaturePipeline
from btc_oracle_ml.models.regime_hmm import RegimeHMM
from btc_oracle_ml.models.ensemble import RegimeEnsemble
from btc_oracle_ml.models.explain import ModelExplainer

logger = logging.getLogger(__name__)


class BTCOraclePredictor:
    """Production serving wrapper for all horizons and regimes."""

    def __init__(self, registry_dir: Optional[Path] = None):
        self.registry_dir = registry_dir or MODEL_REGISTRY_DIR
        self.ensembles: Dict[str, RegimeEnsemble] = {}
        self.regime_hmm: Optional[RegimeHMM] = None
        self.explainers: Dict[str, ModelExplainer] = {}
        self.pipeline = FeaturePipeline()
        self.vol_95th: float = 0.02
        self.version: str = "1.0.0"
        self.model_metadata: Dict[str, Any] = {}

    def load_champion(self) -> bool:
        """Load registered champion artifact package."""
        artifact_path = self.registry_dir / "champion_model.joblib"
        if not artifact_path.exists():
            logger.warning(f"Champion artifact not found at {artifact_path}")
            return False

        try:
            bundle = joblib.load(artifact_path)
            self.ensembles = bundle["ensembles"]
            self.regime_hmm = bundle["regime_hmm"]
            self.explainers = bundle["explainers"]
            self.vol_95th = bundle.get("vol_95th", 0.02)
            self.version = bundle.get("version", "1.0.0")
            self.model_metadata = bundle.get("metadata", {})
            logger.info(f"Loaded champion model v{self.version}")
            return True
        except Exception as e:
            logger.error(f"Error loading champion model bundle: {e}")
            return False

    def predict_live(self, df_recent: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate full suite of live forecasts from recent candle history.
        df_recent: at least 200 hours of recent OHLCV + sentiment data.
        """
        if not self.ensembles:
            success = self.load_champion()
            if not success:
                raise RuntimeError("Predictor cannot serve: no model loaded and no champion artifact found.")

        # Transform features
        X, _ = self.pipeline.transform(df_recent)
        latest_X = X.iloc[-1:]

        current_price = float(df_recent["close"].iloc[-1])
        current_vol = float(latest_X["vol_parkinson_24h"].iloc[0])

        # Regime identification
        returns = latest_X["return_1h"]
        vols = latest_X["vol_parkinson_24h"]
        if self.regime_hmm:
            regime_label, state_probs, regime_conf = self.regime_hmm.predict_regime(returns, vols)
        else:
            regime_label, state_probs, regime_conf = REGIME_RANGING, np.array([0.5, 0.3, 0.2]), 0.5

        # Multi-horizon probabilistic forecasts
        horizon_forecasts: Dict[str, Any] = {}
        for h_name, ensemble in self.ensembles.items():
            fc = ensemble.predict_probabilistic(
                X_sample=latest_X,
                current_price=current_price,
                regime_label=regime_label,
                current_vol=current_vol,
                vol_95th_percentile=self.vol_95th,
            )
            horizon_forecasts[h_name] = fc

        # SHAP explanation for primary horizon (24h)
        primary_explainer = self.explainers.get("24h") or next(iter(self.explainers.values()))
        explanation = primary_explainer.explain_prediction(latest_X)

        # Baseline 24h forecast summary
        primary_24h = horizon_forecasts.get("24h", next(iter(horizon_forecasts.values())))

        return {
            "version": self.version,
            "timestamp": df_recent.index[-1].isoformat(),
            "current_price": current_price,
            "market_regime": {
                "label": regime_label,
                "confidence": round(regime_conf * 100.0, 1),
                "probabilities": {
                    "ranging": round(float(state_probs[0]) * 100.0, 1),
                    "trending_bull": round(float(state_probs[1]) * 100.0, 1),
                    "high_volatility": round(float(state_probs[2]) * 100.0, 1),
                },
            },
            "primary_signal": {
                "signal": primary_24h["signal"],
                "signal_level": primary_24h["signal_level"],
                "prob_up": primary_24h["prob_up"],
                "expected_return_pct": primary_24h["expected_return_pct"],
                "risk_score": primary_24h["risk_score"],
                "agreement_score": primary_24h["agreement_score"],
                "confidence_level": primary_24h["confidence_level"],
                "low_confidence_flag": primary_24h["low_confidence_flag"],
            },
            "horizons": horizon_forecasts,
            "explanation": {
                "narrative": explanation["plain_english_narrative"],
                "top_drivers": explanation["top_drivers"],
            },
        }
