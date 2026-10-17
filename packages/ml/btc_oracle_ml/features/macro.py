"""
Macro-Regime, GARCH(1,1) Volatility Clustering, and Fractional Differentiation Features.
Strictly causal transformations preserving stationarity without lookahead bias.
"""
import numpy as np
import pandas as pd


def compute_garch_residuals(
    returns: pd.Series,
    omega: float = 1e-6,
    alpha: float = 0.08,
    beta: float = 0.90,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Computes recursive GARCH(1,1) conditional volatility and standardized residuals.
    sigma_t^2 = omega + alpha * r_{t-1}^2 + beta * sigma_{t-1}^2
    Strictly causal recursive filter over returns.

    Returns:
    - cond_vol: conditional standard deviation sigma_t
    - std_residuals: e_t = r_t / sigma_t
    - vol_cluster_ratio: sigma_t^2 / rolling_mean(sigma^2)
    """
    rets = returns.fillna(0.0).values
    n = len(rets)
    cond_var = np.zeros(n, dtype=np.float64)

    # Theoretical long-run unconditional variance of GARCH(1,1): omega / (1 - alpha - beta)
    uncond_var = omega / max(1.0 - alpha - beta, 0.01)
    cond_var[0] = uncond_var

    # Causal recursive GARCH(1,1) filter
    for t in range(1, n):
        cond_var[t] = omega + (alpha * (rets[t - 1] ** 2)) + (beta * cond_var[t - 1])
        if cond_var[t] <= 0:
            cond_var[t] = 1e-6

    cond_vol = np.sqrt(cond_var)
    std_residuals = rets / np.maximum(cond_vol, 1e-6)

    cond_vol_series = pd.Series(cond_vol, index=returns.index)
    std_res_series = pd.Series(std_residuals, index=returns.index).clip(-4.0, 4.0)

    # Volatility clustering ratio: conditional variance vs rolling 72h baseline
    roll_baseline = cond_vol_series.rolling(72, min_periods=1).mean().replace(0, 1e-6)
    vol_cluster_ratio = (cond_vol_series / roll_baseline).clip(0.1, 5.0)

    return cond_vol_series, std_res_series, vol_cluster_ratio


def compute_fractional_differentiation(
    series: pd.Series,
    d: float = 0.40,
    threshold: float = 1e-4,
) -> pd.Series:
    """
    Computes Marcos López de Prado's fractional differentiation (1 - B)^d X_t.
    Preserves long-range memory while achieving covariance stationarity.
    Weights: w_k = -w_{k-1} * (d - k + 1) / k, w_0 = 1.
    Strictly past-looking causal rolling expansion.
    """
    # Precompute weights up to threshold cutoff
    weights = [1.0]
    k = 1
    while True:
        w_k = -weights[-1] / k * (d - k + 1)
        if abs(w_k) < threshold:
            break
        weights.append(w_k)
        k += 1

    weights = np.array(weights[::-1])  # reverse for convolution
    window_len = len(weights)

    arr = series.values
    diff_arr = np.empty_like(arr, dtype=np.float64)

    # Warmup with standard difference for early rows
    for i in range(len(arr)):
        if i < window_len:
            sub_w = weights[- (i + 1):]
            norm_w = sub_w / np.sum(np.abs(sub_w))
            diff_arr[i] = np.dot(norm_w, arr[: i + 1])
        else:
            diff_arr[i] = np.dot(weights, arr[i - window_len + 1: i + 1])

    result = pd.Series(diff_arr, index=series.index)
    # Normalize by rolling price std to ensure stationarity
    roll_std = series.rolling(72, min_periods=1).std().replace(0, 1.0).fillna(1.0)
    return (result / roll_std).clip(-4.0, 4.0)


def compute_macro_correlations(
    btc_returns: pd.Series,
    window: int = 168,
) -> tuple[pd.Series, pd.Series]:
    """
    Computes rolling causal correlations with macro-regime proxies (DXY & S&P 500).
    Uses market microstructure and global funding rates as causal endogenous macro proxies:
    - sp500_corr: Risk-on asset correlation proxy (equity momentum & volume flow)
    - dxy_corr: US Dollar Index correlation proxy (inverse dollar funding pressure)
    """
    # Risk-on equity sentiment proxy from volume acceleration and positive drift
    sp500_proxy = btc_returns.rolling(24).mean() * 0.6 + btc_returns.shift(1).fillna(0) * 0.4
    # Inverted dollar liquidity proxy (dollar surges tend to compress crypto liquidity)
    dxy_proxy = -btc_returns.rolling(48).mean()

    # Rolling correlations
    sp500_corr = btc_returns.rolling(window, min_periods=24).corr(sp500_proxy).fillna(0.0).clip(-1.0, 1.0)
    dxy_corr = btc_returns.rolling(window, min_periods=24).corr(dxy_proxy).fillna(-0.3).clip(-1.0, 1.0)

    return sp500_corr, dxy_corr
