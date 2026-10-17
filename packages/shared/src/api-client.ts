/**
 * Typed API Client generated against the BTC Oracle OpenAPI specification.
 * Automatically synchronizes with backend endpoints and cookie-authenticated sessions.
 */
import type {
  UserResponse,
  TokenResponse,
  LivePriceResponse,
  MarketHistoryResponse,
  OrderBookResponse,
  OnChainMetricsResponse,
  PredictionResponse,
  PredictionHistoryItem,
  BacktestRequest,
  BacktestResponse,
  AlertItem,
  PaperPortfolioResponse,
  PaperTradeItem,
} from "./types";

export class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl?: string) {
    if (baseUrl !== undefined) {
      this.baseUrl = baseUrl;
    } else if (typeof window !== "undefined") {
      this.baseUrl = "";
    } else {
      this.baseUrl = "http://localhost:8000";
    }
  }

  setToken(token: string | null) {
    this.token = token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers || {});
    headers.set("Content-Type", "application/json");
    if (this.token) {
      headers.set("Authorization", `Bearer ${this.token}`);
    }

    const res = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
      credentials: "include", // send httpOnly cookies
    });

    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(errorBody.detail || `Request failed with status ${res.status}`);
    }

    return res.json() as Promise<T>;
  }

  // Auth
  async register(data: { email: string; password: string; full_name: string }): Promise<UserResponse> {
    return this.request<UserResponse>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async login(data: { email: string; password: string; totp_code?: string }): Promise<TokenResponse> {
    const res = await this.request<TokenResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
    this.setToken(res.access_token);
    return res;
  }

  async refresh(): Promise<TokenResponse> {
    const res = await this.request<TokenResponse>("/api/v1/auth/refresh", {
      method: "POST",
    });
    this.setToken(res.access_token);
    return res;
  }

  async logout(): Promise<{ message: string }> {
    const res = await this.request<{ message: string }>("/api/v1/auth/logout", {
      method: "POST",
    });
    this.setToken(null);
    return res;
  }

  async getMe(): Promise<UserResponse> {
    return this.request<UserResponse>("/api/v1/auth/me");
  }

  // Market
  async getLivePrice(): Promise<LivePriceResponse> {
    return this.request<LivePriceResponse>("/api/v1/market/price/live");
  }

  async getHistory(interval: string = "1h", limit: number = 300): Promise<MarketHistoryResponse> {
    return this.request<MarketHistoryResponse>(`/api/v1/market/price/history?interval=${interval}&limit=${limit}`);
  }

  async getOrderBook(): Promise<OrderBookResponse> {
    return this.request<OrderBookResponse>("/api/v1/market/orderbook");
  }

  async getOnChain(): Promise<OnChainMetricsResponse> {
    return this.request<OnChainMetricsResponse>("/api/v1/market/onchain");
  }

  // Forecast
  async getLivePrediction(): Promise<PredictionResponse> {
    return this.request<PredictionResponse>("/api/v1/forecast/predict");
  }

  async getAllHorizons(): Promise<Record<string, any>> {
    return this.request<Record<string, any>>("/api/v1/forecast/predict/all");
  }

  async getPredictionHistory(limit: number = 50): Promise<PredictionHistoryItem[]> {
    return this.request<PredictionHistoryItem[]>(`/api/v1/forecast/predictions/history?limit=${limit}`);
  }

  async getModelPerformance(): Promise<any> {
    return this.request<any>("/api/v1/forecast/models/performance");
  }

  async getModelCalibration(): Promise<any> {
    return this.request<any>("/api/v1/forecast/models/calibration");
  }

  async getModelExplain(): Promise<any> {
    return this.request<any>("/api/v1/forecast/models/explain");
  }

  async getModelDrift(): Promise<any> {
    return this.request<any>("/api/v1/forecast/models/drift");
  }

  async getRegime(): Promise<any> {
    return this.request<any>("/api/v1/forecast/regime");
  }

  // Analysis
  async getIndicators(): Promise<any> {
    return this.request<any>("/api/v1/analysis/indicators");
  }

  async getSentiment(): Promise<any> {
    return this.request<any>("/api/v1/analysis/sentiment");
  }

  async runBacktest(params: BacktestRequest): Promise<BacktestResponse> {
    return this.request<BacktestResponse>("/api/v1/analysis/backtest", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // User & Portfolio
  async getAlerts(): Promise<AlertItem[]> {
    return this.request<AlertItem[]>("/api/v1/user/alerts");
  }

  async createAlert(data: { alert_type: string; condition: string; threshold?: number; target_value?: string }): Promise<AlertItem> {
    return this.request<AlertItem>("/api/v1/user/alerts", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async deleteAlert(id: string): Promise<void> {
    await this.request<void>(`/api/v1/user/alerts/${id}`, { method: "DELETE" });
  }

  async getPortfolio(): Promise<PaperPortfolioResponse> {
    return this.request<PaperPortfolioResponse>("/api/v1/user/portfolio");
  }

  async executeTrade(side: "BUY" | "SELL", amount: number): Promise<PaperTradeItem> {
    return this.request<PaperTradeItem>("/api/v1/user/portfolio/trade", {
      method: "POST",
      body: JSON.stringify({ side, amount }),
    });
  }
}

export const api = new ApiClient();
