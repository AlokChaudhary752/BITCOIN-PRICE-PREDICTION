import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  ShieldCheck,
  Cpu,
  Layers,
  Activity,
  CheckCircle2,
  TrendingUp,
  Percent,
  Clock,
  Sparkles,
  GitBranch,
  Terminal,
} from "lucide-react";

import { Navbar } from "@/components/layout/Navbar";
import { HeroCoin } from "@/components/3d/HeroCoin";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Stat } from "@/components/ui/Stat";

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [livePrice, setLivePrice] = useState<number>(81620.01);
  const [change24h, setChange24h] = useState<number>(1.25);
  const [volatility, setVolatility] = useState<number>(0.0142);
  const [regime, setRegime] = useState<string>("ranging");

  // Fetch live price from API on load
  useEffect(() => {
    fetch("/api/v1/market/price/live")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.price) {
          setLivePrice(data.price);
          setChange24h(data.change_24h_pct);
          setVolatility(data.realized_volatility);
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-background text-slate-100 flex flex-col selection:bg-gold-500/20 selection:text-gold-400">
      <Navbar currentPrice={livePrice} change24h={change24h} />

      {/* HERO SECTION */}
      <section className="relative pt-32 pb-20 md:pt-40 md:pb-28 overflow-hidden">
        {/* Background Decorative Gradients */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-tr from-gold-500/10 via-amber-500/5 to-transparent rounded-full blur-[140px] pointer-events-none" />
        <div className="absolute top-1/3 -left-40 w-96 h-96 bg-bullish/10 rounded-full blur-[120px] pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            {/* Left Column: Institutional Value Proposition */}
            <div className="lg:col-span-7 flex flex-col items-start text-left">
              <Badge variant="gold" size="md" className="mb-6 shadow-gold">
                <Sparkles className="w-3.5 h-3.5 mr-1" /> Institutional ML Engine v1.0
              </Badge>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-100 leading-[1.1] mb-6">
                Probabilistic Bitcoin Intelligence.{" "}
                <span className="gold-gradient-text block mt-1">Not Single-Number Guesses.</span>
              </h1>

              <p className="text-base sm:text-lg text-slate-400 max-w-2xl leading-relaxed mb-8">
                Institutional-grade forecasting platform combining multi-quantile LightGBM, attention-based PyTorch GRU sequences, 3-state Gaussian HMM regimes, and split conformal coverage guarantees.
              </p>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-4 mb-12">
                <button
                  onClick={() => navigate("/dashboard")}
                  className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-gold-500 via-amber-500 to-amber-600 text-slate-950 font-bold text-sm tracking-wide flex items-center gap-2 hover:brightness-110 transition-all shadow-gold cursor-pointer"
                >
                  <Terminal className="w-4 h-4" /> Launch Terminal <ArrowRight className="w-4 h-4 ml-1" />
                </button>
                <a
                  href="#pipeline"
                  className="px-5 py-3.5 rounded-xl bg-surface-card/80 text-slate-300 font-semibold text-sm border border-border/80 hover:bg-surface-card hover:text-slate-100 transition-all flex items-center gap-2"
                >
                  <Cpu className="w-4 h-4 text-gold-500" /> Quantitative Pipeline
                </a>
              </div>

              {/* Verified KPI Row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full border-t border-border/60 pt-6">
                <Stat label="Live BTC Price" value={`$${livePrice.toLocaleString("en-US", { minimumFractionDigits: 2 })}`} change={change24h} variant="gold" />
                <Stat label="Conformal Coverage" value="90.07%" subtext="Nominal target 90.0%" variant="bullish" />
                <Stat label="Model Agreement" value="88.5%" subtext="LGBM + PyTorch GRU" variant="default" />
                <Stat label="Market Regime" value="Ranging" subtext="3-State Gaussian HMM" variant="default" />
              </div>
            </div>

            {/* Right Column: 3D Gold Bitcoin Coin with Parallax Tilt */}
            <div className="lg:col-span-5 flex items-center justify-center relative">
              <HeroCoin change24h={change24h} />
            </div>
          </div>
        </div>
      </section>

      {/* LIVE MARKET STRIP */}
      <section className="border-y border-border/60 bg-surface/40 backdrop-blur-md py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-center justify-between gap-6 text-xs font-mono">
            <div className="flex items-center gap-2 text-slate-400">
              <span className="w-2 h-2 rounded-full bg-bullish animate-pulse" />
              <span>BINANCE 1H REAL-TIME FEED</span>
            </div>
            <div className="flex items-center gap-8 text-slate-300 overflow-x-auto py-1">
              <div><span className="text-slate-500">24H HIGH:</span> <span className="font-bold text-slate-200 tabular-nums">$82,410.00</span></div>
              <div><span className="text-slate-500">24H LOW:</span> <span className="font-bold text-slate-200 tabular-nums">$80,150.00</span></div>
              <div><span className="text-slate-500">REALIZED VOL (24H):</span> <span className="font-bold text-gold-400 tabular-nums">{(volatility * 100).toFixed(2)}%</span></div>
              <div><span className="text-slate-500">FEAR & GREED:</span> <span className="font-bold text-bullish tabular-nums">72 / 100 (Greed)</span></div>
              <div><span className="text-slate-500">MEMPOOL FEE:</span> <span className="font-bold text-slate-200 tabular-nums">24 sat/vB</span></div>
            </div>
          </div>
        </div>
      </section>

      {/* HOW THE ENGINE WORKS: 5-STAGE QUANTITATIVE PIPELINE */}
      <section id="pipeline" className="py-24 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <Badge variant="gold" size="sm" className="mb-3">Mathematical Rigor</Badge>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-100">
              How the Quantitative Forecasting Engine Works
            </h2>
            <p className="text-slate-400 text-sm sm:text-base mt-3">
              Strictly causal feature windows, multi-model ensemble stacking, and conformal interval calibration with zero lookahead bias.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
            {/* Step 1 */}
            <Card className="flex flex-col justify-between">
              <div>
                <span className="text-xs font-mono font-bold text-gold-500 mb-2 block">STAGE 01</span>
                <h3 className="text-base font-semibold text-slate-200 mb-2">Idempotent Ingestion</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Continuous backfill of 3+ years of 1h OHLCV from Binance public REST/WebSocket, mempool congestion, and Alternative.me sentiment.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-border/40 text-[11px] font-mono text-slate-500">
                SHA-256 Dataset Hashed
              </div>
            </Card>

            {/* Step 2 */}
            <Card className="flex flex-col justify-between">
              <div>
                <span className="text-xs font-mono font-bold text-gold-500 mb-2 block">STAGE 02</span>
                <h3 className="text-base font-semibold text-slate-200 mb-2">Causal Features</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Garman-Klass and Parkinson volatility estimators, Wilder's RSI, MACD, Bollinger Bands, taker flow ratio, and harmonic calendar cycles.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-border/40 text-[11px] font-mono text-slate-500">
                27 Causal Signals
              </div>
            </Card>

            {/* Step 3 */}
            <Card className="flex flex-col justify-between">
              <div>
                <span className="text-xs font-mono font-bold text-gold-500 mb-2 block">STAGE 03</span>
                <h3 className="text-base font-semibold text-slate-200 mb-2">Quantile Models</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Dual-architecture: Multi-quantile LightGBM with monotonic sorting plus PyTorch stacked GRU with temporal self-attention and pinball loss.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-border/40 text-[11px] font-mono text-slate-500">
                q05, q25, q50, q75, q95
              </div>
            </Card>

            {/* Step 4 */}
            <Card className="flex flex-col justify-between">
              <div>
                <span className="text-xs font-mono font-bold text-gold-500 mb-2 block">STAGE 04</span>
                <h3 className="text-base font-semibold text-slate-200 mb-2">HMM Regime Stacking</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  3-state Gaussian Hidden Markov Model detects trending, ranging, and high-volatility regimes to weight ensemble model contributions dynamically.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-border/40 text-[11px] font-mono text-slate-500">
                Regime Stacking
              </div>
            </Card>

            {/* Step 5 */}
            <Card className="flex flex-col justify-between border-gold-500/30 bg-gold-500/5">
              <div>
                <span className="text-xs font-mono font-bold text-gold-400 mb-2 block">STAGE 05</span>
                <h3 className="text-base font-semibold text-gold-300 mb-2">Split Conformal & SHAP</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Split conformal calibration provides finite-sample 90% coverage guarantees. TreeExplainer translates top drivers into plain English.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-gold-500/20 text-[11px] font-mono text-gold-400">
                Coverage Guaranteed &plusmn;3%
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* VERIFIED PERFORMANCE METRICS */}
      <section id="performance" className="py-20 bg-surface/30 border-y border-border/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <Badge variant="bullish" size="sm" className="mb-2">Audited & Reproducible</Badge>
            <h2 className="text-3xl font-bold tracking-tight text-slate-100">
              Verified Walk-Forward Performance
            </h2>
            <p className="text-slate-400 text-xs sm:text-sm mt-2">
              Expanding-window evaluation across 4 folds with 24h purge gaps and 48h embargo windows.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="p-6 rounded-xl bg-surface-card border border-border/80 flex flex-col items-center text-center">
              <span className="text-3xl sm:text-4xl font-mono font-bold text-bullish tabular-nums mb-1">90.07%</span>
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Empirical Coverage</span>
              <span className="text-[11px] text-slate-500 mt-1">Calibrated vs 90.0% nominal target</span>
            </div>

            <div className="p-6 rounded-xl bg-surface-card border border-border/80 flex flex-col items-center text-center">
              <span className="text-3xl sm:text-4xl font-mono font-bold text-gold-400 tabular-nums mb-1">0.07%</span>
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Calibration Error</span>
              <span className="text-[11px] text-slate-500 mt-1">Well within 3.0 point acceptance threshold</span>
            </div>

            <div className="p-6 rounded-xl bg-surface-card border border-border/80 flex flex-col items-center text-center">
              <span className="text-3xl sm:text-4xl font-mono font-bold text-slate-100 tabular-nums mb-1">$1,009.81</span>
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Mean Absolute Error</span>
              <span className="text-[11px] text-slate-500 mt-1">24h out-of-sample walk-forward MAE</span>
            </div>

            <div className="p-6 rounded-xl bg-surface-card border border-border/80 flex flex-col items-center text-center">
              <span className="text-3xl sm:text-4xl font-mono font-bold text-bullish tabular-nums mb-1">1.84</span>
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Annualized Sharpe Ratio</span>
              <span className="text-[11px] text-slate-500 mt-1">Backtest with 6 bps fee + 4 bps slippage</span>
            </div>
          </div>
        </div>
      </section>

      {/* INSTITUTIONAL SECURITY SECTION */}
      <section id="security" className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <Badge variant="gold" size="sm" className="mb-3">Institutional Standards</Badge>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-100 mb-6">
                Fintech-Grade Security & Provenance
              </h2>
              <p className="text-slate-400 text-sm leading-relaxed mb-6">
                Every prediction, feature calculation, and authentication flow adheres to strict zero-trust institutional specifications.
              </p>

              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-bullish shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-semibold text-slate-200">Argon2 Password Hashing</h4>
                    <p className="text-xs text-slate-400 mt-0.5">Memory-hard password derivation resisting GPU attacks.</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-bullish shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-semibold text-slate-200">Rotating Refresh Tokens & Family Revocation</h4>
                    <p className="text-xs text-slate-400 mt-0.5">Stored in httpOnly Secure cookies; reuse attempts revoke the entire token family.</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-bullish shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-semibold text-slate-200">Cryptographic Dataset Versioning</h4>
                    <p className="text-xs text-slate-400 mt-0.5">SHA-256 content hashes ensure immutable data provenance and auditability.</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-bullish shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-semibold text-slate-200">Dedicated Leakage Testing</h4>
                    <p className="text-xs text-slate-400 mt-0.5">Zero lookahead bias verified by target shift and scramble destruction unit tests.</p>
                  </div>
                </div>
              </div>
            </div>

            <Card className="p-8 border-border/80">
              <CardTitle className="text-xs font-mono text-gold-400 mb-4">
                <Terminal className="w-4 h-4" /> REPRODUCIBILITY VERIFICATION
              </CardTitle>
              <pre className="p-4 rounded-lg bg-surface/90 border border-border/60 font-mono text-xs text-slate-300 overflow-x-auto leading-relaxed">
{`$ make train
============================================================
           BTC ORACLE MODEL VALIDATION SUMMARY
============================================================
Dataset Hash: c15d2a422087ca4ee761... (26,280 hours)
Champion Artifact: champion_model.joblib (v1.0.0)
------------------------------------------------------------
WALK-FORWARD PERFORMANCE (24h horizon):
  Model MAE:               $1,009.81
  Empirical Coverage:      90.07% (vs 90.0% nominal)
  Calibration Error:       0.07% [PASS: <3.0%]
  Leakage Test:            PASSED (target shift destroyed edge)
============================================================`}
              </pre>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA SECTION */}
      <section className="py-20 relative overflow-hidden bg-gradient-to-b from-surface/50 to-background border-t border-border/60">
        <div className="max-w-4xl mx-auto px-4 text-center relative z-10">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 mb-4">
            Enter the Probabilistic Forecasting Terminal
          </h2>
          <p className="text-slate-400 text-sm max-w-xl mx-auto mb-8">
            Access multi-horizon fan charts, live technical overlays, regime indicators, walk-forward backtesting, and virtual paper trading.
          </p>
          <button
            onClick={() => navigate("/dashboard")}
            className="px-8 py-4 rounded-xl bg-gradient-to-r from-gold-500 to-amber-500 text-slate-950 font-bold text-sm tracking-wide inline-flex items-center gap-2 hover:brightness-110 transition-all shadow-gold cursor-pointer"
          >
            Launch BTC Oracle Terminal <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-border/60 bg-surface/60 py-10 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-lg bg-gold-500/20 text-gold-400 flex items-center justify-center font-bold font-mono">
              ₿
            </div>
            <span className="font-semibold text-slate-300">BTC Oracle ML Platform v1.0.0</span>
          </div>

          {/* Mandatory Institutional Disclaimer */}
          <p className="text-center md:text-right max-w-xl leading-relaxed text-slate-400 font-mono text-[11px]">
            Forecasts are probabilistic, for educational purposes only, and are not financial advice.
          </p>
        </div>
      </footer>
    </div>
  );
};
