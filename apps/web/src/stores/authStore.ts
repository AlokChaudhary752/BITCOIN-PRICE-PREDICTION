import { create } from "zustand";
import { api } from "@shared/api-client";
import type { UserResponse } from "@shared/types";

interface AuthState {
  user: UserResponse | null;
  accessToken: string | null;
  isLoading: boolean;
  isInitialized: boolean;
  error: string | null;
  login: (email: string, password: string, totpCode?: string) => Promise<void>;
  register: (fullName: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshTokens: () => Promise<boolean>;
  initAuth: () => Promise<void>;
  bypassLogin: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isLoading: false,
  isInitialized: false,
  error: null,

  clearError: () => set({ error: null }),

  login: async (email: string, password: string, totpCode?: string) => {
    set({ isLoading: true, error: null });
    try {
      const tokenRes = await api.login({ email, password, totp_code: totpCode });
      api.setToken(tokenRes.access_token);
      const userRes = await api.getMe();
      set({ user: userRes, accessToken: tokenRes.access_token, isLoading: false });
    } catch (err: any) {
      set({ error: err.message || "Login failed.", isLoading: false });
      throw err;
    }
  },

  register: async (fullName: string, email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      await api.register({ full_name: fullName, email, password });
      // Automatically log in after registration
      const tokenRes = await api.login({ email, password });
      api.setToken(tokenRes.access_token);
      const userRes = await api.getMe();
      set({ user: userRes, accessToken: tokenRes.access_token, isLoading: false });
    } catch (err: any) {
      set({ error: err.message || "Registration failed.", isLoading: false });
      throw err;
    }
  },

  logout: async () => {
    try {
      await api.logout();
    } catch {
      // Ignore
    } finally {
      api.setToken(null);
      set({ user: null, accessToken: null });
    }
  },

  refreshTokens: async () => {
    try {
      const res = await api.refresh();
      api.setToken(res.access_token);
      const userRes = await api.getMe();
      set({ user: userRes, accessToken: res.access_token });
      return true;
    } catch {
      api.setToken(null);
      set({ user: null, accessToken: null });
      return false;
    }
  },

  initAuth: async () => {
    if (get().isInitialized) return;
    set({ isLoading: true });
    try {
      await get().refreshTokens();
    } catch {
      // Ignore
    } finally {
      set({ isLoading: false, isInitialized: true });
    }
  },

  bypassLogin: async () => {
    set({ isLoading: true, error: null });
    const demoEmail = "demo@btc-oracle.local";
    const demoPassword = "DemoPassword123!";
    const demoFullName = "Institutional Analyst (Demo)";

    try {
      try {
        const tokenRes = await api.login({ email: demoEmail, password: demoPassword });
        api.setToken(tokenRes.access_token);
        const userRes = await api.getMe();
        set({ user: userRes, accessToken: tokenRes.access_token, isLoading: false, isInitialized: true });
        return;
      } catch {
        // Create demo account if not exists
        await api.register({ full_name: demoFullName, email: demoEmail, password: demoPassword });
        const tokenRes = await api.login({ email: demoEmail, password: demoPassword });
        api.setToken(tokenRes.access_token);
        const userRes = await api.getMe();
        set({ user: userRes, accessToken: tokenRes.access_token, isLoading: false, isInitialized: true });
        return;
      }
    } catch {
      // Offline / guest mock fallback
      const guestUser: UserResponse = {
        id: "guest-bypass-user",
        email: demoEmail,
        full_name: demoFullName,
        role: "admin",
        is_active: true,
        is_verified: true,
        two_factor_enabled: false,
        created_at: new Date().toISOString(),
      };
      set({ user: guestUser, accessToken: "bypass-demo-token", isLoading: false, isInitialized: true, error: null });
    }
  },
}));
