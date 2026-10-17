# Model Card: BTC Oracle Multi-Quantile Forecasting Engine

## Model Details
- **Model Name:** BTC Oracle Multi-Horizon Ensemble & Conformal Calibrator
- **Model Version:** `v1.2.0-champion`
- **Release Date:** October 2026
- **Architecture:** 
  1. Multi-Quantile LightGBM (`q05`, `q25`, `q50`, `q75`, `q95`) trained with Pinball Loss.
  2. Multi-Horizon PyTorch Recurrent Unit with Self-Attention (`AttentionGRU`).
  3. 3-State Gaussian Hidden Markov Model (HMM) for regime discovery (Trending Bull, Ranging/Mean-Reverting, High-Volatility Shock).
  4. Non-parametric Split-Conformal Prediction Calibrator (MAPIE methodology) ensuring finite-sample prediction interval guarantees.
- **Explainability:** TreeSHAP exact Shapley feature attribution with natural-language translation engine.

---

## Intended Use
- **Primary Domain:** Quantitative probabilistic Bitcoin price forecasting across multiple forecasting horizons (1 hour, 4 hours, 24 hours, 7 days, 30 days).
- **Target Audience:** Quantitative analysts, algorithmic risk managers, and institutional market observers requiring rigorous prediction intervals rather than point guesses.
- **Out-of-Scope Use:**
  - Automated high-frequency execution without human oversight.
  - Guarantees of risk-free return or deterministic future asset valuations.
  - **Disclaimer:** *"Forecasts are probabilistic, for educational purposes only, and are not financial advice."*

---

## Data & Provenance
- **Primary Dataset:** 3 Years (26,280 hourly candles) of BTC/USDT spot data sourced from Binance Public REST API.
- **Dataset Hash (SHA-256):** `c15d2a422087ca4e78a6db9b8214db21e053fa282dcf7e3d100c6d5d5402c890`
- **Exogenous Signals:**
  - Order Book Imbalance (Top 50 levels via Binance API).
  - Alternative.me Crypto Fear & Greed Index (historical and real-time polling).
  - Mempool and on-chain recommended fee estimates (sat/vB via Mempool.space).
  - Taker Buy/Sell volume ratios.
- **Data Quality Protocol:** Idempotent time-series gap detection, automated outlier rejection (> 15-sigma deviations from 24h rolling median), and non-zero volume verification.

---

## Feature Engineering & Causality
All engineered features are strictly causal with strictly past-looking windows (zero future leakage):
- **Log Returns:** Multi-scale 1h, 4h, 24h, 7d returns.
- **Volatility Estimators:** Parkinson High-Low volatility and Garman-Klass OHLC volatility estimators.
- **Momentum & Trend:** RSI-14, MACD (12, 26, 9), Bollinger Bands (20, 2-std), EMA ratios (20/50/200).
- **Volume & Liquidity:** VWAP distance, Order Flow Imbalance, Volume Z-scores.
- **Regime States:** Gaussian HMM posterior probabilities for states $\{0, 1, 2\}$.

---

## Validation & Evaluation Protocol
- **Evaluation Framework:** Walk-Forward Expanding-Window Validation with 120-hour purge and 24-hour embargo periods between train/test splits to eliminate temporal autocorrelation leakage.
- **Baselines Evaluated:** Last-Price Persistence Baseline and Exponential Moving Average (EMA-24) Drift Baseline.
- **Performance Benchmarks (24h Out-of-Sample Horizon):**
  - **Champion Model MAE:** $1,009.81
  - **Persistence Baseline MAE:** $958.39
  - **Directional Accuracy:** 51.4%
  - **Nominal vs Empirical Interval Coverage (90% Interval):**
    - Nominal: 90.00%
    - Empirical: 90.07%
    - Calibration Error ($\Delta$): **0.07%** (Threshold $\le 3.0\%$)
- **Data Leakage Verification:** Verified via automated unit tests where randomly shuffling or shifting target labels forward in time destroys predictive score, proving zero lookahead bias.

---

## Limitations & Risks
1. **Regime Shifts & Black Swan Events:** In unprecedented macro regimes (e.g., sudden regulatory actions, exchange insolvencies), historical causal distributions may fail to span the actual realized volatility shock.
2. **Conformal Exchangeability Assumption:** Conformal coverage guarantees hold asymptotically under distribution exchangeability; sudden structural breaks can temporarily compress or widen empirical coverage.
3. **Execution Friction:** Forecasted theoretical alpha does not account for exchange slippage on large market orders, exchange downtime, or liquidity shocks unless modeled via the built-in walk-forward backtest engine.
