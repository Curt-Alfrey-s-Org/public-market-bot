// TypeScript type definitions for Market Bot Mobile API

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  username: string;
  email?: string;
  created_at?: string;
}

export interface BotStatusResponse {
  status: 'stopped' | 'running' | 'error';
  mode: 'live' | 'sandbox' | 'backtest';
  uptime_seconds?: number;
  active_positions: number;
  pending_orders: number;
  last_trade_time?: string;
  capital_available: number;
  capital_invested: number;
  total_capital: number;
}

export interface BotControlResponse {
  success: boolean;
  message: string;
  status?: 'stopped' | 'running';
}

export interface Trade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  total_value: number;
  timestamp: string;
  status: 'pending' | 'filled' | 'canceled' | 'rejected';
}

export interface TradeDetail extends Trade {
  order_id?: string;
  commission?: number;
  profit_loss?: number;
  strategy?: string;
  notes?: string;
}

export interface TradesResponse {
  trades: Trade[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface StatisticsResponse {
  total_trades: number;
  win_rate: number;
  total_profit_loss: number;
  avg_profit_per_trade: number;
  best_trade: number;
  worst_trade: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
}

export interface SettingsResponse {
  risk_per_trade: number;
  max_positions: number;
  stop_loss_percent: number;
  take_profit_percent: number;
  strategy: string;
  auto_trading: boolean;
}

export interface ErrorResponse {
  detail: string;
  status_code?: number;
  timestamp?: string;
}
