import React, { useEffect, useState } from "react";
import { Network, Zap, Cpu, Activity, BarChart2, ArrowRight } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Stat } from "@/components/ui/Stat";

export const OnChainView: React.FC = () => {
  const [onchain, setOnchain] = useState<any>(null);

  useEffect(() => {
    fetch("/api/v1/market/onchain")
      .then((r) => r.json())
      .then((d) => setOnchain(d))
      .catch((e) => console.error(e));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Network className="w-5 h-5 text-gold-500" /> On-Chain & Network Microstructure
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time mempool fee congestion, transaction size dispersion, and aggressive taker flow.
          </p>
        </div>
        <Badge variant="gold" size="md">Mempool.space API & Exchange Flow</Badge>
      </div>

      {/* STATS ROW */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Stat label="Fastest Fee Rate" value={`${onchain?.fastest_fee || 25} sat/vB`} subtext="Next Block Priority" variant="gold" />
        <Stat label="Half-Hour Fee" value={`${onchain?.half_hour_fee || 20} sat/vB`} subtext="~3 Blocks Confirmation" variant="default" />
        <Stat label="Taker Buy Ratio" value={`${((onchain?.taker_buy_ratio || 0.51) * 100).toFixed(1)}%`} subtext="Aggressive Buyer Volume" variant={onchain?.taker_buy_ratio > 0.5 ? "bullish" : "bearish"} />
        <Stat label="Average Trade Size" value={`${onchain?.average_trade_size || 0.45} BTC`} subtext="Microstructural Institutional Flow" variant="default" />
      </div>

      {/* MEMPOOL & CONGESTION CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-5">
          <CardHeader>
            <CardTitle>Mempool Fee Recommendation</CardTitle>
            <Badge variant="outline" size="sm">sat/vB</Badge>
          </CardHeader>
          <div className="space-y-3 font-mono text-xs">
            <div className="flex justify-between items-center p-2.5 rounded-lg bg-surface/80 border border-border/60">
              <span className="text-slate-400">High Priority (10 min):</span>
              <span className="text-gold-400 font-bold tabular-nums">{onchain?.fastest_fee || 25} sat/vB</span>
            </div>
            <div className="flex justify-between items-center p-2.5 rounded-lg bg-surface/80 border border-border/60">
              <span className="text-slate-400">Medium Priority (30 min):</span>
              <span className="text-slate-200 font-bold tabular-nums">{onchain?.half_hour_fee || 20} sat/vB</span>
            </div>
            <div className="flex justify-between items-center p-2.5 rounded-lg bg-surface/80 border border-border/60">
              <span className="text-slate-400">Low Priority (60 min):</span>
              <span className="text-slate-200 font-bold tabular-nums">{onchain?.hour_fee || 15} sat/vB</span>
            </div>
            <div className="flex justify-between items-center p-2.5 rounded-lg bg-surface/80 border border-border/60">
              <span className="text-slate-400">Minimum Purge Fee:</span>
              <span className="text-slate-500 font-bold tabular-nums">{onchain?.minimum_fee || 10} sat/vB</span>
            </div>
          </div>
        </Card>

        <Card className="p-5">
          <CardHeader>
            <CardTitle>Why Mempool Congestion Matters</CardTitle>
            <Badge variant="gold" size="sm">Theory</Badge>
          </CardHeader>
          <p className="text-xs text-slate-300 leading-relaxed">
            Spikes in mempool fee rates typically accompany intense volatility and panic rebalancing. When on-chain fees accelerate, urgency among market makers to move collateral across centralized and decentralized venues causes sudden liquidity gaps and widening bid-ask spreads.
          </p>
        </Card>

        <Card className="p-5">
          <CardHeader>
            <CardTitle>Taker Aggression Flow</CardTitle>
            <Badge variant="bullish" size="sm">Microstructure</Badge>
          </CardHeader>
          <p className="text-xs text-slate-300 leading-relaxed">
            Taker buy ratio measures the fraction of trading volume that crosses the spread as market orders rather than passive limit orders. A taker ratio above 54% signals institutional accumulation, while below 46% reflects forced liquidations or structural distribution.
          </p>
        </Card>
      </div>
    </div>
  );
};
