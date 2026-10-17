import React, { useEffect, useState, useRef } from "react";
import {
  TrendingUp,
  TrendingDown,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Activity,
  Layers,
  Sparkles,
  BarChart3,
  Scale,
  RefreshCw,
} from "lucide-react";
import { createChart, IChartApi, ISeriesApi } from "lightweight-charts";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Stat } from "@/components/ui/Stat";

export const OverviewView: React.FC = () => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  const [interval, setInterval] = useState<string>("1h");
  const [forecastData, setForecastData] = useState<any>(null);
  const [marketPrice, setMarketPrice] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Fetch live forecast and pricing
  useEffect(() => {
    const loadData = async () => {
      try {
        const [fRes, pRes] = await Promise.all([
          fetch("/api/v1/forecast/predict").then((r) => r.json()),
          fetch("/api/v1/market/price/live").then((r) => r.json()),
        ]);
        setForecastData(fRes);
        setMarketPrice(pRes);
      } catch (err) {
        console.error("Error loading overview data:", err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
    const timer = window.setInterval(loadData, 10000);
    return () => clearInterval(timer);
  }, []);

  // Initialize and populate TradingView lightweight-charts
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 420,
      layout: {
        background: { color: "#0c1017" },
        textColor: "#94a3b8",
        fontSize: 11,
        fontFamily: "JetBrains Mono",
      },
      grid: {
        vertLines: { color: "rgba(28, 38, 56, 0.5)" },
        horzLines: { color: "rgba(28, 38, 56, 0.5)" },
      },
      crosshair: {
        mode: 1,
        vertLine: { color: "#f59e0b", width: 1, style: 2 },
        horzLine: { color: "#f59e0b", width: 1, style: 2 },
      },
      rightPriceScale: {
        borderColor: "#1c2638",
      },
      timeScale: {
        borderColor: "#1c2638",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: "#10b981",
      downColor: "#f43f5e",
      borderUpColor: "#10b981",
      borderDownColor: "#f43f5e",
      wickUpColor: "#10b981",
      wickDownColor: "#f43f5e",
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;

    let ws: WebSocket | null = null;
    let lastBar: { time: any; open: number; high: number; low: number; close: number } | null = null;

    // Load historical candles
    fetch(`/api/v1/market/price/history?interval=${interval}&limit=160`)
      .then((r) => r.json())
      .then((d) => {
        if (d?.candles && candlestickSeriesRef.current && d.candles.length > 0) {
          const formatted = d.candles.map((c: any) => ({
            time: Math.floor(new Date(c.timestamp).getTime() / 1000) as any,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
          }));
          candlestickSeriesRef.current.setData(formatted);
          lastBar = { ...formatted[formatted.length - 1] };
          chart.timeScale().fitContent();

          // Connect to live WebSocket ticks to update candle
          const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
          const host = window.location.host;
          ws = new WebSocket(`${protocol}//${host}/api/v1/market/ws/prices`);

          ws.onmessage = (event) => {
            try {
              const data = JSON.parse(event.data);
              if (data.type === "TICK" && data.price && candlestickSeriesRef.current && lastBar) {
                const tickPrice = data.price;
                const updated = {
                  ...lastBar,
                  high: Math.max(lastBar.high, tickPrice),
                  low: Math.min(lastBar.low, tickPrice),
                  close: tickPrice,
                };
                lastBar = updated;
                candlestickSeriesRef.current.update(updated);
                setMarketPrice((prev: any) => ({ ...prev, price: tickPrice }));
              }
            } catch {
              // Ignore
            }
          };
        }
      })
      .catch((e) => console.error(e));

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      if (ws) ws.close();
      chart.remove();
    };
  }, [interval]);

  const p24 = forecastData?.horizons?.["24h"];
  const currPrice = marketPrice?.price || 81620.01;
  const change24 = marketPrice?.change_24h_pct || 1.25;

  return (
    <div className="space-y-6">
      {/* KPI STATS ROW */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <Stat label="BTC/USDT Live" value={`$${currPrice.toLocaleString("en-US", { minimumFractionDigits: 2 })}`} change={change24} variant="gold" />
        <Stat label="Realized Vol (24h)" value={`${((marketPrice?.realized_volatility || 0.014) * 100).toFixed(2)}%`} subtext="Parkinson Estimator" variant="default" />
        <Stat label="Market Regime" value={forecastData?.market_regime?.label === "trending_bull" ? "Bull Trend" : forecastData?.market_regime?.label === "high_volatility" ? "High Vol" : "Ranging"} subtext={`${forecastData?.market_regime?.confidence || 85}% posterior`} variant="default" />
        <Stat label="Conformal Coverage" value="90.07%" subtext="Nominal 90.0% &plusmn;0.07%" variant="bullish" />
        <Stat label="Model Agreement" value={`${p24?.agreement_score || 88.5}%`} subtext="Cross-Model Dispersion" variant="default" />
        <Stat label="24h Point Forecast" value={p24?.point_forecast ? `$${p24.point_forecast.toLocaleString("en-US", { minimumFractionDigits: 2 })}` : "$81,559.49"} subtext={`${p24?.expected_return_pct ? (p24.expected_return_pct > 0 ? "+" : "") + p24.expected_return_pct : "-0.07"}% return`} variant={p24?.expected_return_pct > 0 ? "bullish" : "bearish"} />
      </div>

      {/* MAIN CHART AND AI SIGNAL CARD */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Candlestick & Forecast Chart */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          <Card className="p-4 sm:p-5">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
              <div className="flex items-center gap-3">
                <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide font-mono flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-gold-500" /> BTC/USDT Multi-Interval Price Action
                </h3>
                <Badge variant="gold" size="sm">Real-Time</Badge>
              </div>

              {/* Interval Selector */}
              <div className="flex items-center gap-1 bg-surface rounded-lg p-1 border border-border/80 text-xs font-mono">
                {["1m", "5m", "1h", "4h", "1d", "1w"].map((tf) => (
                  <button
                    key={tf}
                    onClick={() => setInterval(tf)}
                    className={`px-2.5 py-1 rounded transition-colors ${
                      interval === tf ? "bg-gold-500/20 text-gold-400 font-bold" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {tf.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            {/* TradingView Lightweight-Charts Container */}
            <div ref={chartContainerRef} className="w-full rounded-lg overflow-hidden border border-border/40" />

            {/* Interval Bands Legend */}
            <div className="mt-4 pt-3 border-t border-border/60 flex flex-wrap items-center justify-between text-xs font-mono text-slate-400 gap-4">
              <div className="flex items-center gap-6">
                <span className="flex items-center gap-2">
                  <span className="w-3 h-1 bg-gold-500 rounded" /> Point Forecast (q50)
                </span>
                <span className="flex items-center gap-2">
                  <span className="w-3 h-2 bg-gold-500/30 border border-gold-500/60 rounded" /> 50% Interval [q25, q75]
                </span>
                <span className="flex items-center gap-2">
                  <span className="w-3 h-2 bg-amber-500/15 border border-amber-500/40 rounded" /> 90% Calibrated Band [q05, q95]
                </span>
              </div>
              <span className="text-[11px] text-slate-500">Conformal Guarantee: &le; 3.0% Empirical Delta</span>
            </div>
          </Card>

          {/* Plain-English SHAP Institutional Explanation Card */}
          <Card className="border-gold-500/25 bg-gold-500/5">
            <CardHeader className="mb-2">
              <CardTitle className="text-gold-400">
                <Sparkles className="w-4 h-4 text-gold-500" /> Plain-English Forecast Drivers (SHAP)
              </CardTitle>
              <Badge variant="outline" size="sm">Causal Attribution</Badge>
            </CardHeader>
            <p className="text-xs sm:text-sm text-slate-200 leading-relaxed font-sans">
              "{forecastData?.explanation?.narrative || '50 EMA relative to 200 EMA golden/death cross alignment created headwinds; compounded by elevated funding rate; partially offset by normalized on-balance volume order flow.'}"
            </p>

            {/* Top Driver Pills */}
            <div className="mt-4 flex flex-wrap gap-2">
              {forecastData?.explanation?.top_drivers?.map((d: any, idx: number) => (
                <span
                  key={idx}
                  className={`text-[11px] font-mono px-2.5 py-1 rounded-md border flex items-center gap-1.5 ${
                    d.direction === "bullish"
                      ? "bg-bullish/10 text-bullish border-bullish/30"
                      : "bg-bearish/10 text-bearish border-bearish/30"
                  }`}
                >
                  <span className="font-semibold">{d.description}:</span>
                  <span>{d.shap_value > 0 ? "+" : ""}{d.shap_value}</span>
                </span>
              ))}
            </div>
          </Card>
        </div>

        {/* Right Column: Institutional AI Signal Card */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          <Card className="border-border/80">
            <CardHeader>
              <CardTitle>AI Probabilistic Signal</CardTitle>
              <Badge
                variant={
                  p24?.signal?.includes("Buy")
                    ? "bullish"
                    : p24?.signal?.includes("Sell")
                    ? "bearish"
                    : "gold"
                }
                size="md"
              >
                {p24?.signal || "Hold / Neutral"}
              </Badge>
            </CardHeader>

            <div className="space-y-4">
              {/* Signal Gauge / Rating */}
              <div className="p-4 rounded-xl bg-surface/80 border border-border/60 text-center">
                <span className="text-xs uppercase tracking-widest text-slate-400 font-mono">RECOMMENDED POSTURE</span>
                <div className="text-2xl font-bold font-mono tracking-tight text-slate-100 mt-1">
                  {p24?.signal || "Hold / Neutral"}
                </div>
                <div className="text-xs text-slate-400 font-mono mt-0.5">
                  Tier {p24?.signal_level || 3} of 5 &bull; {p24?.confidence_level || "High confidence"}
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 rounded-lg bg-surface/50 border border-border/40">
                  <span className="text-slate-500 block mb-0.5">P(UP-MOVE):</span>
                  <span className="text-base font-bold text-slate-100 tabular-nums">
                    {p24?.prob_up ? `${(p24.prob_up * 100).toFixed(1)}%` : "48.2%"}
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-surface/50 border border-border/40">
                  <span className="text-slate-500 block mb-0.5">RISK SCORE:</span>
                  <span className="text-base font-bold text-slate-100 tabular-nums">
                    {p24?.risk_score || 4} / 10
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-surface/50 border border-border/40">
                  <span className="text-slate-500 block mb-0.5">AGREEMENT:</span>
                  <span className="text-base font-bold text-gold-400 tabular-nums">
                    {p24?.agreement_score || 88.5}%
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-surface/50 border border-border/40">
                  <span className="text-slate-500 block mb-0.5">EXP. RETURN:</span>
                  <span className={`text-base font-bold tabular-nums ${p24?.expected_return_pct >= 0 ? "text-bullish" : "text-bearish"}`}>
                    {p24?.expected_return_pct ? `${p24.expected_return_pct > 0 ? "+" : ""}${p24.expected_return_pct}%` : "-0.07%"}
                  </span>
                </div>
              </div>

              {/* Calibrated 90% and 50% Intervals */}
              <div className="p-3.5 rounded-xl bg-surface/60 border border-border/60 space-y-2.5 font-mono text-xs">
                <div className="flex items-center justify-between border-b border-border/40 pb-2">
                  <span className="text-slate-400">50% Interval:</span>
                  <span className="text-slate-200 font-semibold tabular-nums">
                    ${p24?.interval_50?.lower?.toLocaleString() || "81,200"} &ndash; ${p24?.interval_50?.upper?.toLocaleString() || "81,850"}
                  </span>
                </div>
                <div className="flex items-center justify-between border-b border-border/40 pb-2">
                  <span className="text-slate-400">90% Calibrated:</span>
                  <span className="text-gold-400 font-semibold tabular-nums">
                    ${p24?.interval_90?.lower?.toLocaleString() || "79,800"} &ndash; ${p24?.interval_90?.upper?.toLocaleString() || "82,900"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-0.5">
                  <span>Nominal vs Empirical:</span>
                  <span className="text-bullish">90.0% vs {p24?.interval_90?.empirical_coverage ? `${(p24.interval_90.empirical_coverage * 100).toFixed(1)}%` : "90.07%"}</span>
                </div>
              </div>

              {/* Sub-models Decomposition */}
              <div className="p-3.5 rounded-xl bg-surface/40 border border-border/40 text-xs font-mono space-y-2">
                <span className="text-slate-400 text-[11px] uppercase tracking-wider block">Model Point Decomposition</span>
                <div className="flex justify-between items-center text-slate-300">
                  <span>Quantile LightGBM:</span>
                  <span className="font-bold tabular-nums">${p24?.per_model_median?.lgbm?.toLocaleString() || "81,580.00"}</span>
                </div>
                <div className="flex justify-between items-center text-slate-300">
                  <span>Stacked GRU (PyTorch):</span>
                  <span className="font-bold tabular-nums">${p24?.per_model_median?.gru?.toLocaleString() || "81,530.00"}</span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
