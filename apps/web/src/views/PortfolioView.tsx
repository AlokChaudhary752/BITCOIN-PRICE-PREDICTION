import React, { useEffect, useState } from "react";
import { Briefcase, ArrowUpRight, ArrowDownRight, DollarSign, Wallet, ArrowRight } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Stat } from "@/components/ui/Stat";
import { useAuthStore } from "@/stores/authStore";

export const PortfolioView: React.FC = () => {
  const { accessToken } = useAuthStore();
  const [portfolio, setPortfolio] = useState<any>(null);
  const [tradeSide, setTradeSide] = useState<"BUY" | "SELL">("BUY");
  const [amount, setAmount] = useState<string>("0.1");
  const [tradeMsg, setTradeMsg] = useState<string | null>(null);

  const fetchPortfolio = async () => {
    try {
      const headers: Record<string, string> = {};
      if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
      const res = await fetch("/api/v1/user/portfolio", { headers, credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setPortfolio(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchPortfolio();
  }, [accessToken]);

  const handleTrade = async (e: React.FormEvent) => {
    e.preventDefault();
    setTradeMsg(null);
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
      const res = await fetch("/api/v1/user/portfolio/trade", {
        method: "POST",
        headers,
        credentials: "include",
        body: JSON.stringify({
          side: tradeSide,
          amount: parseFloat(amount),
        }),
      });
      if (res.ok) {
        const t = await res.json();
        setTradeMsg(`Executed ${t.side} ${t.amount} BTC @ $${t.price.toLocaleString()}`);
        fetchPortfolio();
      } else {
        const err = await res.json();
        setTradeMsg(`Failed: ${err.detail}`);
      }
    } catch (err: any) {
      setTradeMsg(`Error: ${err.message}`);
    }
  };

  const p = portfolio;
  const currPrice = p?.current_btc_price || 81620.01;
  const totEq = p?.total_equity || 100000;
  const initialCap = p?.initial_capital || 100000;
  const totRet = ((totEq - initialCap) / initialCap) * 100;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-gold-500" /> Virtual Paper Trading Portfolio
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Simulate allocation following probabilistic model signals with zero real capital risk.
          </p>
        </div>
        <Badge variant="gold" size="md">Live Simulated Execution</Badge>
      </div>

      {tradeMsg && (
        <div className="p-3 rounded-lg bg-surface-card border border-gold-500/30 text-gold-400 text-xs font-mono">
          {tradeMsg}
        </div>
      )}

      {/* METRIC CARDS */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Stat label="Total Net Equity" value={`$${totEq.toLocaleString("en-US", { minimumFractionDigits: 2 })}`} change={totRet} variant="gold" />
        <Stat label="Available Cash" value={`$${(p?.cash || 100000).toLocaleString("en-US", { minimumFractionDigits: 2 })}`} subtext="USD Liquidity" variant="default" />
        <Stat label="BTC Position" value={`${(p?.btc_balance || 0).toFixed(4)} BTC`} subtext={`Value: $${((p?.btc_balance || 0) * currPrice).toLocaleString()}`} variant="default" />
        <Stat label="Unrealized P&L" value={`$${(p?.unrealized_pnl || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}`} variant={p?.unrealized_pnl >= 0 ? "bullish" : "bearish"} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* EXECUTE ORDER FORM */}
        <div className="lg:col-span-5">
          <Card className="p-5">
            <CardHeader>
              <CardTitle>Execute Paper Order</CardTitle>
              <span className="text-xs font-mono text-slate-400">Market Price: ${currPrice.toLocaleString()}</span>
            </CardHeader>

            <form onSubmit={handleTrade} className="space-y-4 font-mono text-xs">
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setTradeSide("BUY")}
                  className={`py-2 rounded-lg font-bold transition-all ${
                    tradeSide === "BUY" ? "bg-bullish text-slate-950 shadow-emerald" : "bg-surface border border-border text-slate-400"
                  }`}
                >
                  BUY BTC
                </button>
                <button
                  type="button"
                  onClick={() => setTradeSide("SELL")}
                  className={`py-2 rounded-lg font-bold transition-all ${
                    tradeSide === "SELL" ? "bg-bearish text-slate-100 shadow-rose" : "bg-surface border border-border text-slate-400"
                  }`}
                >
                  SELL BTC
                </button>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Order Quantity (BTC)</label>
                <input
                  type="number"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-surface border border-border/80 text-slate-100 focus:outline-none"
                />
              </div>

              <div className="p-3 rounded-lg bg-surface/70 border border-border/50 text-[11px] space-y-1 text-slate-400">
                <div className="flex justify-between">
                  <span>Estimated Value:</span>
                  <span className="text-slate-200 font-semibold">${(parseFloat(amount || "0") * currPrice).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between">
                  <span>Est. Fee (6 bps):</span>
                  <span className="text-slate-200 font-semibold">${(parseFloat(amount || "0") * currPrice * 0.0006).toFixed(2)}</span>
                </div>
              </div>

              <button
                type="submit"
                className={`w-full py-2.5 rounded-lg font-bold text-xs tracking-wide transition-all ${
                  tradeSide === "BUY" ? "bg-bullish text-slate-950 hover:brightness-110" : "bg-bearish text-slate-100 hover:brightness-110"
                }`}
              >
                Place {tradeSide} Market Order
              </button>
            </form>
          </Card>
        </div>

        {/* TRADE HISTORY TABLE */}
        <div className="lg:col-span-7">
          <Card className="p-5">
            <CardHeader>
              <CardTitle>Recent Portfolio Fills</CardTitle>
              <span className="text-xs font-mono text-slate-400">{p?.recent_trades?.length || 0} Transactions</span>
            </CardHeader>

            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-border/80 text-slate-500 uppercase text-[10px]">
                    <th className="py-2.5 px-3">Side</th>
                    <th className="py-2.5 px-3">Amount</th>
                    <th className="py-2.5 px-3 text-right">Price</th>
                    <th className="py-2.5 px-3 text-right">Value</th>
                    <th className="py-2.5 px-3 text-right">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40 text-slate-300">
                  {(p?.recent_trades || []).map((t: any) => (
                    <tr key={t.id} className="hover:bg-surface/50">
                      <td className={`py-2 px-3 font-bold ${t.side === "BUY" ? "text-bullish" : "text-bearish"}`}>{t.side}</td>
                      <td className="py-2 px-3">{t.amount.toFixed(4)} BTC</td>
                      <td className="py-2 px-3 text-right tabular-nums">${t.price.toLocaleString()}</td>
                      <td className="py-2 px-3 text-right tabular-nums">${t.value.toLocaleString()}</td>
                      <td className="py-2 px-3 text-right text-slate-500 text-[11px]">{t.timestamp.slice(11, 16)}</td>
                    </tr>
                  ))}
                  {(!p?.recent_trades || p.recent_trades.length === 0) && (
                    <tr>
                      <td colSpan={5} className="py-6 text-center text-slate-500">
                        No paper trades executed yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
