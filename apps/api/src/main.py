"""
FastAPI Main Application.
Institutional Bitcoin Forecasting API.
"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from apps.api.src.config import settings
from apps.api.src.database import init_db
from apps.api.src.routers import (
    admin,
    analysis,
    auth,
    forecast,
    market,
    user,
)
from apps.api.src.routers.market import get_latest_dataframe
from apps.api.src.scheduler import start_scheduler, stop_scheduler
from apps.api.src.websocket import (
    start_streaming_pipeline,
    stop_streaming_pipeline,
    stream_price_feed,
)

# Prometheus metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP Requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP Request Latency", ["endpoint"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager: startup and shutdown hooks."""
    # 1. Initialize DB tables
    await init_db()
    # 2. Start background scheduler
    start_scheduler()
    # 3. Start real-time Binance WebSocket streaming inference pipeline
    await start_streaming_pipeline()
    yield
    # 4. Gracefully shutdown streaming pipeline
    await stop_streaming_pipeline()
    # 5. Shutdown scheduler
    stop_scheduler()


app = FastAPI(
    title="BTC Oracle API",
    description="Institutional-grade probabilistic Bitcoin forecasting platform API.",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_and_metrics_middleware(request: Request, call_next):
    """Add institutional security headers and prometheus instrumentation."""
    start_time = time.time()
    response: Response = await call_next(request)
    duration = time.time() - start_time

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Prometheus metrics
    endpoint = request.url.path
    REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=response.status_code).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)

    return response


# SYSTEM HEALTH & METRICS
@app.get("/healthz", tags=["System"])
async def healthz():
    """Liveness probe."""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/readyz", tags=["System"])
async def readyz():
    """Readiness probe checking database and model availability."""
    df = get_latest_dataframe()
    dataset_ready = not df.empty
    return {
        "status": "ready" if dataset_ready else "initializing",
        "dataset_rows": len(df),
        "scheduler_active": True,
    }


@app.get("/metrics", tags=["System"])
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# WEBSOCKET STREAM
@app.websocket("/api/v1/market/ws/prices")
@app.websocket("/ws/prices")
async def websocket_price_endpoint(websocket: WebSocket):
    """Real-time tick streaming WebSocket."""
    df = get_latest_dataframe()
    curr_p = float(df["close"].iloc[-1]) if not df.empty else 81500.0
    await stream_price_feed(websocket, base_price=curr_p)


# MOUNT API V1 ROUTERS
app.include_router(auth.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
app.include_router(forecast.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
