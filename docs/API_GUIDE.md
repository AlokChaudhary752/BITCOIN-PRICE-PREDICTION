# BTC Oracle API Guide (v1)

## Overview
The BTC Oracle API is an asynchronous, institutional-grade REST and WebSocket interface built with FastAPI, Pydantic v2, and SQLAlchemy 2. All responses adhere to strict JSON schemas, and all error responses conform to the **RFC 7807 Problem Details** standard.

- **Base URL:** `http://localhost:8000/api/v1`
- **Interactive OpenAPI Documentation:** `http://localhost:8000/docs`
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`
- **Prometheus Metrics:** `http://localhost:8000/metrics`

---

## Authentication & Session Security

Authentication uses dual-token rotation with Argon2id password hashing:
1. **Access Token:** Short-lived JWT (15-minute expiration) passed via standard `Authorization: Bearer <access_token>` header.
2. **Refresh Token:** Long-lived rotating token stored securely in an `httpOnly`, `Secure`, `SameSite=Strict` cookie (`btc_oracle_refresh`).
3. **Token Family Reuse Detection:** Every refresh operation rotates the token family. If an already-spent refresh token is presented (indicating theft or token replay), the server immediately revokes the **entire token family**, logging a high-priority security audit event.
4. **Progressive Lockout:** After 5 consecutive failed login attempts, the account is locked for 15 minutes with HTTP 429 Too Many Requests.

### Endpoints
- `POST /api/v1/auth/register`: Register new account with $100,000 virtual paper portfolio.
- `POST /api/v1/auth/login`: Authenticate and obtain JWT access token and set refresh cookie.
- `POST /api/v1/auth/refresh`: Rotate refresh token and issue new access token.
- `POST /api/v1/auth/logout`: Invalidate current token family and clear auth cookies.
- `GET /api/v1/auth/me`: Retrieve authenticated user identity, role, and permissions.

---

## Market Data & WebSockets

### Real-Time Streaming Ticker
Connect to the high-throughput WebSocket ticker:
```
ws://localhost:8000/api/v1/market/ws/prices
```
**Sample Inbound Payload:**
```json
{
  "symbol": "BTCUSDT",
  "price": 81612.55,
  "volume_24h": 28491.4,
  "change_24h": -1.24,
  "high_24h": 83450.00,
  "low_24h": 80920.10,
  "timestamp": 1729108390.124
}
```

### Market REST Endpoints
- `GET /api/v1/market/live`: Returns current spot price, 24h volume, high/low, realized volatility, and dominance.
- `GET /api/v1/market/history?limit=100`: Returns historical OHLCV candles formatted for TradingView Lightweight Charts.
- `GET /api/v1/market/orderbook`: Returns live order book bids, asks, and depth imbalance ratio.
- `GET /api/v1/market/onchain`: Returns live mempool recommended fee rates (sat/vB), taker buy ratios, and block metrics.

---

## Machine Learning & Forecasts

### Forecast Endpoints
- `GET /api/v1/forecast/predict?horizon=24h`: Real-time multi-quantile probabilistic prediction (`q05`, `q25`, `q50`, `q75`, `q95`), P(Up), conformal prediction intervals, HMM regime state, model agreement score, and natural language SHAP explanation.
- `GET /api/v1/forecast/predict/all`: Returns bundled forecasts for all 5 horizons (`1h`, `4h`, `24h`, `7d`, `30d`).
- `GET /api/v1/forecast/models/performance`: Live out-of-sample accuracy vs Last-Price Persistence and EMA Baselines.
- `GET /api/v1/forecast/models/calibration`: Split-conformal empirical vs nominal coverage curves and reliability diagram bins.
- `GET /api/v1/forecast/models/explain`: Global TreeSHAP feature importance ranking and impact directions.
- `GET /api/v1/forecast/models/drift`: Population Stability Index (PSI) and Kolmogorov-Smirnov drift statistics on live feature distributions.

---

## Quantitative Backtesting Engine

### Walk-Forward Backtest Execution
`POST /api/v1/analysis/backtest`
```json
{
  "initial_capital": 100000.0,
  "fee_bps": 6.0,
  "slippage_bps": 4.0,
  "signal_threshold": 0.55,
  "stop_loss_pct": 0.03,
  "risk_per_trade_pct": 0.02
}
```
**Response Format:**
```json
{
  "total_trades": 84,
  "win_rate": 0.583,
  "profit_factor": 1.72,
  "sharpe_ratio": 1.48,
  "sortino_ratio": 2.15,
  "max_drawdown": 0.084,
  "final_equity": 128450.12,
  "cagr": 0.342,
  "equity_curve": [{"time": "2024-01-01", "equity": 100000.0, "benchmark": 100000.0}],
  "trades": [...]
}
```

---

## RFC 7807 Error Response Specification
All client and server errors return standardized problem descriptions:
```json
{
  "type": "https://errors.btcoracle.ai/rate-limit-exceeded",
  "title": "Too Many Requests",
  "status": 429,
  "detail": "Account locked: 5 consecutive failed attempts. Locked for 15 minutes.",
  "instance": "/api/v1/auth/login"
}
```
