import React, { useEffect } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";

interface ProtectedRouteProps {
  children?: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, isLoading, isInitialized, initAuth } = useAuthStore();
  const location = useLocation();

  useEffect(() => {
    if (!isInitialized) {
      initAuth();
    }
  }, [isInitialized, initAuth]);

  if (!isInitialized || isLoading) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center">
        <div className="w-10 h-10 rounded-xl bg-gold-500/10 border border-gold-500/30 flex items-center justify-center animate-pulse-subtle">
          <span className="text-gold-400 font-mono font-bold text-lg">₿</span>
        </div>
        <span className="text-xs font-mono text-slate-400 mt-3 tracking-wider uppercase">Authenticating Session...</span>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};
