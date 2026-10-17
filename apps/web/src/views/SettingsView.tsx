import React, { useState } from "react";
import { Settings, Shield, Key, QrCode, CheckCircle2, Lock, AlertTriangle } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useAuthStore } from "@/stores/authStore";

export const SettingsView: React.FC = () => {
  const { user, accessToken } = useAuthStore();
  const [totpData, setTotpData] = useState<any>(null);
  const [verifyCode, setVerifyCode] = useState("");
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const init2FA = async () => {
    try {
      const headers: Record<string, string> = {};
      if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
      const res = await fetch("/api/v1/auth/2fa/setup", {
        method: "POST",
        headers,
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setTotpData(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleVerify2FA = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
      const res = await fetch("/api/v1/auth/2fa/verify", {
        method: "POST",
        headers,
        credentials: "include",
        body: JSON.stringify({ code: verifyCode }),
      });
      if (res.ok) {
        setStatusMsg("Two-factor authentication successfully verified and enabled.");
        setTotpData(null);
      } else {
        setStatusMsg("Invalid verification code.");
      }
    } catch {
      setStatusMsg("Verification failed.");
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Settings className="w-5 h-5 text-gold-500" /> Account & Security Configuration
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Manage institutional credentials, two-factor authentication, and platform settings.
          </p>
        </div>
      </div>

      {statusMsg && (
        <div className="p-3 rounded-lg bg-bullish/10 border border-bullish/30 text-bullish text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{statusMsg}</span>
        </div>
      )}

      {/* USER PROFILE */}
      <Card className="p-5">
        <CardHeader>
          <CardTitle>User Profile</CardTitle>
          <Badge variant="gold" size="sm">{user?.role?.toUpperCase() || "USER"}</Badge>
        </CardHeader>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 font-mono text-xs">
          <div>
            <span className="text-slate-500 block mb-0.5">FULL NAME:</span>
            <span className="text-slate-200 font-semibold">{user?.full_name || "Institutional Analyst"}</span>
          </div>
          <div>
            <span className="text-slate-500 block mb-0.5">EMAIL:</span>
            <span className="text-slate-200 font-semibold">{user?.email || "trader@fund.com"}</span>
          </div>
          <div>
            <span className="text-slate-500 block mb-0.5">ACCOUNT ID:</span>
            <span className="text-slate-400 truncate block">{user?.id || "usr-uuid-primary"}</span>
          </div>
          <div>
            <span className="text-slate-500 block mb-0.5">AUTHENTICATION SCHEME:</span>
            <span className="text-bullish font-semibold">Argon2id + Rotating JWT</span>
          </div>
        </div>
      </Card>

      {/* 2FA SETUP */}
      <Card className="p-5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-gold-500" /> Two-Factor Authentication (TOTP)
          </CardTitle>
          <Badge variant={user?.two_factor_enabled ? "bullish" : "outline"} size="sm">
            {user?.two_factor_enabled ? "ENABLED" : "DISABLED"}
          </Badge>
        </CardHeader>

        <p className="text-xs text-slate-300 leading-relaxed mb-4">
          Protect account actions and withdrawals with standard TOTP authenticators (Google Authenticator, 1Password, or YubiKey).
        </p>

        {!totpData ? (
          <button
            onClick={init2FA}
            className="px-4 py-2 rounded-lg bg-gold-500/10 border border-gold-500/30 text-gold-400 text-xs font-mono font-medium hover:bg-gold-500/20 transition-all cursor-pointer flex items-center gap-2"
          >
            <QrCode className="w-4 h-4" /> Setup Authenticator 2FA
          </button>
        ) : (
          <div className="p-4 rounded-xl bg-surface/80 border border-border/80 space-y-4 font-mono text-xs">
            <div>
              <span className="text-slate-400 block mb-1">PROVISIONING SECRET:</span>
              <code className="text-gold-400 text-sm font-bold tracking-wider">{totpData.secret}</code>
            </div>

            <div>
              <span className="text-slate-400 block mb-1">RECOVERY CODES:</span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {totpData.recovery_codes.map((c: string, i: number) => (
                  <code key={i} className="p-1.5 rounded bg-surface border border-border/50 text-center text-slate-300">{c}</code>
                ))}
              </div>
            </div>

            <form onSubmit={handleVerify2FA} className="flex gap-2 items-center pt-2">
              <input
                type="text"
                placeholder="6-digit code"
                value={verifyCode}
                onChange={(e) => setVerifyCode(e.target.value)}
                className="px-3 py-1.5 rounded bg-surface border border-border text-slate-100 font-mono w-36"
              />
              <button type="submit" className="px-4 py-1.5 rounded bg-bullish text-slate-950 font-bold text-xs">
                Verify & Activate
              </button>
            </form>
          </div>
        )}
      </Card>

      {/* INSTITUTIONAL DISCLAIMER */}
      <Card className="p-5 border-border/80 bg-surface/30">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-gold-500 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-1 font-mono">
              Mandatory Institutional Disclaimer
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed font-mono">
              Forecasts are probabilistic, for educational purposes only, and are not financial advice.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};
