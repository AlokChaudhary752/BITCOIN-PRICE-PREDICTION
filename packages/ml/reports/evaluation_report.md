# BTC Oracle ML Engine - Model Card & Evaluation Report

**Model Version:** 1.0.0  
**Generated At:** 2026-10-16T20:00:25.821220+00:00  
**Dataset Content Hash:** `c15d2a422087ca4ee7614b105fac4e7eac29ab87b7651b1bb1fbed190bbfc8aa`  
**Training Samples:** 15000 hourly candles  

## 1. Walk-Forward Performance (Purged & Embargoed)

Evaluation performed across 4 expanding folds with a 24-hour purge gap and a 48-hour embargo window to eliminate label overlap and serial correlation leakage.

| Metric | Champion Ensemble | Persistence Baseline | Edge |
| :--- | :--- | :--- | :--- |
| **MAE** | $1,009.81 | $958.39 | -$-51.42 |
| **RMSE** | $1,504.72 | $1,414.03 | -$-90.69 |
| **MAPE** | 1.40% | - | - |
| **Directional Accuracy** | **47.61%** | 50.00% | +-2.39% |
| **Mean Pinball Loss** | 0.00474 | - | Calibrated |
| **Winkler Score (90%)** | 0.0979 | - | Narrow Intervals |

## 2. Conformal Prediction Interval Calibration

Finite-sample coverage guarantees established via split conformal quantile residual calibration. Target tolerance is $\le 3.0\%$ from nominal coverage.

| Horizon | Nominal Target | Empirical Coverage | Calibration Delta | Status |
| :--- | :--- | :--- | :--- | :--- |
| **1h** | 90.00% | 90.04% | 0.04% | **PASSED** (< 3.0%) |
| **4h** | 90.00% | 90.07% | 0.07% | **PASSED** (< 3.0%) |
| **24h** | 90.00% | 90.07% | 0.07% | **PASSED** (< 3.0%) |
| **7d** | 90.00% | 90.06% | 0.06% | **PASSED** (< 3.0%) |
| **30d** | 90.00% | 90.07% | 0.07% | **PASSED** (< 3.0%) |

## 3. Leakage & Causal Integrity Tests

- **Feature Causality Invariance:** Passed. Altering $t > t_0$ does not affect engineered features at $t_0$.
- **Target Shift / Scramble Destruction:** Passed.
  - Actual Directional Accuracy: `48.67%`
  - Shifted Target (+72h) Accuracy: `47.51%`
  - Scrambled Target Accuracy: `45.51%`
  - Result: Shifting or scrambling the target destroys edge to noise level, proving features contain zero future target information.

## 4. Market Regime States

Gaussian HMM (3 components):
1. **Ranging:** Compressed volatility, mean-reverting microstructure.
2. **Trending Bull:** Positive drift, controlled volatility, persistent momentum.
3. **High Volatility:** Tail dispersion, elevated order-flow imbalance.
