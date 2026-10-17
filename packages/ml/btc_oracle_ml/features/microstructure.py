"""
Microstructure Feature Engineering.
Calculates Order Flow Imbalance (OFI), Cumulative Volume Delta (CVD),
and aggressive taker participant dynamics.
"""
import pandas as pd


def compute_order_flow_imbalance(
    taker_buy_vol: pd.Series,
    taker_sell_vol: pd.Series,
    window: int = 24,
) -> tuple[pd.Series, pd.Series]:
    """
    Computes Order Flow Imbalance (OFI) and its rolling Z-score.
    OFI_raw = (V_buy - V_sell) / (V_buy + V_sell + eps)
    OFI_z = (OFI - rolling_mean(OFI)) / (rolling_std(OFI) + eps)
    """
    total_vol = taker_buy_vol + taker_sell_vol
    eps = 1e-12
    ofi_raw = (taker_buy_vol - taker_sell_vol) / (total_vol + eps)
    ofi_raw = ofi_raw.clip(-1.0, 1.0)

    # Rolling Z-score
    roll_mean = ofi_raw.rolling(window, min_periods=1).mean()
    roll_std = ofi_raw.rolling(window, min_periods=1).std().replace(0, eps).fillna(eps)
    ofi_zscore = ((ofi_raw - roll_mean) / roll_std).clip(-4.0, 4.0)

    return ofi_raw, ofi_zscore


def compute_cumulative_volume_delta(
    taker_buy_vol: pd.Series,
    taker_sell_vol: pd.Series,
    window: int = 24,
) -> tuple[pd.Series, pd.Series]:
    """
    Computes Cumulative Volume Delta (CVD) and stationary normalized CVD momentum.
    Delta = V_buy - V_sell
    Normalized CVD Momentum = rolling_sum(Delta, window) / rolling_sum(Total_Vol, window)
    """
    delta = taker_buy_vol - taker_sell_vol
    total_vol = taker_buy_vol + taker_sell_vol
    eps = 1e-12

    # Stationary rolling volume delta momentum
    roll_delta = delta.rolling(window, min_periods=1).sum()
    roll_total = total_vol.rolling(window, min_periods=1).sum().replace(0, eps).fillna(eps)
    cvd_momo = (roll_delta / roll_total).clip(-1.0, 1.0)

    # CVD acceleration (rate of change of volume delta momentum)
    cvd_accel = cvd_momo.diff(4).fillna(0.0).clip(-1.0, 1.0)

    return cvd_momo, cvd_accel
