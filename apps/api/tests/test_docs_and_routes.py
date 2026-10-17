"""
Documentation and OpenAPI Specification Tests.
Acceptance Check: /docs lists every route.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_docs_and_openapi_routes(client: AsyncClient):
    # 1. /docs responds with 200 OK
    docs_resp = await client.get("/docs")
    assert docs_resp.status_code == 200
    assert "swagger" in docs_resp.text.lower() or "html" in docs_resp.text.lower()

    # 2. /openapi.json lists every required route
    spec_resp = await client.get("/openapi.json")
    assert spec_resp.status_code == 200
    spec = spec_resp.json()
    paths = spec["paths"]

    required_routes = [
        # Auth
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/auth/me",
        "/api/v1/auth/2fa/setup",
        "/api/v1/auth/2fa/verify",
        # Market
        "/api/v1/market/price/live",
        "/api/v1/market/price/history",
        "/api/v1/market/orderbook",
        "/api/v1/market/onchain",
        # Forecast
        "/api/v1/forecast/predict",
        "/api/v1/forecast/predict/all",
        "/api/v1/forecast/predictions/history",
        "/api/v1/forecast/models/performance",
        "/api/v1/forecast/models/calibration",
        "/api/v1/forecast/models/explain",
        "/api/v1/forecast/models/drift",
        "/api/v1/forecast/regime",
        # Analysis
        "/api/v1/analysis/indicators",
        "/api/v1/analysis/sentiment",
        "/api/v1/analysis/backtest",
        # User
        "/api/v1/user/alerts",
        "/api/v1/user/portfolio",
        "/api/v1/user/portfolio/trade",
        # Admin
        "/api/v1/admin/retrain",
        "/api/v1/admin/promote",
        "/api/v1/admin/model-registry",
        "/api/v1/admin/audit-log",
        # System
        "/healthz",
        "/readyz",
        "/metrics",
    ]

    for route in required_routes:
        assert route in paths, f"Missing route in OpenAPI specification: {route}"

    print(f"\n[OK] All {len(required_routes)} required routes verified in OpenAPI schema /docs.")
