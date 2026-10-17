"""
Unit tests for Regime-Conditional Router and VectorBT-style Backtest Engine.
"""
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
from btc_oracle_ml.evaluation.trading_performance import VectorizedBacktestEngine
from btc_oracle_ml.models.conformal import ConformalCalibrator
from btc_oracle_ml.models.ensemble import RegimeConditionalRouter


def test_regime_conditional_router_weight_switching():
    # Mock LightGBM and GRU
    mock_lgbm = MagicMock()
    mock_lgbm.predict_quantiles.return_value = {
        0.05: np.array([-0.02]),
        0.25: np.array([-0.01]),
        0.50: np.array([0.015]),
        0.75: np.array([0.025]),
        0.95: np.array([0.04]),
    }
    mock_gru = MagicMock()
    mock_gru.predict_quantiles.return_value = {
        0.05: np.array([-0.04]),
        0.25: np.array([-0.02]),
        0.50: np.array([-0.005]),
        0.75: np.array([0.01]),
        0.95: np.array([0.03]),
    }

    calibrator = ConformalCalibrator()
    router = RegimeConditionalRouter(
        horizon_name="24h",
        lgbm_model=mock_lgbm,
        gru_model=mock_gru,
        calibrator=calibrator,
    )

    X_dummy = pd.DataFrame({"feat1": [1.0]})

    # 1. Test Trending Bull State Routing (p_bull = 0.85)
    bull_res = router.predict_probabilistic(
        X_sample=X_dummy,
        current_price=60000.0,
        regime_label="trending_bull",
        current_vol=0.015,
        vol_95th_percentile=0.030,
        regime_probs=np.array([0.05, 0.85, 0.10]),
        regime_confidence=0.85,
    )
    assert bull_res["primary_predictor"] == "LightGBM"
    assert bull_res["expert_weights"]["lgbm"] >= 0.60
    assert bull_res["regime_confidence"] == 85.0
    assert "expected_volatility" in bull_res

    # 2. Test High-Volatility Shock State Routing (p_shock = 0.85)
    shock_res = router.predict_probabilistic(
        X_sample=X_dummy,
        current_price=60000.0,
        regime_label="high_volatility",
        current_vol=0.035,
        vol_95th_percentile=0.030,
        regime_probs=np.array([0.05, 0.10, 0.85]),
        regime_confidence=0.85,
    )
    assert shock_res["primary_predictor"] == "AttentionGRU"
    assert shock_res["expert_weights"]["gru"] >= 0.60
    assert shock_res["expected_volatility"] > 0


def test_vectorized_backtest_performance_metrics():
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=100, freq="1h")
    # Upward trending price
    prices = pd.Series(50000.0 * np.exp(np.cumsum(np.random.normal(0.001, 0.005, 100))), index=dates)

    # Buy at bar 10, exit at bar 50
    signals = pd.Series(0, index=dates)
    signals.iloc[10:50] = 1

    engine = VectorizedBacktestEngine(
        fee_rate=0.0006,  # 6 bps
        slippage=0.0004,  # 4 bps
        stop_loss_pct=0.03,
        risk_per_trade_pct=0.10,
    )

    result = engine.run_backtest(prices=prices, signals=signals, initial_capital=100000.0)

    assert result.initial_capital == 100000.0
    assert result.total_trades >= 1
    assert result.sharpe_ratio != 0.0
    assert result.profit_factor >= 0.0
    assert result.max_drawdown_pct >= 0.0
    assert len(result.equity_curve) == len(prices)
    assert result.equity_curve[0]["strategy_equity"] == 100000.0
