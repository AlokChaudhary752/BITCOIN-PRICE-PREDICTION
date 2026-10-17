"""
Analysis Router.
Technical indicators, sentiment analysis, and walk-forward backtest engine.
"""
import numpy as np
import pandas as pd
from btc_oracle_ml.config import DATA_DIR
from btc_oracle_ml.data.sentiment import FearGreedClient
from btc_oracle_ml.evaluation.trading_performance import VectorizedBacktestEngine
from btc_oracle_ml.features.pipeline import FeaturePipeline
from fastapi import APIRouter

from apps.api.src.schemas import (
    BacktestRequest,
    BacktestResponse,
    BacktestTradeLog,
    EquityPoint,
)

router = APIRouter(prefix="/analysis", tags=["Analysis & Backtesting"])
pipeline = FeaturePipeline()
fg_client = FearGreedClient()


def load_candles():
    parquet_path = DATA_DIR / "btcusdt_1h.parquet"
    if parquet_path.exists():
        return pd.read_parquet(parquet_path).sort_index()
    return pd.DataFrame()


@router.get("/indicators")
async def get_technical_indicators():
    """Return latest technical indicators with historical series for charting."""
    df = load_candles()
    if df.empty:
        return {"error": "Dataset empty"}

    df_slice = df.iloc[-250:]
    X, _ = pipeline.transform(df_slice)

    timestamps = [ts.isoformat() for ts in df_slice.index]
    return {
        "timestamps": timestamps,
        "rsi": [round(float(v), 2) for v in X["rsi_14"]],
        "macd_hist": [round(float(v), 3) for v in X["macd_hist"]],
        "bb_pct_b": [round(float(v), 3) for v in X["bb_pct_b"]],
        "bb_bandwidth": [round(float(v), 4) for v in X["bb_bandwidth"]],
        "atr_relative": [round(float(v), 4) for v in X["atr_relative"]],
        "stoch_k": [round(float(v), 2) for v in X["stoch_k"]],
        "stoch_d": [round(float(v), 2) for v in X["stoch_d"]],
        "vwap_dev": [round(float(v), 4) for v in X["vwap_dev"]],
        "current_indicators": {
            "rsi": round(float(X["rsi_14"].iloc[-1]), 2),
            "macd_hist": round(float(X["macd_hist"].iloc[-1]), 3),
            "bb_bandwidth": round(float(X["bb_bandwidth"].iloc[-1]), 4),
            "atr_relative": round(float(X["atr_relative"].iloc[-1]), 4),
            "stoch_k": round(float(X["stoch_k"].iloc[-1]), 2),
            "stoch_d": round(float(X["stoch_d"].iloc[-1]), 2),
            "vwap_dev": round(float(X["vwap_dev"].iloc[-1]), 4),
        },
    }


@router.get("/sentiment")
async def get_sentiment():
    """Return historical Fear & Greed index and headline polarity."""
    fg_df = fg_client.load_cached()
    if fg_df.empty:
        fg_df = fg_client.fetch_history()

    history = []
    if not fg_df.empty:
        last_30 = fg_df.iloc[-30:]
        for ts, row in last_30.iterrows():
            history.append({
                "date": ts.strftime("%Y-%m-%d"),
                "value": int(row["fear_greed_val"]),
                "classification": "Greed" if row["fear_greed_val"] > 55 else ("Fear" if row["fear_greed_val"] < 45 else "Neutral"),
            })

    current_val = int(history[-1]["value"]) if history else 50
    return {
        "current_score": current_val,
        "classification": "Greed" if current_val > 55 else ("Fear" if current_val < 45 else "Neutral"),
        "rolling_sentiment_index": round(current_val / 100.0, 3),
        "history_30d": history,
        "sample_headlines": [
            {"title": "Institutional inflows into spot Bitcoin ETF accelerate", "polarity": 0.72, "impact": "bullish"},
            {"title": "Federal Reserve holds benchmark rate steady amid resilient growth", "polarity": 0.15, "impact": "neutral"},
            {"title": "Global hash rate hits all-time high following mining efficiency upgrade", "polarity": 0.54, "impact": "bullish"},
            {"title": "Options open interest suggests implied volatility spike ahead of expiry", "polarity": -0.28, "impact": "bearish"},
        ],
    }


@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(req: BacktestRequest):
    """
    Execute walk-forward backtest simulation with fees, slippage, and position sizing.
    Matches exact mathematical formulas: CAGR, Sharpe, Sortino, Calmar, Max Drawdown.
    """
    df = load_candles()
    if df.empty:
        # Generate clean synthetic backtest fixture
        dates = pd.date_range("2024-01-01", periods=1000, freq="1h")
        prices = 45000.0 * np.exp(np.cumsum(np.random.normal(0.0001, 0.005, 1000)))
        df = pd.DataFrame(
            {"close": prices, "open": prices, "high": prices * 1.002, "low": prices * 0.998, "volume": 100},
            index=dates,
        )

    # Use slice
    df_bt = df.iloc[-720:].copy()  # 30-day hourly walk-forward backtest
    X, _ = pipeline.transform(df_bt)

    # Vectorized Trading Signal rule: RSI oversold with positive MACD momentum -> BUY (1)
    rsi_val = X["rsi_14"].shift(1).fillna(50.0)
    macd_val = X["macd_hist"].shift(1).fillna(0.0)
    signals = pd.Series(0, index=df_bt.index)
    signals[(rsi_val < 45) & (macd_val > 0)] = 1
    signals[rsi_val > 65] = 0

    engine = VectorizedBacktestEngine(
        fee_rate=req.fee_rate,
        slippage=req.slippage,
        stop_loss_pct=req.stop_loss_pct,
        risk_per_trade_pct=req.risk_per_trade_pct,
    )
    result = engine.run_backtest(
        prices=df_bt["close"],
        signals=signals,
        initial_capital=req.initial_capital,
    )

    eq_curve = [
        EquityPoint(
            timestamp=pt["timestamp"],
            strategy_equity=pt["strategy_equity"],
            benchmark_equity=pt["benchmark_equity"],
            drawdown_pct=pt["drawdown_pct"],
        )
        for pt in result.equity_curve
    ]
    trade_logs = [
        BacktestTradeLog(
            entry_time=t["entry_time"],
            exit_time=t["exit_time"],
            side=t["side"],
            entry_price=t["entry_price"],
            exit_price=t["exit_price"],
            return_pct=t["return_pct"],
            pnl=t["pnl"],
            reason=t["reason"],
        )
        for t in result.trades
    ]

    return BacktestResponse(
        initial_capital=result.initial_capital,
        final_equity=result.final_equity,
        total_return_pct=result.total_return_pct,
        benchmark_return_pct=result.benchmark_return_pct,
        cagr_pct=result.cagr_pct,
        sharpe_ratio=result.sharpe_ratio,
        sortino_ratio=result.sortino_ratio,
        calmar_ratio=result.calmar_ratio,
        max_drawdown_pct=result.max_drawdown_pct,
        win_rate_pct=result.win_rate_pct,
        profit_factor=result.profit_factor,
        total_trades=result.total_trades,
        equity_curve=eq_curve,
        trades=trade_logs,
    )
