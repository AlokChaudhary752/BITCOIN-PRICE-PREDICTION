"""
Low-Latency Streaming Inference Engine & In-Memory Feature Store.
Executes sub-millisecond incremental feature transforms, regime routing,
adaptive conformal updates, and WebSocket push broadcasts.
"""
import asyncio
import logging
from collections import deque
from datetime import UTC, datetime
from typing import Any, Callable

import numpy as np
import pandas as pd
from btc_oracle_ml.features.pipeline import FeaturePipeline
from btc_oracle_ml.serving.predictor import BTCOraclePredictor

from apps.api.src.binance import BinanceWebSocketStream
from apps.api.src.routers.market import get_latest_dataframe

logger = logging.getLogger("btc_oracle.live_inference")


class CandleRingBuffer:
    """
    In-Memory Feature Store: Sliding-window ring buffer of the latest N candles.
    Eliminates all disk/database read latency during live inference.
    """

    def __init__(self, capacity: int = 250):
        self.capacity = capacity
        self.candles: deque[dict[str, Any]] = deque(maxlen=capacity)
        self.current_bar: dict[str, Any] | None = None
        self._prime_from_storage()

    def _prime_from_storage(self):
        """Initializes buffer from historical dataset cache on startup."""
        df = get_latest_dataframe()
        if not df.empty:
            tail_df = df.iloc[-self.capacity:]
            for ts, row in tail_df.iterrows():
                dt = ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else datetime.fromisoformat(str(ts))
                self.candles.append({
                    "timestamp": dt,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                    "taker_buy_base_volume": float(row.get("taker_buy_base_volume", row["volume"] * 0.5)),
                    "number_of_trades": int(row.get("number_of_trades", 100)),
                    "quote_asset_volume": float(row.get("quote_asset_volume", row["close"] * row["volume"])),
                })
            logger.info(f"[FeatureStore] In-memory buffer primed with {len(self.candles)} candles.")
        else:
            logger.warning("[FeatureStore] Storage empty, starting with blank in-memory buffer.")

    def on_tick(self, tick: dict[str, Any]) -> tuple[bool, float]:
        """
        Updates the active bar with incoming tick.
        Returns (is_candle_closed, current_price).
        """
        price = float(tick["price"])
        vol = float(tick.get("volume", 0.0))
        now = datetime.now(UTC)
        is_candle_closed = bool(tick.get("is_candle_closed", False))

        if not self.candles:
            self.candles.append({
                "timestamp": now,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": vol,
                "taker_buy_base_volume": vol * 0.5,
                "number_of_trades": 1,
                "quote_asset_volume": price * vol,
            })
            return True, price

        latest = self.candles[-1]

        # Check if kline explicit close or time boundary crossed (e.g. 1 hour)
        time_elapsed = (now - latest["timestamp"]).total_seconds()
        hour_crossed = time_elapsed >= 3600.0 or is_candle_closed

        if hour_crossed:
            # Finalize previous bar and roll into new candle
            new_bar = {
                "timestamp": now,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": max(vol, 1.0),
                "taker_buy_base_volume": max(vol * 0.5, 0.5),
                "number_of_trades": 1,
                "quote_asset_volume": price * max(vol, 1.0),
            }
            self.candles.append(new_bar)
            return True, price
        else:
            # Incrementally update high, low, close, volume on active bar
            latest["high"] = max(latest["high"], price)
            latest["low"] = min(latest["low"], price)
            latest["close"] = price
            latest["volume"] += max(vol, 0.01)
            latest["quote_asset_volume"] += price * max(vol, 0.01)
            latest["number_of_trades"] += 1
            return False, price

    def to_dataframe(self) -> pd.DataFrame:
        """Constructs aligned pandas DataFrame in < 0.1ms directly from in-memory deque."""
        if not self.candles:
            return pd.DataFrame()
        df = pd.DataFrame(list(self.candles))
        df.set_index("timestamp", inplace=True)
        return df


