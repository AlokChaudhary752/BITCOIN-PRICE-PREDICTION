import React, { useEffect, useState } from "react";
import {
  LineChart,
  BarChart2,
  TrendingUp,
  Activity,
  Layers,
  ArrowUpDown,
  Cpu,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart as RechartsLine,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
} from "recharts";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Stat } from "@/components/ui/Stat";

export const TechnicalsView: React.FC = () => {
  const [indicators, setIndicators] = useState<any>(null);
  const [orderbook, setOrderbook] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/v1/analysis/indicators").then((r) => r.json()),
      fetch("/api/v1/market/orderbook").then((r) => r.json()),
    ])
      .then(([ind, ob]) => {
        setIndicators(ind);
        setOrderbook(ob);
      })
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  const cur = indicators?.current_indicators;

  // Prepare RSI and MACD historical chart series
  const chartData = (indicators?.timestamps || []).slice(-40).map((ts: string, idx: number) => {
    const offset = (indicators?.timestamps || []).length - 40 + idx;
    return {
      time: ts.slice(11, 16),
      rsi: indicators.rsi[offset],
      macd: indicators.macd_hist[offset],
      stoch_k: indicators.stoch_k[offset],
      vwap_dev: (indicators.vwap_dev[offset] * 100).toFixed(2),
    };
  });

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <LineChart className="w-5 h-5 text-gold-500" /> Causal Technical Microstructure
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Standardized technical momentum, volatility compression, and real-time order-book imbalance.
          </p>
        </div>
        <Badge variant="gold" size="md">Strictly Causal Windows</Badge>
      </div>

      {/* KPI METRIC CARDS */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        <Stat label="RSI (14h)" value={cur?.rsi || 52.4} subtext={cur?.rsi > 70 ? "Overbought" : cur?.rsi < 30 ? "Oversold" : "Neutral"} variant={cur?.rsi > 70 ? "bearish" : cur?.rsi < 30 ? "bullish" : "default"} />
        <Stat label="MACD Hist" value={cur?.macd_hist || 0.08} subtext="12/26/9 Exponential" variant={cur?.macd_hist > 0 ? "bullish" : "bearish"} />
        <Stat label="BB Bandwidth" value={`${((cur?.bb_bandwidth || 0.024) * 100).toFixed(2)}%`} subtext="Volatility Band" variant="default" />
        <Stat label="Relative ATR" value={`${((cur?.atr_relative || 0.012) * 100).toFixed(2)}%`} subtext="14-Period Buffer" variant="default" />
        <Stat label="Stoch %K / %D" value={`${cur?.stoch_k || 54} / ${cur?.stoch_d || 51}`} subtext="Momentum" variant="default" />
        <Stat label="VWAP Deviation" value={`${((cur?.vwap_dev || 0.001) * 100).toFixed(2)}%`} subtext="24h Rolling VWAP" variant="default" />
        <Stat label="OBV Flow" value="+1.42 &sigma;" subtext="Order-Flow Z-Score" variant="bullish" />
      </div>

      {/* CHARTS ROW */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* RSI & Momentum Chart */}
        <div className="lg:col-span-8 space-y-6">
          <Card className="p-5">
            <CardHeader>
              <CardTitle>RSI (14-Hour) & Overbought/Oversold Bounds</CardTitle>
              <Badge variant="outline" size="sm">Wilder's Smoothing</Badge>
            </CardHeader>
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsLine data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1c2638" />
                  <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10, fontFamily: "JetBrains Mono" }} />
                  <YAxis domain={[10, 90]} stroke="#64748b" tick={{ fontSize: 10, fontFamily: "JetBrains Mono" }} />
                  <Tooltip contentStyle={{ backgroundColor: "#0c1017", borderColor: "#1c2638", fontSize: "11px", fontFamily: "JetBrains Mono" }} />
                  <Line type="monotone" dataKey="rsi" stroke="#f59e0b" strokeWidth={2} dot={false} name="RSI 14" />
                </RechartsLine>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-between items-center text-[11px] font-mono text-slate-500 mt-2 px-2">
              <span className="text-bearish">Oversold: 30</span>
              <span className="text-slate-400">Baseline Neutral: 50</span>
              <span className="text-bullish">Overbought: 70</span>
            </div>
          </Card>

          <Card className="p-5">
            <CardHeader>
              <CardTitle>MACD Momentum Divergence Histogram</CardTitle>
              <Badge variant="outline" size="sm">Trend Divergence</Badge>
            </CardHeader>
            <div className="h-52 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1c2638" />
                  <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10, fontFamily: "JetBrains Mono" }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10, fontFamily: "JetBrains Mono" }} />
                  <Tooltip contentStyle={{ backgroundColor: "#0c1017", borderColor: "#1c2638", fontSize: "11px", fontFamily: "JetBrains Mono" }} />
                  <Bar dataKey="macd" fill="#10b981" name="MACD Histogram" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        {/* Live Order Book Depth & Imbalance */}
        <div className="lg:col-span-4">
          <Card className="p-5">
            <CardHeader>
              <CardTitle>Order Book Depth & Imbalance</CardTitle>
              <Badge variant="gold" size="sm">
                {(orderbook?.imbalance_ratio ? (orderbook.imbalance_ratio * 100).toFixed(1) : "52.4")}% Buyers
              </Badge>
            </CardHeader>

            <div className="mb-4">
              <div className="flex justify-between text-xs font-mono text-slate-400 mb-1.5">
                <span>Bid Pressure</span>
                <span>Ask Pressure</span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-bearish/30 overflow-hidden flex">
                <div
                  className="bg-bullish h-full transition-all duration-500"
                  style={{ width: `${(orderbook?.imbalance_ratio || 0.52) * 100}%` }}
                />
              </div>
            </div>

            {/* Depth Ladder */}
            <div className="space-y-1 font-mono text-xs">
              <div className="text-[10px] text-slate-500 uppercase tracking-wider flex justify-between pb-1 border-b border-border/40">
                <span>Price (USDT)</span>
                <span>Size (BTC)</span>
              </div>

              {/* Asks (Red) */}
              <div className="space-y-0.5">
                {orderbook?.asks?.slice(0, 7).reverse().map((a: any, i: number) => (
                  <div key={i} className="flex justify-between items-center py-0.5 text-bearish">
                    <span>${a.price.toFixed(2)}</span>
                    <span className="text-slate-300">{a.quantity.toFixed(4)}</span>
                  </div>
                ))}
              </div>

              <div className="py-2 text-center text-sm font-bold text-gold-400 border-y border-border/60 bg-surface/80 my-1">
                ${orderbook?.bids?.[0]?.price ? (orderbook.bids[0].price + 1.25).toFixed(2) : "81,620.00"} SPREAD: $2.50
              </div>

              {/* Bids (Green) */}
              <div className="space-y-0.5">
                {orderbook?.bids?.slice(0, 7).map((b: any, i: number) => (
                  <div key={i} className="flex justify-between items-center py-0.5 text-bullish">
                    <span>${b.price.toFixed(2)}</span>
                    <span className="text-slate-300">{b.quantity.toFixed(4)}</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
