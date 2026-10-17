"""
WebSocket Connection Manager and Real-Time Push Gateway.
Broadcasts live Binance ticks and instantaneous model forecast updates to connected React clients.
"""
import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("btc_oracle.websocket")


class ConnectionManager:
    """
    Manages active frontend WebSocket sessions and dispatches push events:
    - Real-time price ticks (type: 'TICK')
    - Streaming forecast updates (type: 'FORECAST_UPDATE')
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accepts and registers incoming client WebSocket."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Frontend client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Removes disconnected client from active pool."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Frontend client disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any]):
        """Dispatches JSON payload concurrently to all connected clients."""
        if not self.active_connections:
            return

        payload = json.dumps(message)
        dead_connections: list[WebSocket] = []

        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


manager = ConnectionManager()


async def stream_price_feed(websocket: WebSocket, base_price: float = 81600.0):
    """
    Main WebSocket endpoint handler for React frontend clients.
    Immediately pushes the latest in-memory tick and prediction snapshot,
    then keeps the channel open for instant event-driven broadcasts.
    """
    from apps.api.src.live_inference import streaming_pipeline

    await manager.connect(websocket)

    try:
        # 1. Instantly push latest tick snapshot so frontend chart initializes immediately
        if streaming_pipeline.last_tick:
            await websocket.send_text(json.dumps(streaming_pipeline.last_tick))
        elif streaming_pipeline.buffer.candles:
            latest_bar = streaming_pipeline.buffer.candles[-1]
            await websocket.send_text(
                json.dumps({
                    "type": "TICK",
                    "symbol": "BTCUSDT",
                    "price": latest_bar["close"],
                    "volume": latest_bar["volume"],
                    "timestamp": latest_bar["timestamp"].isoformat(),
                })
            )

        # 2. Instantly push latest forecast state so frontend doesn't need to poll
        if streaming_pipeline.live_predictor.latest_forecast_payload:
            await websocket.send_text(
                json.dumps(streaming_pipeline.live_predictor.latest_forecast_payload)
            )

        # 3. Maintain connection loop, handling client pings or heartbeats
        while True:
            # Await client messages or ping/pong heartbeats
            data = await websocket.receive_text()
            # If client requests manual refresh or ping:
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "PONG"}))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"Client connection closed: {e}")
        manager.disconnect(websocket)


async def start_streaming_pipeline():
    """Initializes and starts the streaming inference pipeline with WebSocket broadcast."""
    from apps.api.src.live_inference import streaming_pipeline

    streaming_pipeline.broadcast_fn = manager.broadcast
    await streaming_pipeline.start()


async def stop_streaming_pipeline():
    """Stops the streaming inference pipeline gracefully."""
    from apps.api.src.live_inference import streaming_pipeline

    await streaming_pipeline.stop()

