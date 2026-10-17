import React from "react";
import { clsx } from "clsx";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "glow" | "gold" | "bullish" | "bearish";
}

export const Card: React.FC<CardProps> = ({
  className,
  variant = "default",
  children,
  ...props
}) => {
  const variantStyles = {
    default: "border-border/60 hover:border-border",
    glow: "border-gold-500/20 shadow-gold",
    gold: "border-gold-500/30 hover:border-gold-500/50 hover:shadow-gold",
    bullish: "border-bullish/30 hover:border-bullish/50 hover:shadow-emerald",
    bearish: "border-bearish/30 hover:border-bearish/50 hover:shadow-rose",
  };

  return (
    <div
      className={clsx(
        "glass-card rounded-xl p-5 relative overflow-hidden",
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div className={clsx("flex items-center justify-between mb-4", className)} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  className,
  children,
  ...props
}) => (
  <h3 className={clsx("text-sm font-semibold tracking-wide uppercase text-slate-400 flex items-center gap-2", className)} {...props}>
    {children}
  </h3>
);
