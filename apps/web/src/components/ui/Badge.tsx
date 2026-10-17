import React from "react";
import { clsx } from "clsx";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "gold" | "bullish" | "bearish" | "outline" | "neutral";
  size?: "sm" | "md";
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = "default",
  size = "md",
  children,
  ...props
}) => {
  const variantStyles = {
    default: "bg-slate-800/80 text-slate-300 border-slate-700/60",
    gold: "bg-gold-500/10 text-gold-400 border-gold-500/30",
    bullish: "bg-bullish/10 text-bullish border-bullish/30",
    bearish: "bg-bearish/10 text-bearish border-bearish/30",
    neutral: "bg-slate-800 text-slate-400 border-slate-700",
    outline: "border-border text-slate-400",
  };

  const sizeStyles = {
    sm: "text-[10px] px-2 py-0.5",
    md: "text-xs px-2.5 py-1",
  };

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full font-medium border font-mono tracking-wide uppercase",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};
