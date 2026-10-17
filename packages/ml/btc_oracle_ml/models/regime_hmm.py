"""
Hidden Markov Model (HMM) Market Regime Detection.
Classifies market state into:
0: Ranging (Low volatility, mean-reverting)
1: Trending Bull (Positive drift, moderate volatility)
2: High Volatility / Crash (Elevated dispersion, erratic flow)
"""
import logging

import numpy as np
import pandas as pd
from btc_oracle_ml.config import (
    REGIME_HIGH_VOLATILITY,
    REGIME_RANGING,
    REGIME_TRENDING_BULL,
)
from hmmlearn.hmm import GaussianHMM

logger = logging.getLogger(__name__)


class RegimeHMM:
    """3-State Gaussian HMM fitted on returns and Parkinson volatility."""

    def __init__(self, n_components: int = 3, random_state: int = 42):
        self.n_components = n_components
        self.model = GaussianHMM(
            n_components=n_components,
            covariance_type="full",
            n_iter=100,
            random_state=random_state,
        )
        self.state_map: dict[int, str] = {}
        self.is_fitted = False

    def fit(self, returns: pd.Series, vol: pd.Series) -> "RegimeHMM":
        """Fit HMM and identify state semantics based on mean return and volatility."""
        clean_mask = ~(returns.isna() | vol.isna() | np.isinf(returns) | np.isinf(vol))
        ret_clean = returns[clean_mask].values
        vol_clean = vol[clean_mask].values

        X = np.column_stack([ret_clean, vol_clean])
        self.model.fit(X)

        # Inspect component means to assign semantic labels deterministically
        means = self.model.means_  # shape: (n_components, 2) -> [mean_return, mean_vol]
        vol_means = means[:, 1]
        ret_means = means[:, 0]

        # Highest volatility state is High Volatility
        high_vol_state = int(np.argmax(vol_means))

        remaining_states = [s for s in range(self.n_components) if s != high_vol_state]
        # Of remaining, higher return is Trending Bull, lower/flat is Ranging
        if ret_means[remaining_states[0]] > ret_means[remaining_states[1]]:
            bull_state = remaining_states[0]
            ranging_state = remaining_states[1]
        else:
            bull_state = remaining_states[1]
            ranging_state = remaining_states[0]

        self.state_map = {
            ranging_state: REGIME_RANGING,
            bull_state: REGIME_TRENDING_BULL,
            high_vol_state: REGIME_HIGH_VOLATILITY,
        }
        self.is_fitted = True
        logger.info(f"HMM fitted. State mapping: {self.state_map}")
        return self

    def predict_regime(self, returns: pd.Series, vol: pd.Series) -> tuple[str, np.ndarray, float]:
        """
        Returns:
        - current_regime_label (str)
        - state_probabilities (np.ndarray of length 3)
        - regime_confidence (float 0..1)
        """
        if not self.is_fitted:
            return REGIME_RANGING, np.array([0.5, 0.3, 0.2]), 0.5

        ret_val = float(returns.iloc[-1]) if not pd.isna(returns.iloc[-1]) else 0.0
        vol_val = float(vol.iloc[-1]) if not pd.isna(vol.iloc[-1]) else 0.01

        X = np.array([[ret_val, vol_val]])
        try:
            posteriors = self.model.predict_proba(X)[0]
            raw_state = int(np.argmax(posteriors))
            label = self.state_map.get(raw_state, REGIME_RANGING)
            confidence = float(np.max(posteriors))
            return label, posteriors, confidence
        except Exception as e:
            logger.warning(f"Error in regime prediction: {e}")
            return REGIME_RANGING, np.array([0.5, 0.3, 0.2]), 0.5
