import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { TrendingUp, TrendingDown, Shield, Cpu, Activity, ArrowRight, User } from "lucide-react";

interface NavbarProps {
  currentPrice?: number;
  change24h?: number;
  isAuthenticated?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentPrice = 81620.01,
  change24h = 1.25,
  isAuthenticated = false,
}) => {
  const [scrolled, setScrolled] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const isBullish = change24h >= 0;

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled ? "bg-surface/85 backdrop-blur-md border-b border-border/80 shadow-glass py-3" : "bg-transparent py-5"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        {/* Logo and Brand */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-gold-600 via-gold-500 to-amber-300 flex items-center justify-center shadow-gold group-hover:scale-105 transition-transform">
            <span className="text-background font-bold text-lg font-mono">₿</span>
          </div>
          <div className="flex flex-col">
            <span className="font-bold tracking-tight text-base text-slate-100 flex items-center gap-1.5">
              BTC <span className="gold-gradient-text">ORACLE</span>
            </span>
            <span className="text-[10px] text-slate-400 uppercase tracking-widest font-mono">Institutional Intelligence</span>
          </div>
        </Link>

        {/* Live Market Price Ticker */}
        <div className="hidden md:flex items-center gap-3 px-3.5 py-1.5 rounded-full bg-surface-card/80 border border-border/80 font-mono text-xs">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-bullish opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-bullish"></span>
          </span>
          <span className="text-slate-400 font-medium">BTC/USDT</span>
          <span className="font-bold text-slate-100 tabular-nums">${currentPrice.toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
          <span className={`flex items-center gap-0.5 font-semibold tabular-nums ${isBullish ? "text-bullish" : "text-bearish"}`}>
            {isBullish ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {isBullish ? "+" : ""}{change24h.toFixed(2)}%
          </span>
        </div>

        {/* Nav Links */}
        <div className="hidden lg:flex items-center gap-7 text-xs font-medium uppercase tracking-wider text-slate-300">
          <a href="#pipeline" className="hover:text-gold-400 transition-colors flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-gold-500" /> Pipeline
          </a>
          <a href="#capabilities" className="hover:text-gold-400 transition-colors flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-gold-500" /> Capabilities
          </a>
          <a href="#performance" className="hover:text-gold-400 transition-colors">
            Performance
          </a>
          <a href="#security" className="hover:text-gold-400 transition-colors flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-gold-500" /> Security
          </a>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <button
              onClick={() => navigate("/dashboard")}
              className="px-4 py-2 rounded-lg bg-gold-500/10 text-gold-400 border border-gold-500/30 hover:bg-gold-500/20 text-xs font-mono font-medium tracking-wide flex items-center gap-2 transition-all shadow-gold"
            >
              <User className="w-3.5 h-3.5" /> Dashboard
            </button>
          ) : (
            <>
              <button
                onClick={() => navigate("/login")}
                className="text-xs font-medium text-slate-300 hover:text-slate-100 px-3 py-2 transition-colors"
              >
                Sign In
              </button>
              <button
                onClick={() => navigate("/dashboard")}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-gold-500 to-amber-500 text-slate-950 font-bold text-xs tracking-wide flex items-center gap-1.5 hover:brightness-110 transition-all shadow-gold"
              >
                Launch Terminal <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};
