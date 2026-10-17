import React, { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  TrendingUp,
  LineChart,
  Network,
  Smile,
  History,
  FlaskConical,
  Bell,
  Briefcase,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Search,
  Command,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useAuthStore } from "@/stores/authStore";

interface DashboardLayoutProps {
  children: React.ReactNode;
  activeNav: string;
  onNavChange: (key: string) => void;
}

export const NAV_ITEMS = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "forecasts", label: "Forecasts", icon: TrendingUp },
  { id: "technicals", label: "Technicals", icon: LineChart },
  { id: "onchain", label: "On-Chain", icon: Network },
  { id: "sentiment", label: "Sentiment", icon: Smile },
  { id: "backtest", label: "Backtest", icon: History },
  { id: "modellab", label: "Model Lab", icon: FlaskConical },
  { id: "alerts", label: "Alerts", icon: Bell },
  { id: "portfolio", label: "Paper Portfolio", icon: Briefcase },
  { id: "settings", label: "Settings", icon: Settings },
];

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  activeNav,
  onNavChange,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [livePrice, setLivePrice] = useState<number>(81620.01);
  const [wsConnected, setWsConnected] = useState<boolean>(true);
  const [searchOpen, setSearchOpen] = useState(false);

  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  // Connect to live WebSocket price feed
  useEffect(() => {
    // Initial fetch
    fetch("/api/v1/market/price/live")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.price) setLivePrice(d.price);
      })
      .catch(() => {});

    // Live WebSocket connection
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const ws = new WebSocket(`${protocol}//${host}/api/v1/market/ws/prices`);

    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => setWsConnected(false);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "TICK" && data.price) {
          setLivePrice(data.price);
        }
      } catch {
        // Ignore parse errors
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  // Keyboard shortcut Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-background text-slate-100 flex flex-row overflow-hidden font-sans">
      {/* SIDEBAR */}
      <aside
        className={`bg-surface/95 border-r border-border/80 flex flex-col justify-between transition-all duration-300 relative z-30 ${
          collapsed ? "w-16" : "w-60"
        }`}
      >
        <div>
          {/* Brand header */}
          <div className="h-16 flex items-center justify-between px-4 border-b border-border/60">
            <Link to="/" className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-gold-600 to-amber-400 flex items-center justify-center shrink-0 shadow-gold">
                <span className="text-slate-950 font-bold font-mono text-sm">₿</span>
              </div>
              {!collapsed && (
                <span className="font-bold tracking-tight text-sm text-slate-100">
                  BTC <span className="gold-gradient-text">ORACLE</span>
                </span>
              )}
            </Link>

            <button
              onClick={() => setCollapsed(!collapsed)}
              className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            >
              {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-2 space-y-1 mt-2">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activeNav === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onNavChange(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? "bg-gold-500/15 text-gold-400 border border-gold-500/30 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                  } ${collapsed ? "justify-center px-0" : ""}`}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                </button>
              );
            })}
          </nav>
        </div>

        {/* User Footer */}
        <div className="p-3 border-t border-border/60">
          <div className={`flex items-center gap-2.5 ${collapsed ? "justify-center" : ""}`}>
            <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-mono font-bold text-gold-400 shrink-0">
              {user?.full_name ? user.full_name[0].toUpperCase() : "U"}
            </div>
            {!collapsed && (
              <div className="flex flex-col min-w-0 flex-1 text-left">
                <span className="text-xs font-semibold text-slate-200 truncate">{user?.full_name || "Institutional Analyst"}</span>
                <span className="text-[10px] text-slate-500 truncate font-mono uppercase">{user?.role || "Trader"}</span>
              </div>
            )}
            {!collapsed && (
              <button data-testid="logout-button" onClick={handleLogout} className="text-slate-500 hover:text-bearish p-1" title="Sign Out">
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        {/* TOP BAR */}
        <header className="h-16 border-b border-border/80 bg-surface/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-20">
          {/* Search / Command Palette Trigger */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSearchOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-card border border-border/80 text-xs text-slate-400 hover:border-slate-600 transition-colors cursor-pointer"
            >
              <Search className="w-3.5 h-3.5 text-slate-500" />
              <span>Search metrics, indicators, models...</span>
              <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono bg-slate-800 text-slate-400 rounded border border-border">
                <Command className="w-2.5 h-2.5" /> K
              </kbd>
            </button>
          </div>

          {/* Right Header Status Bar */}
          <div className="flex items-center gap-4">
            {/* Live Ticker */}
            <div className="flex items-center gap-2.5 px-3 py-1 rounded-full bg-surface-card/90 border border-border font-mono text-xs">
              <span className="text-slate-400 font-medium">BTC/USDT</span>
              <span className="font-bold text-slate-100 tabular-nums">${livePrice.toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
              <span className="flex items-center gap-1 text-[11px] text-bullish">
                {wsConnected ? <Wifi className="w-3 h-3 text-bullish" /> : <WifiOff className="w-3 h-3 text-slate-500" />}
                LIVE
              </span>
            </div>

            {/* Terminal Status */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-gold-500/10 text-gold-400 border border-gold-500/25 text-[11px] font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-gold-400 animate-pulse" />
              CHAMPION v1.0
            </div>
          </div>
        </header>

        {/* VIEW CONTAINER */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
          {children}
        </main>
      </div>

      {/* QUICK COMMAND PALETTE MODAL */}
      {searchOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-start justify-center pt-24 p-4" onClick={() => setSearchOpen(false)}>
          <div className="w-full max-w-lg rounded-xl glass-card border border-border/80 shadow-2xl p-4 overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-2 border-b border-border/60 pb-3">
              <Search className="w-4 h-4 text-slate-400" />
              <input
                autoFocus
                placeholder="Jump to section or tool..."
                className="w-full bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
              />
              <kbd className="text-[10px] font-mono text-slate-500 border border-border px-1.5 py-0.5 rounded">ESC</kbd>
            </div>
            <div className="py-2 space-y-1">
              {NAV_ITEMS.map((item) => (
                <button
                  key={item.id}
                  onClick={() => {
                    onNavChange(item.id);
                    setSearchOpen(false);
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs text-slate-300 hover:bg-gold-500/10 hover:text-gold-400 text-left transition-colors"
                >
                  <item.icon className="w-4 h-4 text-slate-500" />
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
