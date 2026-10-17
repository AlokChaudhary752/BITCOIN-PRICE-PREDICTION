"""
Volatility and Return Estimators.
Strictly causal windows. Includes Parkinson and Garman-Klass estimators.
"""
import numpy as np
import pandas as pd


def compute_log_returns(series: pd.Series, periods: int = 1) -> pd.Series:
    """Compute causal log returns: ln(P_t / P_{t-k})."""
    return np.log(series / series.shift(periods))


def parkinson_volatility(high: pd.Series, low: pd.Series, window: int = 24) -> pd.Series:
    """
    Parkinson Volatility Estimator (High-Low estimator).
    5x more efficient than close-to-close volatility.
    sigma_p = sqrt( 1 / (4 * ln(2) * window) * sum( ln(H / L)^2 ) )
    """
    factor = 1.0 / (4.0 * np.log(2.0))
    log_hl = np.log(high / low) ** 2
    rolling_var = factor * log_hl.rolling(window=window).mean()
    return np.sqrt(rolling_var)


def garman_klass_volatility(
    open_p: pd.Series,
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 24,
) -> pd.Series:
    """
    Garman-Klass Volatility Estimator (OHLC estimator).
    8x more efficient than close-to-close volatility.
    """
    log_hl = np.log(high / low) ** 2
    log_co = np.log(close / open_p) ** 2
    gk_term = 0.5 * log_hl - (2.0 * np.log(2.0) - 1.0) * log_co
    rolling_var = gk_term.rolling(window=window).mean()
    return np.sqrt(np.maximum(rolling_var, 1e-12))


def realized_volatility(returns: pd.Series, window: int = 24) -> pd.Series:
    """Rolling sample standard deviation of hourly log returns."""
    return returns.rolling(window=window).std()
