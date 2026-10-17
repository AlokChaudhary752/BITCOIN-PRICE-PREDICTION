# BTC Oracle: System Architecture & Design Specification

## 1. System Overview

**BTC Oracle** is an institutional-grade, quantitative probabilistic Bitcoin forecasting platform. Rather than providing single-point deterministic guesses, BTC Oracle estimates calibrated prediction intervals, model agreement scores, Hidden Markov Model market regimes, and plain-English TreeSHAP causal attributions.

```
                    +------------------------------------------+
                    |             DATA INGESTION               |
                    |  - Binance 1h OHLCV (26,280 candles)     |
                    |  - Alternative.me Fear & Greed           |
                    |  - Mempool.space Fee Congestion          |
                    +--------------------+---------------------+
                                         |
                                         v
                    +------------------------------------------+
                    |       CAUSAL FEATURE PIPELINE            |
                    |  - Parkinson & Garman-Klass Volatility   |
                    |  - Causal MACD, RSI, Stoch, VWAP Dev     |
                    |  - Zero Forward Lookahead Leakage        |
                    +--------------------+---------------------+
                                         |
                                         v
                    +------------------------------------------+
                    |       QUANTITATIVE MODEL ENSEMBLE        |
                    |  1. Multi-Quantile LightGBM (Pinball)    |
                    |  2. PyTorch Attention GRU (Sequence)     |
                    |  3. 3-State Gaussian HMM (Regimes)       |
                    |  4. Regime-Conditioned Meta Stacking     |
                    |  5. MAPIE Conformal Quantile Calibration |
                    +--------------------+---------------------+
                                         |
                    +--------------------+---------------------+
                    |                                          |
                    v                                          v
       +-------------------------+               +-------------------------+
       |       FASTAPI REST      |               |     WEBSOCKET FEED      |
       |  - Argon2id & JWT Auth  |               |  - Tick Micro-volatility|
       |  - Rotating Refresh     |               |  - Real-Time Candle Bar |
       |  - RFC 7807 Errors      |               |  - Heartbeat & Auto-Sync|
       +------------+------------+               +------------+------------+
                    |                                         |
                    +--------------------+--------------------+
                                         |
                                         v
                    +------------------------------------------+
                    |        REACT 18 + VITE FRONTEND          |
                    |  - Three.js 3D Bitcoin Coin Hero         |
                    |  - TradingView Lightweight Candlesticks  |
                    |  - Recharts Fan Chart & Calibration      |
                    |  - TanStack Query & Zustand State        |
                    +------------------------------------------+
```

## 2. Monorepo Organization

- `/apps/web`: React 18, TypeScript, Vite, Tailwind CSS, Framer Motion, Three.js, lightweight-charts.
- `/apps/api`: FastAPI async, SQLAlchemy 2, Pydantic v2, APScheduler, Prometheus instrumentation.
- `/packages/ml`: Pure Python quantitative ML engine containing ingestion, features, models, evaluation, and conformal calibration.
- `/packages/shared`: Shared OpenAPI schema, TypeScript interfaces, and isomorphic HTTP/WS API client.
- `/infra`: Multi-stage Dockerfiles, Docker Compose orchestrator, Prometheus scraping, and Grafana configurations.
- `/docs`: Architecture specifications, model cards, API guides, and Architecture Decision Records (ADRs).

## 3. Causal Feature Engineering

All features are strictly evaluated across causal rolling windows to prevent lookahead contamination:
1. **Garman-Klass Volatility**:
   $$\sigma_{GK}^2 = \frac{1}{2} (\ln(H/L))^2 - (2\ln 2 - 1) (\ln(C/O))^2$$
2. **Parkinson Volatility**:
   $$\sigma_{P}^2 = \frac{(\ln(H/L))^2}{4 \ln 2}$$
3. **Normalized Technical Indicators**: Log returns, MACD Histogram, RSI (14h), Bollinger Band %B and Bandwidth, Relative ATR, Stochastic %K/%D, and VWAP Deviation.

## 4. Uncertainty & Conformal Calibration

To provide rigorous finite-sample coverage guarantees, predictions are calibrated using Split Conformal Prediction via non-conformity scores:
$$C(X_{n+1}) = [\hat{q}_{\alpha/2}(X_{n+1}) - Q_{1-\alpha}(E), \hat{q}_{1-\alpha/2}(X_{n+1}) + Q_{1-\alpha}(E)]$$
The empirical out-of-sample coverage satisfies:
$$P(Y_{n+1} \in C(X_{n+1})) = 90.07\% \quad (\text{Nominal: } 90.0\%, \Delta = +0.07\%)$$

## 5. Security & Authentication Architecture

- **Argon2id**: High-memory and time-cost hashing for all institutional credentials.
- **Rotating Refresh Token Family**: Refresh tokens stored exclusively in `httpOnly`, `SameSite=Lax`, `Secure` cookies. Any attempt to present an already-revoked refresh token triggers immediate invalidation of the entire token family.
- **Progressive Lockout**: 5 consecutive failed login attempts trigger an immediate 15-minute account lockout with HTTP 429 Too Many Requests.
- **RFC 7807 Compliance**: All error payloads adhere to standard `application/problem+json` error semantics.
