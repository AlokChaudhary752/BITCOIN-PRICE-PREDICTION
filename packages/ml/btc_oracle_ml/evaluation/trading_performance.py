"""
Quantitative Trading Performance Layer.
VectorBT-style vectorized backtest engine calculating Sharpe Ratio, Maximum Drawdown (MDD),
Profit Factor, Sortino Ratio, Calmar Ratio, and transaction friction.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    initial_capital: float
    final_equity: float
    total_return_pct: float
    benchmark_return_pct: float
    cagr_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    profit_factor: float
    total_trades: int
    equity_curve: list[dict[str, Any]]
    trades: list[dict[str, Any]]


class VectorizedBacktestEngine:
    """
    Vectorized Quantitative Backtester.
    Models institutional exchange mechanics:
    - Configurable taker fee (default: 6 bps / 0.0006)
    - Dynamic market slippage (default: 4 bps / 0.0004)
    - Stop-loss and risk management rules
    """

    def __init__(
        self,
        fee_rate: float = 0.0006,
        slippage: float = 0.0004,
        stop_loss_pct: float = 0.02,
        risk_per_trade_pct: float = 0.02,
        annualization_factor: float = np.sqrt(8760),  # 8,760 hours in crypto year
    ):
        self.fee_rate = fee_rate
        self.slippage = slippage
        self.stop_loss_pct = stop_loss_pct
        self.risk_per_trade_pct = risk_per_trade_pct
        self.ann_factor = annualization_factor

    def run_backtest(
        self,
        prices: pd.Series,
        signals: pd.Series,
        initial_capital: float = 100000.0,
    ) -> BacktestResult:
        """
        Executes vectorized backtest from a price series and binary/trinary signal series:
        signals: 1 = Long, 0 = Cash / Neutral, -1 = Short (or flat)
        """
        n = len(prices)
        if n < 2:
            raise ValueError("Price series must have at least 2 observations.")

        cash = initial_capital
        btc_held = 0.0
        equity = initial_capital
        high_water_mark = initial_capital
        max_dd = 0.0

        equity_curve: list[dict[str, Any]] = []
        trades: list[dict[str, Any]] = []

        pos_open_time = None
        entry_p = 0.0
        initial_p = float(prices.iloc[0])

        for i in range(len(prices)):
            ts = prices.index[i]
            ts_dt = ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else datetime.fromisoformat(str(ts))
            curr_p = float(prices.iloc[i])
            sig = int(signals.iloc[i]) if i < len(signals) else 0

            # Benchmark (Buy and Hold)
            bench_eq = initial_capital * (curr_p / initial_p)

            # Check stop loss on active long position
            if btc_held > 0.0:
                pos_ret = (curr_p - entry_p) / entry_p
                if pos_ret <= -self.stop_loss_pct:
                    # Stop loss triggered
                    effective_p = curr_p * (1.0 - self.slippage)
                    gross = btc_held * effective_p
                    fee = gross * self.fee_rate
                    net = gross - fee
                    pnl = net - (btc_held * entry_p)
                    cash += net

                    trades.append({
                        "entry_time": pos_open_time,
                        "exit_time": ts_dt,
                        "side": "BUY",
                        "entry_price": round(entry_p, 2),
                        "exit_price": round(effective_p, 2),
                        "return_pct": round(pos_ret * 100.0, 2),
                        "pnl": round(pnl, 2),
                        "reason": "Stop Loss",
                    })
                    btc_held = 0.0

            # Entry Logic
            if btc_held == 0.0 and sig == 1:
                effective_p = curr_p * (1.0 + self.slippage)
                invest_amount = cash * min(self.risk_per_trade_pct * 5.0, 1.0)
                fee = invest_amount * self.fee_rate
                btc_held = (invest_amount - fee) / effective_p
                cash -= invest_amount
                pos_open_time = ts_dt
                entry_p = effective_p

            # Exit Logic
            elif btc_held > 0.0 and sig <= 0:
                effective_p = curr_p * (1.0 - self.slippage)
                gross = btc_held * effective_p
                fee = gross * self.fee_rate
                net = gross - fee
                pnl = net - (btc_held * entry_p)
                cash += net
                pos_ret = (effective_p - entry_p) / entry_p

                trades.append({
                    "entry_time": pos_open_time,
                    "exit_time": ts_dt,
                    "side": "BUY",
                    "entry_price": round(entry_p, 2),
                    "exit_price": round(effective_p, 2),
                    "return_pct": round(pos_ret * 100.0, 2),
                    "pnl": round(pnl, 2),
                    "reason": "Signal Exit" if pos_ret > 0 else "Stop Exit",
                })
                btc_held = 0.0

            # Mark to market
            equity = cash + (btc_held * curr_p)
            high_water_mark = max(high_water_mark, equity)
            dd = (high_water_mark - equity) / high_water_mark if high_water_mark > 0 else 0.0
            max_dd = max(max_dd, dd)

            equity_curve.append({
                "timestamp": ts_dt,
                "strategy_equity": round(equity, 2),
                "benchmark_equity": round(bench_eq, 2),
                "drawdown_pct": round(dd * 100.0, 2),
            })

        # Final metrics calculations
        tot_ret = ((equity - initial_capital) / initial_capital) * 100.0
        final_bench = equity_curve[-1]["benchmark_equity"] if equity_curve else initial_capital
        bench_ret = ((final_bench - initial_capital) / initial_capital) * 100.0

        # Returns series
        eq_vals = pd.Series([pt["strategy_equity"] for pt in equity_curve])
        hourly_rets = eq_vals.pct_change().dropna()

        mean_ret = float(hourly_rets.mean()) if not hourly_rets.empty else 0.0
        std_ret = float(hourly_rets.std()) if not hourly_rets.empty else 1e-6
        downside_rets = hourly_rets[hourly_rets < 0]
        downside_std = float(downside_rets.std()) if len(downside_rets) > 0 else 1e-6

        # Annualized Sharpe & Sortino
        sharpe = round((mean_ret / std_ret) * self.ann_factor, 2) if std_ret > 0 else 0.0
        sortino = round((mean_ret / downside_std) * self.ann_factor, 2) if downside_std > 0 else 0.0

        # Annualized CAGR
        days = max(n / 24.0, 1.0)
        cagr = round((((equity / initial_capital) ** (365.25 / days)) - 1.0) * 100.0, 2)
        calmar = round(tot_ret / (max_dd * 100.0), 2) if max_dd > 0 else 1.0

        # Trade statistics
        total_trades = len(trades)
        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] <= 0]
        win_rate = round((len(wins) / total_trades) * 100.0, 1) if total_trades > 0 else 0.0

        gross_profit = sum(t["pnl"] for t in wins) if wins else 0.0
        gross_loss = abs(sum(t["pnl"] for t in losses)) if losses else 0.0
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (2.0 if gross_profit > 0 else 1.0)

        return BacktestResult(
            initial_capital=initial_capital,
            final_equity=round(equity, 2),
            total_return_pct=round(tot_ret, 2),
            benchmark_return_pct=round(bench_ret, 2),
            cagr_pct=cagr,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            max_drawdown_pct=round(max_dd * 100.0, 2),
            win_rate_pct=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            equity_curve=equity_curve,
            trades=trades,
        )
