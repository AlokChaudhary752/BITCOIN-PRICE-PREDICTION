"""
SHAP Explanations and Plain-English Institutional Narrative Generation.
Extracts local feature attributions and translates them into transparent executive summaries.
"""
from typing import Any

import numpy as np
import pandas as pd
import shap
from btc_oracle_ml.features.pipeline import FEATURE_DESCRIPTIONS


class ModelExplainer:
    """Computes SHAP values and generates institutional plain-English narratives."""

    def __init__(self, lgbm_model, feature_names: list[str]):
        self.feature_names = feature_names
        # Create TreeExplainer on median quantile (q50) model
        median_model = lgbm_model.models[0.50]
        self.explainer = shap.TreeExplainer(median_model)

    def explain_prediction(self, X_sample: pd.DataFrame) -> dict[str, Any]:
        """
        Explain a single observation (latest live tick).
        Returns top features, shap values, and natural language narrative.
        """
        if hasattr(self, "feature_names") and self.feature_names:
            cols = [c for c in self.feature_names if c in X_sample.columns]
            if len(cols) == len(self.feature_names):
                X_sample = X_sample[cols]

        shap_vals = self.explainer.shap_values(X_sample)
        if isinstance(shap_vals, list):
            vals = shap_vals[0]
        else:
            vals = shap_vals

        if len(vals.shape) > 1:
            vals = vals[0]  # Take first row

        feature_impacts = []
        for name, val in zip(self.feature_names, vals):
            raw_val = float(X_sample[name].iloc[0])
            desc = FEATURE_DESCRIPTIONS.get(name, name)
            feature_impacts.append({
                "feature": name,
                "description": desc,
                "value": round(raw_val, 4),
                "shap_value": round(float(val), 5),
                "abs_impact": abs(float(val)),
                "direction": "bullish" if val > 0 else "bearish",
            })

        # Sort by absolute magnitude
        feature_impacts.sort(key=lambda x: x["abs_impact"], reverse=True)

        top_drivers = feature_impacts[:5]
        narrative = self._generate_narrative(top_drivers)

        return {
            "top_drivers": top_drivers,
            "all_impacts": feature_impacts,
            "plain_english_narrative": narrative,
        }

    def _generate_narrative(self, drivers: list[dict[str, Any]]) -> str:
        """Synthesize natural institutional prose from top positive and negative drivers."""
        bullish = [d for d in drivers if d["direction"] == "bullish"]
        bearish = [d for d in drivers if d["direction"] == "bearish"]

        clauses = []
        if bearish:
            top_bear = bearish[0]
            desc = top_bear["description"].lower()
            clauses.append(f"{desc} (SHAP {top_bear['shap_value']:+.3f}) created headwinds")
            if len(bearish) > 1:
                clauses.append(f"compounded by {bearish[1]['description'].lower()}")

        if bullish:
            top_bull = bullish[0]
            desc = top_bull["description"].lower()
            if clauses:
                clauses.append(f"partially offset by {desc} (SHAP {top_bull['shap_value']:+.3f})")
            else:
                clauses.append(f"supported primarily by {desc} (SHAP {top_bull['shap_value']:+.3f})")

        if not clauses:
            return "Neutral macroeconomic and microstructural indicators with low directional dispersion."

        narrative = "; ".join(clauses)
        return narrative[0].upper() + narrative[1:] + "."

    def get_global_importance(self, X_sample: pd.DataFrame) -> list[dict[str, Any]]:
        """Compute mean absolute SHAP values across sample for Model Lab."""
        if hasattr(self, "feature_names") and self.feature_names:
            cols = [c for c in self.feature_names if c in X_sample.columns]
            if len(cols) == len(self.feature_names):
                X_sample = X_sample[cols]

        shap_vals = self.explainer.shap_values(X_sample)
        if isinstance(shap_vals, list):
            vals = shap_vals[0]
        else:
            vals = shap_vals

        mean_abs = np.mean(np.abs(vals), axis=0)
        items = []
        for name, score in zip(self.feature_names, mean_abs):
            items.append({
                "feature": name,
                "description": FEATURE_DESCRIPTIONS.get(name, name),
                "importance": round(float(score), 5),
            })
        items.sort(key=lambda x: x["importance"], reverse=True)
        return items
