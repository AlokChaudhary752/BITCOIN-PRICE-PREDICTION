import React, { useEffect, useState } from "react";
import { Bell, Plus, Trash2, CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useAuthStore } from "@/stores/authStore";

export const AlertsView: React.FC = () => {
  const { accessToken } = useAuthStore();
  const [alerts, setAlerts] = useState<any[]>([]);
  const [alertType, setAlertType] = useState("price");
  const [condition, setCondition] = useState("above");
  const [threshold, setThreshold] = useState("85000");
  const [targetValue, setTargetValue] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  const fetchAlerts = async () => {
    try {
      const headers: Record<string, string> = {};
      if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
      const res = await fetch("/api/v1/user/alerts", { headers, credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setAlerts(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [accessToken]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
      const res = await fetch("/api/v1/user/alerts", {
        method: "POST",
        headers,
        credentials: "include",
        body: JSON.stringify({
          alert_type: alertType,
          condition: condition,
          threshold: threshold ? parseFloat(threshold) : null,
          target_value: targetValue || null,
        }),
      });
      if (res.ok) {
        setMsg("Alert trigger successfully configured.");
        fetchAlerts();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const headers: Record<string, string> = {};
      if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
      const res = await fetch(`/api/v1/user/alerts/${id}`, {
        method: "DELETE",
        headers,
        credentials: "include",
      });
      if (res.ok) {
        fetchAlerts();
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Bell className="w-5 h-5 text-gold-500" /> Automated Triggers & Alerts
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time triggers on price levels, model AI signal shifts, and HMM regime transitions.
          </p>
        </div>
        <Badge variant="gold" size="md">In-App & Webhook Delivery</Badge>
      </div>

      {msg && (
        <div className="p-3 rounded-lg bg-bullish/10 border border-bullish/30 text-bullish text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{msg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Create Alert Form */}
        <div className="lg:col-span-4">
          <Card className="p-5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Plus className="w-4 h-4 text-gold-500" /> New Alert Trigger
              </CardTitle>
            </CardHeader>

            <form onSubmit={handleCreate} className="space-y-4 font-mono text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Trigger Type</label>
                <select
                  value={alertType}
                  onChange={(e) => setAlertType(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-surface border border-border/80 text-slate-100 focus:outline-none"
                >
                  <option value="price">Price Threshold ($)</option>
                  <option value="signal">AI Signal Shift</option>
                  <option value="regime">Market Regime Change</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Condition</label>
                <select
                  value={condition}
                  onChange={(e) => setCondition(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-surface border border-border/80 text-slate-100 focus:outline-none"
                >
                  <option value="above">Breaches Above</option>
                  <option value="below">Breaches Below</option>
                  <option value="change">State Transitions</option>
                </select>
              </div>

              {alertType === "price" ? (
                <div>
                  <label className="text-slate-400 block mb-1">Threshold Price ($)</label>
                  <input
                    type="number"
                    value={threshold}
                    onChange={(e) => setThreshold(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-surface border border-border/80 text-slate-100 focus:outline-none"
                  />
                </div>
              ) : (
                <div>
                  <label className="text-slate-400 block mb-1">Target Value</label>
                  <input
                    type="text"
                    value={targetValue}
                    onChange={(e) => setTargetValue(e.target.value)}
                    placeholder="e.g. Strong Buy or high_volatility"
                    className="w-full px-3 py-2 rounded-lg bg-surface border border-border/80 text-slate-100 focus:outline-none"
                  />
                </div>
              )}

              <button
                type="submit"
                className="w-full py-2.5 rounded-lg bg-gold-500 text-slate-950 font-bold text-xs tracking-wide flex items-center justify-center gap-1.5 hover:bg-gold-400 transition-all cursor-pointer mt-2"
              >
                <Plus className="w-3.5 h-3.5" /> Arm Trigger
              </button>
            </form>
          </Card>
        </div>

        {/* Active Alerts List */}
        <div className="lg:col-span-8">
          <Card className="p-5">
            <CardHeader>
              <CardTitle>Active Trigger Monitors</CardTitle>
              <span className="text-xs font-mono text-slate-400">{alerts.length} Configured</span>
            </CardHeader>

            {alerts.length === 0 ? (
              <div className="p-8 text-center text-slate-500 font-mono text-xs border border-dashed border-border/60 rounded-xl">
                No active triggers configured. Use the form on the left to set price or regime alerts.
              </div>
            ) : (
              <div className="space-y-2 font-mono text-xs">
                {alerts.map((a: any) => (
                  <div key={a.id} className="p-3 rounded-lg bg-surface/70 border border-border/50 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="w-2 h-2 rounded-full bg-gold-500" />
                      <div>
                        <span className="font-bold text-slate-200 uppercase">{a.alert_type}</span>
                        <span className="text-slate-400 ml-2">
                          {a.condition} {a.threshold ? `$${a.threshold.toLocaleString()}` : a.target_value}
                        </span>
                      </div>
                    </div>
                    <button onClick={() => handleDelete(a.id)} className="text-slate-500 hover:text-bearish p-1">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
