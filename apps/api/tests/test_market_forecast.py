"""
Market, Forecast, and Analysis Endpoint Tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_market_endpoints(client: AsyncClient):
    # Live price
    p_resp = await client.get("/api/v1/market/price/live")
    assert p_resp.status_code == 200
    p_data = p_resp.json()
    assert "price" in p_data
    assert p_data["price"] > 0
    assert "realized_volatility" in p_data

    # History
    h_resp = await client.get("/api/v1/market/price/history?interval=1h&limit=50")
    assert h_resp.status_code == 200
    h_data = h_resp.json()
    assert len(h_data["candles"]) > 0

    # Orderbook
    ob_resp = await client.get("/api/v1/market/orderbook")
    assert ob_resp.status_code == 200
    ob_data = ob_resp.json()
    assert len(ob_data["bids"]) > 0
    assert len(ob_data["asks"]) > 0
    assert "imbalance_ratio" in ob_data

    # Onchain
    oc_resp = await client.get("/api/v1/market/onchain")
    assert oc_resp.status_code == 200
    oc_data = oc_resp.json()
    assert "fastest_fee" in oc_data


@pytest.mark.asyncio
async def test_forecast_endpoints(client: AsyncClient):
    # Live forecast
    f_resp = await client.get("/api/v1/forecast/predict")
    assert f_resp.status_code == 200
    f_data = f_resp.json()
    assert "current_price" in f_data
    assert "market_regime" in f_data
    assert "primary_signal" in f_data
    assert "horizons" in f_data
    assert "24h" in f_data["horizons"]
    assert "narrative" in f_data["explanation"]

    # All horizons
    all_resp = await client.get("/api/v1/forecast/predict/all")
    assert all_resp.status_code == 200
    all_data = all_resp.json()
    for h in ["1h", "4h", "24h", "7d", "30d"]:
        assert h in all_data

    # Model performance vs baselines
    perf_resp = await client.get("/api/v1/forecast/models/performance")
    assert perf_resp.status_code == 200
    perf_data = perf_resp.json()
    assert "walk_forward_metrics_24h" in perf_data

    # Model calibration
    cal_resp = await client.get("/api/v1/forecast/models/calibration")
    assert cal_resp.status_code == 200
    cal_data = cal_resp.json()
    assert "conformal_horizons" in cal_data

    # SHAP explanations
    exp_resp = await client.get("/api/v1/forecast/models/explain")
    assert exp_resp.status_code == 200
    exp_data = exp_resp.json()
    assert "global_importance" in exp_data


@pytest.mark.asyncio
async def test_analysis_and_backtest(client: AsyncClient):
    # Indicators
    ind_resp = await client.get("/api/v1/analysis/indicators")
    assert ind_resp.status_code == 200
    ind_data = ind_resp.json()
    assert "current_indicators" in ind_data

    # Sentiment
    sent_resp = await client.get("/api/v1/analysis/sentiment")
    assert sent_resp.status_code == 200
    sent_data = sent_resp.json()
    assert "current_score" in sent_data

    # Backtest simulation
    bt_payload = {
        "initial_capital": 100000.0,
        "fee_rate": 0.0006,
        "slippage": 0.0004,
        "stop_loss_pct": 0.02,
        "risk_per_trade_pct": 0.02,
    }
    bt_resp = await client.post("/api/v1/analysis/backtest", json=bt_payload)
    assert bt_resp.status_code == 200
    bt_data = bt_resp.json()
    assert "final_equity" in bt_data
    assert "sharpe_ratio" in bt_data
    assert "sortino_ratio" in bt_data
    assert "equity_curve" in bt_data
