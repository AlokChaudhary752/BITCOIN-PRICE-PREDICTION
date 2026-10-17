"""
Technical Indicators computed with strictly causal windows.
No lookahead bias. Compatible with institutional feature pipelines.
"""
import numpy as np
import pandas as pd


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's Relative Strength Index (RSI)."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's exponential smoothing
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, 1e-12)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def compute_macd(
    close: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> pd.DataFrame:
    """Moving Average Convergence Divergence (MACD)."""
    ema_fast = close.ewm(span=fast_period, adjust=False).mean()
    ema_slow = close.ewm(span=slow_period, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    macd_hist = macd_line - signal_line

    return pd.DataFrame(
        {
            "macd_line": macd_line,
            "macd_signal": signal_line,
            "macd_hist": macd_hist,
        },
        index=close.index,
    )


def compute_bollinger_bands(
    close: pd.Series,
    period: int = 20,
    num_std: float = 2.0,
) -> pd.DataFrame:
    """Bollinger Bands (Middle, Upper, Lower, Bandwidth, %B)."""
    middle = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)

    bandwidth = (upper - lower) / middle.replace(0, 1e-12)
    pct_b = (close - lower) / (upper - lower).replace(0, 1e-12)

    return pd.DataFrame(
        {
            "bb_middle": middle,
            "bb_upper": upper,
            "bb_lower": lower,
            "bb_bandwidth": bandwidth,
            "bb_pct_b": pct_b,
        },
        index=close.index,
    )


def compute_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Average True Range (ATR)."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    return atr


def compute_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3,
) -> pd.DataFrame:
    """Stochastic Oscillator (%K and %D)."""
    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    denom = (highest_high - lowest_low).replace(0, 1e-12)

    fast_k = 100.0 * ((close - lowest_low) / denom)
    fast_d = fast_k.rolling(d_period).mean()

    return pd.DataFrame(
        {"stoch_k": fast_k, "stoch_d": fast_d},
        index=close.index,
    )


def compute_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume (OBV)."""
    price_change = close.diff()
    direction = np.sign(price_change).fillna(0)
    obv = (direction * volume).cumsum()
    return obv


def compute_vwap_deviation(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    volume: pd.Series,
    window: int = 24,
) -> pd.Series:
    """Rolling 24-hour VWAP percentage deviation: (Close - VWAP) / VWAP."""
    typical_price = (high + low + close) / 3.0
    cum_vol_price = (typical_price * volume).rolling(window).sum()
    cum_vol = volume.rolling(window).sum().replace(0, 1e-12)
    vwap = cum_vol_price / cum_vol
    return (close - vwap) / vwap
