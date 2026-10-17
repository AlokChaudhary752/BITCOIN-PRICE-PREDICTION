import React, { useState } from "react";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { OverviewView } from "@/views/OverviewView";
import { ForecastsView } from "@/views/ForecastsView";
import { TechnicalsView } from "@/views/TechnicalsView";
import { OnChainView } from "@/views/OnChainView";
import { SentimentView } from "@/views/SentimentView";
import { BacktestView } from "@/views/BacktestView";
import { ModelLabView } from "@/views/ModelLabView";
import { AlertsView } from "@/views/AlertsView";
import { PortfolioView } from "@/views/PortfolioView";
import { SettingsView } from "@/views/SettingsView";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

export const DashboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>("overview");

  const renderActiveView = () => {
    switch (activeTab) {
      case "overview":
        return <OverviewView />;
      case "forecasts":
        return <ForecastsView />;
      case "technicals":
        return <TechnicalsView />;
      case "onchain":
        return <OnChainView />;
      case "sentiment":
        return <SentimentView />;
      case "backtest":
        return <BacktestView />;
      case "modellab":
        return <ModelLabView />;
      case "alerts":
        return <AlertsView />;
      case "portfolio":
        return <PortfolioView />;
      case "settings":
        return <SettingsView />;
      default:
        return <OverviewView />;
    }
  };

  return (
    <DashboardLayout activeNav={activeTab} onNavChange={setActiveTab}>
      <ErrorBoundary fallbackTitle="View Failed to Load">
        {renderActiveView()}
      </ErrorBoundary>
    </DashboardLayout>
  );
};
