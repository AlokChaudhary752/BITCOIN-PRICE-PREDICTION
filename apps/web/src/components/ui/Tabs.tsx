import React from "react";
import { clsx } from "clsx";

interface TabItem {
  id: string;
  label: string;
  badge?: string | number;
}

interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
  size?: "sm" | "md";
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onChange,
  className,
  size = "md",
}) => {
  return (
    <div
      className={clsx(
        "flex items-center gap-1 p-1 bg-surface/80 border border-border/60 rounded-xl overflow-x-auto",
        className
      )}
      role="tablist"
    >
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.id)}
            className={clsx(
              "flex items-center gap-2 rounded-lg font-medium transition-all whitespace-nowrap",
              size === "sm" ? "px-3 py-1 text-xs" : "px-4 py-1.5 text-sm",
              isActive
                ? "bg-gold-500/15 text-gold-400 border border-gold-500/30 shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
            )}
          >
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span
                className={clsx(
                  "text-[10px] px-1.5 py-0.2 rounded-full font-mono",
                  isActive ? "bg-gold-500/20 text-gold-300" : "bg-slate-800 text-slate-400"
                )}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
