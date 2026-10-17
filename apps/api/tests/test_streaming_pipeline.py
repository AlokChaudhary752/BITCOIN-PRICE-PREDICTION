"""
Unit and Integration Tests for Real-Time Streaming Inference Pipeline.
Tests Z-Score outlier filter, CandleRingBuffer in-memory store, LivePredictor, and WebSocket push.
"""
import asyncio
from datetime import UTC, datetime

import numpy as np
import pytest

from apps.api.src.binance import ZScoreOutlierFilter
from apps.api.src.live_inference import (
    CandleRingBuffer,
    LivePredictor,
    StreamingInferencePipeline,
)


def test_z_score_outlier_filter():
    """Verify that anomalous price spikes ('Fat Finger' trades) are rejected."""
    outlier_filter = ZScoreOutlierFilter(window_size=30, z_threshold=4.0, max_pct_dev=0.035)

    # Feed steady prices around $80,000
    base_price = 80000.0
    for _ in range(20):
        p = base_price + float(np.random.normal(0, 50))
        assert outlier_filter.is_valid(p) is True

    # 1. Normal micro-fluctuation (+0.2%) should pass
    assert outlier_filter.is_valid(80150.0) is True

    # 2. Extreme anomalous fat-finger spike (+10%, e.g. $88,000) must be REJECTED
    assert outlier_filter.is_valid(88000.0) is False

    # 3. Flash crash anomaly (-12%, e.g. $70,000) must be REJECTED
    assert outlier_filter.is_valid(70000.0) is False

    # 4. Invalid numbers (negative or NaN) must be rejected
    assert outlier_filter.is_valid(-100.0) is False
    assert outlier_filter.is_valid(float("nan")) is False


def test_candle_ring_buffer_in_memory():
    """Verify low-latency sliding-window candle buffer without database reads."""
    buffer = CandleRingBuffer(capacity=50)

    # Clear for test isolation
    buffer.candles.clear()

    # Initial tick
    tick1 = {
        "price": 80000.0,
        "volume": 2.5,
        "is_candle_closed": False,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    is_closed, p = buffer.on_tick(tick1)
    assert p == 80000.0
    assert len(buffer.candles) == 1

    # Second tick updates active bar
    tick2 = {
        "price": 80500.0,
        "volume": 1.5,
        "is_candle_closed": False,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    is_closed, p = buffer.on_tick(tick2)
    assert is_closed is False
    assert buffer.candles[-1]["high"] == 80500.0
    assert buffer.candles[-1]["close"] == 80500.0

    # Tick with is_candle_closed=True triggers candle finalization
    tick3 = {
        "price": 80600.0,
        "volume": 3.0,
        "is_candle_closed": True,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    is_closed, _ = buffer.on_tick(tick3)
    assert is_closed is True
    assert len(buffer.candles) == 2

    # Fast in-memory dataframe conversion
    df = buffer.to_dataframe()
    assert len(df) == 2
    assert "close" in df.columns
    assert "volume" in df.columns


def test_live_predictor_streaming_inference():
    """Verify streaming inference triggers and emits complete forecast payload."""
    buffer = CandleRingBuffer(capacity=100)

    # Ensure buffer has enough candles for FeaturePipeline (e.g. 50 bars)
    now = datetime.now(UTC)
    base_p = 80000.0
    for i in range(50):
        buffer.candles.append({
            "timestamp": now,
            "open": base_p,
            "high": base_p + 100,
            "low": base_p - 100,
            "close": base_p + (i * 10),
            "volume": 50.0,
            "taker_buy_base_volume": 25.0,
            "number_of_trades": 150,
            "quote_asset_volume": 50.0 * base_p,
        })

    predictor = LivePredictor(buffer=buffer, move_threshold_pct=0.25, min_interval_sec=0.0)

    # Small tick (< 0.25% move) should not trigger inference
    assert predictor.should_predict(base_p + 500, is_candle_closed=False) is True  # initial run

    payload = predictor.predict_streaming(current_price=80500.0, is_candle_closed=True)

    assert payload["type"] == "FORECAST_UPDATE"
    assert payload["symbol"] == "BTCUSDT"
    assert payload["current_price"] == 80500.0
    assert "market_regime" in payload
    assert "regime_confidence" in payload
    assert "expected_volatility" in payload
    assert "primary_predictor" in payload
    assert "horizons" in payload
    assert "24h" in payload["horizons"]

    h24 = payload["horizons"]["24h"]
    assert "interval_90" in h24
    assert "interval_50" in h24
    assert h24["interval_90"]["lower"] < h24["interval_90"]["upper"]


@pytest.mark.asyncio
async def test_streaming_pipeline_async_flow():
    """Verify end-to-end async queue ingestion and broadcast callback execution."""
    broadcasted_messages = []

    async def mock_broadcast(msg: dict):
        broadcasted_messages.append(msg)

    pipeline = StreamingInferencePipeline(broadcast_fn=mock_broadcast)

    # Manually prime with enough bars
    now = datetime.now(UTC)
    for i in range(40):
        pipeline.buffer.candles.append({
            "timestamp": now,
            "open": 80000.0,
            "high": 80100.0,
            "low": 79900.0,
            "close": 80000.0 + i * 5,
            "volume": 30.0,
            "taker_buy_base_volume": 15.0,
            "number_of_trades": 100,
            "quote_asset_volume": 2400000.0,
        })

    # Start pipeline
    pipeline.is_running = True
    worker_task = asyncio.create_task(pipeline._inference_worker_loop())

    # Put a tick into queue
    test_tick = {
        "type": "TICK",
        "symbol": "BTCUSDT",
        "price": 81000.0,
        "volume": 10.0,
        "is_candle_closed": True,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    await pipeline.queue.put(test_tick)

    # Allow worker to process
    await asyncio.sleep(0.3)

    pipeline.is_running = False
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass

    # Verify that messages were broadcasted
    assert len(broadcasted_messages) >= 1
    # Check that TICK was broadcasted
    tick_msgs = [m for m in broadcasted_messages if m.get("type") == "TICK"]
    assert len(tick_msgs) >= 1
    assert tick_msgs[0]["price"] == 81000.0
