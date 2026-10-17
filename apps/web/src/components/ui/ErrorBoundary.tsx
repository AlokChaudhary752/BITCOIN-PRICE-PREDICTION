import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error in UI component:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 rounded-xl border border-bearish/30 bg-bearish/5 text-center flex flex-col items-center justify-center my-4">
          <AlertTriangle className="w-8 h-8 text-bearish mb-2" />
          <h4 className="text-sm font-semibold text-slate-200">
            {this.props.fallbackTitle || "Component Failed to Load"}
          </h4>
          <p className="text-xs text-slate-400 mt-1 max-w-md font-mono">
            {this.state.error?.message || "An unexpected error occurred."}
          </p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="mt-4 px-3 py-1.5 rounded-lg bg-slate-800 text-xs font-medium text-slate-200 hover:bg-slate-700 flex items-center gap-1.5 border border-border"
          >
            <RefreshCw className="w-3 h-3" /> Retry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
