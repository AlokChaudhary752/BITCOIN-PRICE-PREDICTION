import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Eye, EyeOff, Lock, Mail, User, ShieldCheck, ArrowRight, AlertCircle } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";

export const AuthPage: React.FC = () => {
  const [isSignUp, setIsSignUp] = useState<boolean>(false);
  const [showPassword, setShowPassword] = useState<boolean>(false);

  // Login Form states
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Signup Form states
  const [signupFullName, setSignupFullName] = useState("");
  const [signupEmail, setSignupEmail] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  const [signupConfirmPassword, setSignupConfirmPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [termsAccepted, setTermsAccepted] = useState(true);
  const [validationError, setValidationError] = useState<string | null>(null);

  const { login, register, error, clearError, isLoading } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as any)?.from?.pathname || "/dashboard";

  // Password strength meter
  const getPasswordStrength = (pass: string) => {
    let score = 0;
    if (pass.length >= 8) score++;
    if (pass.length >= 12) score++;
    if (/[A-Z]/.test(pass)) score++;
    if (/[0-9]/.test(pass)) score++;
    if (/[^A-Za-z0-9]/.test(pass)) score++;
    return score;
  };

  const strength = getPasswordStrength(signupPassword);
  const strengthLabels = ["Very Weak", "Weak", "Fair", "Strong", "Institutional Grade"];
  const strengthColors = ["bg-bearish", "bg-orange-500", "bg-amber-400", "bg-gold-500", "bg-bullish"];

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    clearError();
    try {
      await login(loginEmail, loginPassword);
      navigate(from, { replace: true });
    } catch {
      // Error handled in store
    }
  };

  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    clearError();

    if (!signupFullName.trim()) {
      setValidationError("Full name is required.");
      return;
    }
    if (signupPassword !== signupConfirmPassword) {
      setValidationError("Passwords do not match.");
      return;
    }
    if (signupPassword.length < 8) {
      setValidationError("Password must be at least 8 characters.");
      return;
    }
    if (!termsAccepted) {
      setValidationError("Please accept terms of service.");
      return;
    }

    try {
      await register(signupFullName, signupEmail, signupPassword);
      navigate(from, { replace: true });
    } catch {
      // Error is set in store
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Lightweight 3D backdrop glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] bg-gradient-to-tr from-gold-500/10 via-amber-500/5 to-transparent rounded-full blur-[120px] pointer-events-none" />

      {/* Brand Header */}
      <div className="flex flex-col items-center mb-8 relative z-10 cursor-pointer" onClick={() => navigate("/")}>
        <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-gold-600 via-gold-500 to-amber-300 flex items-center justify-center shadow-gold mb-3">
          <span className="text-background font-bold text-xl font-mono">₿</span>
        </div>
        <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-1.5">
          BTC <span className="gold-gradient-text">ORACLE</span>
        </h1>
        <span className="text-xs text-slate-400 font-mono tracking-wider mt-0.5">INSTITUTIONAL GATEWAY</span>
      </div>

      {/* 3D Card Flip Container */}
      <div className="w-full max-w-md relative z-10 [perspective:1200px]">
        <motion.div
          animate={{ rotateY: isSignUp ? 180 : 0 }}
          transition={{ duration: 0.6, ease: "easeInOut" }}
          className="w-full [transform-style:preserve-3d] relative"
        >
          {/* LOGIN CARD (FRONT) */}
          <div
            className={`w-full glass-card rounded-2xl p-7 border border-border/80 shadow-glass [backface-visibility:hidden] ${
              isSignUp ? "pointer-events-none" : ""
            }`}
          >
            <div className="text-left mb-6">
              <h2 className="text-lg font-bold text-slate-100">Sign in to Terminal</h2>
              <p className="text-xs text-slate-400 mt-1">Access probabilistic BTC models and live forecasts</p>
            </div>

            {(error || validationError) && !isSignUp && (
              <div className="p-3 mb-5 rounded-lg bg-bearish/10 border border-bearish/30 text-bearish text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error || validationError}</span>
              </div>
            )}

            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Work Email</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    name="email"
                    data-testid="login-email"
                    required
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    placeholder="analyst@fund.com"
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-lg bg-surface/80 border border-border/80 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-gold-500/50 focus:ring-1 focus:ring-gold-500/20"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    data-testid="login-password"
                    required
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full pl-9 pr-9 py-2 text-xs rounded-lg bg-surface/80 border border-border/80 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-gold-500/50 focus:ring-1 focus:ring-gold-500/20"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs pt-1">
                <label className="flex items-center gap-2 cursor-pointer text-slate-400 select-none">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="rounded bg-surface border-border text-gold-500 focus:ring-0"
                  />
                  <span>Remember me</span>
                </label>
                <a href="#reset" className="text-gold-400 hover:underline">Forgot password?</a>
              </div>

              <button
                type="submit"
                data-testid="login-submit"
                disabled={isLoading}
                className="w-full py-2.5 rounded-lg bg-gradient-to-r from-gold-500 to-amber-500 text-slate-950 font-bold text-xs tracking-wide flex items-center justify-center gap-2 hover:brightness-110 transition-all shadow-gold disabled:opacity-50 cursor-pointer mt-2"
              >
                {isLoading ? "Signing in..." : "Enter Terminal"} <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </form>

            <div className="mt-6 pt-5 border-t border-border/60 text-center">
              <span className="text-xs text-slate-400">Don't have institutional credentials? </span>
              <button
                type="button"
                data-testid="switch-to-signup"
                onClick={() => {
                  clearError();
                  setValidationError(null);
                  setIsSignUp(true);
                }}
                className="text-xs font-semibold text-gold-400 hover:underline ml-1"
              >
                Request Access
              </button>
            </div>
          </div>

          {/* SIGN UP CARD (BACK) */}
          <div
            className={`w-full glass-card rounded-2xl p-7 border border-border/80 shadow-glass [backface-visibility:hidden] [transform:rotateY(180deg)] absolute top-0 left-0 ${
              !isSignUp ? "pointer-events-none" : ""
            }`}
          >
            <div className="text-left mb-5">
              <h2 className="text-lg font-bold text-slate-100">Create Account</h2>
              <p className="text-xs text-slate-400 mt-1">Initialize paper portfolio with $100k virtual capital</p>
            </div>

            {(error || validationError) && isSignUp && (
              <div className="p-3 mb-4 rounded-lg bg-bearish/10 border border-bearish/30 text-bearish text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error || validationError}</span>
              </div>
            )}

            <form onSubmit={handleSignupSubmit} className="space-y-3.5">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    name="signup_fullname"
                    data-testid="signup-fullname"
                    required
                    value={signupFullName}
                    onChange={(e) => setSignupFullName(e.target.value)}
                    placeholder="Alexander Hamilton"
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-lg bg-surface/80 border border-border/80 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-gold-500/50"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Email</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    name="signup_email"
                    data-testid="signup-email"
                    required
                    value={signupEmail}
                    onChange={(e) => setSignupEmail(e.target.value)}
                    placeholder="analyst@fund.com"
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-lg bg-surface/80 border border-border/80 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-gold-500/50"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    name="signup_password"
                    data-testid="signup-password"
                    required
                    value={signupPassword}
                    onChange={(e) => setSignupPassword(e.target.value)}
                    placeholder="Min. 8 characters"
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-lg bg-surface/80 border border-border/80 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-gold-500/50"
                  />
                </div>

                {/* Password Strength Meter */}
                {signupPassword.length > 0 && (
                  <div className="mt-2 space-y-1">
                    <div className="flex gap-1 h-1">
                      {[1, 2, 3, 4, 5].map((lvl) => (
                        <div
                          key={lvl}
                          className={`flex-1 rounded-full transition-all ${
                            lvl <= strength ? strengthColors[strength - 1] : "bg-slate-800"
                          }`}
                        />
                      ))}
                    </div>
                    <span className="text-[10px] text-slate-400 font-mono">
                      Strength: {strengthLabels[Math.max(0, strength - 1)]}
                    </span>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Confirm Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    name="signup_confirm_password"
                    data-testid="signup-confirm-password"
                    required
                    value={signupConfirmPassword}
                    onChange={(e) => setSignupConfirmPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-lg bg-surface/80 border border-border/80 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-gold-500/50"
                  />
                </div>
              </div>

              <div className="pt-1">
                <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-400 select-none">
                  <input
                    type="checkbox"
                    checked={termsAccepted}
                    onChange={(e) => setTermsAccepted(e.target.checked)}
                    className="rounded bg-surface border-border text-gold-500 focus:ring-0"
                  />
                  <span>I understand forecasts are probabilistic & educational.</span>
                </label>
              </div>

              <button
                type="submit"
                data-testid="signup-submit"
                disabled={isLoading}
                className="w-full py-2.5 rounded-lg bg-gradient-to-r from-gold-500 to-amber-500 text-slate-950 font-bold text-xs tracking-wide flex items-center justify-center gap-2 hover:brightness-110 transition-all shadow-gold disabled:opacity-50 cursor-pointer mt-2"
              >
                {isLoading ? "Creating..." : "Initialize Account"} <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </form>

            <div className="mt-5 pt-4 border-t border-border/60 text-center">
              <span className="text-xs text-slate-400">Already registered? </span>
              <button
                type="button"
                data-testid="switch-to-login"
                onClick={() => {
                  clearError();
                  setValidationError(null);
                  setIsSignUp(false);
                }}
                className="text-xs font-semibold text-gold-400 hover:underline ml-1"
              >
                Sign In
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};
