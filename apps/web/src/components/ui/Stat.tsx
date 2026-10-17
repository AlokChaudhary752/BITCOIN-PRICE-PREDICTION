import React from "react";
import { clsx } from "clsx";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface StatProps {
  label: string;
  value: string | number;
  change?: number;
  changeSuffix?: string;
  subtext?: string;
  prefix?: string;
  variant?: "default" | "gold" | "bullish" | "bearish";
  icon?: React.ReactNode;
  className?: string;
}

export const Stat: React.FC<StatProps> = ({
  label,
  value,
  change,
  changeSuffix = "%",
  subtext,
  prefix,
  variant = "default",
  icon,
  className,
}) => {
  const isPositive = change !== undefined && change > 0;
  const isNegative = change !== undefined && change < 0;

  const valueColors = {
    default: "text-slate-100",
    gold: "text-gold-400",
    bullish: "text-bullish",
    bearish: "text-bearish",
  };

  return (
    <div className={clsx("flex flex-col gap-1 p-3.5 rounded-lg bg-surface/50 border border-border/40", className)}>
      <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-medium">
        <span>{label}</span>
        {icon && <span className="text-slate-500">{icon}</span>}
      </div>

      <div className="flex items-baseline gap-2 mt-0.5">
        <span className={clsx("font-mono text-xl sm:text-2xl font-bold tracking-tight tabular-nums", valueColors[variant])}>
          {prefix}{value}
        </span>

        {change !== undefined && (
          <span
            className={clsx(
              "inline-flex items-center text-xs font-mono font-medium px-1.5 py-0.5 rounded",
              isPositive && "bg-bullish/10 text-bullish",
              isNegative && "bg-bearish/10 text-bearish",
              !isPositive && !isNegative && "bg-slate-800 text-slate-400"
            )}
          >
            {isPositive && <TrendingUp className="w-3 h-3 mr-0.5" />}
            {isNegative && <TrendingDown className="w-3 h-3 mr-0.5" />}
            {!isPositive && !isNegative && <Minus className="w-3 h-3 mr-0.5" />}
            {isPositive ? "+" : ""}{change.toFixed(2)}{changeSuffix}
          </span>
        )}
      </div>

      {subtext && <span className="text-[11px] text-slate-500 mt-0.5">{subtext}</span>}
    </div>
  );
};