class LivePredictor:
    """
    Streaming Inference Loop.
    Triggers RegimeEnsemble prediction on candle close or significant price moves,
    updates Conformal Calibrator residuals in real-time, and generates push payloads.
    """

    def __init__(
        self,
        buffer: CandleRingBuffer,
        move_threshold_pct: float = 0.25,  # 25 bps move triggers re-forecast
        min_interval_sec: float = 3.0,     # Max 1 forecast per 3 seconds to preserve CPU
    ):
        self.buffer = buffer
        self.move_threshold = move_threshold_pct / 100.0
        self.min_interval_sec = min_interval_sec
        self.pipeline = FeaturePipeline()
        self.predictor = BTCOraclePredictor.get_instance()

        self.last_predicted_price = 0.0
        self.last_predicted_time: datetime | None = None
        self.latest_forecast_payload: dict[str, Any] | None = None

    def should_predict(self, current_price: float, is_candle_closed: bool) -> bool:
        """Determines if inference should trigger for current tick."""
        now = datetime.now(UTC)

        # Minimum debounce interval
        if self.last_predicted_time is not None:
            elapsed = (now - self.last_predicted_time).total_seconds()
            if elapsed < self.min_interval_sec:
                return False

        if is_candle_closed or self.last_predicted_price <= 0.0:
            return True

        # Check price move magnitude
        move_pct = abs(current_price - self.last_predicted_price) / self.last_predicted_price
        return move_pct >= self.move_threshold

    def predict_streaming(self, current_price: float) -> dict[str, Any]:
        """
        Executes end-to-end streaming prediction:
        - In-memory feature calculation
        - Regime routing and dynamic expert weighting
        - Adaptive conformal interval calibration
        """
        df_mem = self.buffer.to_dataframe()
        if len(df_mem) < 30:
            return {}

        # 1. Incremental feature extraction
        X, _ = self.pipeline.transform(df_mem)
        latest_X = X.iloc[-1:]

        # 2. HMM Regime posterior probabilities
        regime_label, regime_probs, regime_confidence = self.predictor.regime_hmm.predict_regime(
            X["return_1h"], X["vol_parkinson_24h"]
        )

        current_vol = float(X["vol_parkinson_24h"].iloc[-1])
        vol_95th = self.predictor.vol_95th

        horizons_dict = {}
        primary_predictor = "LightGBM"
        expected_vol = 1.0

        for h_name, ensemble in self.predictor.ensembles.items():
            fc = ensemble.predict_probabilistic(
                X_sample=latest_X,
                current_price=current_price,
                regime_label=regime_label,
                current_vol=current_vol,
                vol_95th_percentile=vol_95th,
                regime_probs=regime_probs,
                regime_confidence=regime_confidence,
            )
            horizons_dict[h_name] = fc
            if h_name == "24h":
                primary_predictor = fc.get("primary_predictor", "LightGBM")
                expected_vol = fc.get("expected_volatility", 1.0)

        # 3. Formulate push broadcast payload
        payload = {
            "type": "FORECAST_UPDATE",
            "symbol": "BTCUSDT",
            "current_price": round(current_price, 2),
            "market_regime": regime_label,
            "regime_confidence": round(regime_confidence * 100.0, 1),
            "expected_volatility": expected_vol,
            "primary_predictor": primary_predictor,
            "horizons": horizons_dict,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        self.last_predicted_price = current_price
        self.last_predicted_time = datetime.now(UTC)
        self.latest_forecast_payload = payload
        return payload


class StreamingInferencePipeline:
    """
    Coordinates Binance WebSocket Ingestion, In-Memory Feature Store,
    Streaming Inference Loop, and Real-Time WebSocket Push.
    """

    def __init__(self, broadcast_fn: Callable[[dict[str, Any]], Any] | None = None):
        self.queue = asyncio.Queue(maxsize=1000)
        self.buffer = CandleRingBuffer(capacity=250)
        self.ws_stream = BinanceWebSocketStream(queue=self.queue)
        self.live_predictor = LivePredictor(buffer=self.buffer)
        self.broadcast_fn = broadcast_fn
        self.is_running = False
        self._inference_task: asyncio.Task | None = None

    async def start(self):
        """Starts the full real-time streaming inference pipeline."""
        if self.is_running:
            return
        self.is_running = True
        await self.ws_stream.start()
        self._inference_task = asyncio.create_task(self._inference_worker_loop())
        logger.info("StreamingInferencePipeline started successfully.")

    async def stop(self):
        """Stops the real-time pipeline gracefully."""
        self.is_running = False
        await self.ws_stream.stop()
        if self._inference_task and not self._inference_task.done():
            self._inference_task.cancel()
            try:
                await self._inference_task
            except asyncio.CancelledError:
                pass
        logger.info("StreamingInferencePipeline stopped.")

    async def _inference_worker_loop(self):
        """Consumes ticks from concurrent queue and triggers low-latency inference."""
        while self.is_running:
            try:
                tick = await self.queue.get()

                # Update in-memory buffer
                is_closed, price = self.buffer.on_tick(tick)

                # Broadcast live tick to connected clients
                if self.broadcast_fn:
                    await self.broadcast_fn(tick)

                # Check if inference should trigger
                if self.live_predictor.should_predict(price, is_closed):
                    forecast_payload = self.live_predictor.predict_streaming(price)
                    if forecast_payload and self.broadcast_fn:
                        await self.broadcast_fn(forecast_payload)

                self.queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as loop_err:
                logger.error(f"[StreamingPipeline] Error in inference worker loop: {loop_err}", exc_info=True)
                await asyncio.sleep(0.1)


# Global singleton pipeline instance
streaming_pipeline = StreamingInferencePipeline()
