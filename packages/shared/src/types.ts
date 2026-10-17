/**
 * Shared Type Definitions generated from OpenAPI 3.1.0 schema.
 */

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  role: "user" | "admin";
  is_active: boolean;
  is_verified: boolean;
  two_factor_enabled: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface LivePriceResponse {
  symbol: string;
  price: number;
  change_24h_pct: number;
  high_24h: number;
  low_24h: number;
  volume_24h: number;
  realized_volatility: number;
  timestamp: string;
}

export interface CandleItem {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketHistoryResponse {
  symbol: string;
  interval: string;
  count: number;
  candles: CandleItem[];
}

export interface OrderBookLevel {
  price: number;
  quantity: number;
}

export interface OrderBookResponse {
  symbol: string;
  timestamp: string;
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
  imbalance_ratio: number;
}

export interface OnChainMetricsResponse {
  fastest_fee: number;
  half_hour_fee: number;
  hour_fee: number;
  minimum_fee: number;
  taker_buy_ratio: number;
  volume_momentum_24h: number;
  average_trade_size: number;
}

export interface IntervalBand {
  lower: number;
  upper: number;
  nominal_coverage: number;
  empirical_coverage: number;
}

export interface QuantilesDict {
  q05: number;
  q25: number;
  q50: number;
  q75: number;
  q95: number;
}

export interface HorizonForecast {
  horizon: "1h" | "4h" | "24h" | "7d" | "30d";
  current_price: number;
  point_forecast: number;
  expected_return_pct: number;
  prob_up: number;
  agreement_score: number;
  risk_score: number;
  signal: "Strong Buy" | "Buy" | "Hold / Neutral" | "Sell" | "Strong Sell";
  signal_level: number;
  confidence_level: "High confidence" | "Moderate confidence" | "Low confidence";
  low_confidence_flag: boolean;
  interval_50: IntervalBand;
  interval_90: IntervalBand;
  quantiles: QuantilesDict;
  per_model_median: {
    lgbm: number;
    gru: number;
  };
}

export interface MarketRegime {
  label: "trending_bull" | "ranging" | "high_volatility";
  confidence: number;
  probabilities: {
    ranging: number;
    trending_bull: number;
    high_volatility: number;
  };
}

export interface DriverImpact {
  feature: string;
  description: string;
  value: number;
  shap_value: number;
  abs_impact: number;
  direction: "bullish" | "bearish";
}

export interface PredictionExplanation {
  narrative: string;
  top_drivers: DriverImpact[];
}

export interface PredictionResponse {
  version: string;
  timestamp: string;
  current_price: number;
  market_regime: MarketRegime;
  primary_signal: {
    signal: string;
    signal_level: number;
    prob_up: number;
    expected_return_pct: number;
    risk_score: number;
    agreement_score: number;
    confidence_level: string;
    low_confidence_flag: boolean;
  };
  horizons: Record<string, HorizonForecast>;
  explanation: PredictionExplanation;
}

export interface PredictionHistoryItem {
  id: string;
  timestamp: string;
  horizon: string;
  current_price: number;
  point_forecast: number;
  actual_price: number | null;
  abs_error: number | null;
  is_scored: boolean;
  signal: string;
  model_version: string;
}

export interface BacktestRequest {
  initial_capital?: number;
  fee_rate?: number;
  slippage?: number;
  stop_loss_pct?: number;
  risk_per_trade_pct?: number;
  confidence_threshold?: number;
  start_date?: string;
  end_date?: string;
}

export interface EquityPoint {
  timestamp: string;
  strategy_equity: number;
  benchmark_equity: number;
  drawdown_pct: number;
}

export interface BacktestTradeLog {
  entry_time: string;
  exit_time: string;
  side: string;
  entry_price: number;
  exit_price: number;
  return_pct: number;
  pnl: number;
  reason: string;
}

export interface BacktestResponse {
  initial_capital: number;
  final_equity: number;
  total_return_pct: number;
  benchmark_return_pct: number;
  cagr_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  max_drawdown_pct: number;
  win_rate_pct: number;
  profit_factor: number;
  total_trades: number;
  equity_curve: EquityPoint[];
  trades: BacktestTradeLog[];
}

export interface AlertItem {
  id: string;
  alert_type: "price" | "signal" | "regime";
  condition: string;
  threshold: number | null;
  target_value: string | null;
  is_active: boolean;
  triggered_at: string | null;
  created_at: string;
}

export interface PaperTradeItem {
  id: string;
  side: "BUY" | "SELL";
  price: number;
  amount: number;
  value: number;
  fee: number;
  pnl: number;
  timestamp: string;
}

export interface PaperPortfolioResponse {
  id: string;
  initial_capital: number;
  cash: number;
  btc_balance: number;
  total_equity: number;
  realized_pnl: number;
  current_btc_price: number;
  unrealized_pnl: number;
  recent_trades: PaperTradeItem[];
}
