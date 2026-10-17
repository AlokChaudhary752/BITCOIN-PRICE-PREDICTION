import React from "react";
import { clsx } from "clsx";

export const Skeleton: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  ...props
}) => {
  return (
    <div
      className={clsx(
        "animate-pulse bg-slate-800/60 rounded-md",
        className
      )}
      {...props}
    />
  );
};

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionText,
  onAction,
  className,
}) => {
  return (
    <div
      className={clsx(
        "flex flex-col items-center justify-center p-8 text-center border border-dashed border-border/80 rounded-xl bg-surface/30",
        className
      )}
    >
      {icon && <div className="p-3 mb-3 rounded-full bg-slate-800/80 text-gold-400">{icon}</div>}
      <h4 className="text-base font-semibold text-slate-200 mb-1">{title}</h4>
      <p className="text-xs text-slate-400 max-w-sm mb-4 leading-relaxed">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-1.5 text-xs font-medium rounded-lg bg-gold-500/10 text-gold-400 border border-gold-500/30 hover:bg-gold-500/20 transition-all"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
