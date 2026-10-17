"""
WebSocket Connection Manager and Live Price Broadcast.
Streams real-time Bitcoin price ticks and candlestick updates to connected web clients.
"""
import asyncio
import json
from datetime import UTC, datetime

import numpy as np
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


manager = ConnectionManager()


async def stream_price_feed(websocket: WebSocket, base_price: float = 81600.0):
    """Simulates live tick volatility around current real market price."""
    await manager.connect(websocket)
    price = base_price
    try:
        while True:
            # Random micro-fluctuation (+/- 0.05%)
            delta = float(np.random.normal(0, price * 0.0003))
            price = round(price + delta, 2)
            tick_msg = {
                "type": "TICK",
                "symbol": "BTCUSDT",
                "price": price,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            await websocket.send_text(json.dumps(tick_msg))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
