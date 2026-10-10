/**
 * Mock Data Fixtures for Testing
 */

import { User, LoginResponse, BotStatus, Trade, TradesResponse, Statistics } from '@/types';

export const mockUser: User = {
  id: '123',
  username: 'testuser',
  email: 'operator@example.com',
  role: 'user',
};

export const mockLoginResponse: LoginResponse = {
  access_token: 'change-me',
  token_type: 'change-me',
  expires_in: 86400,
  user: mockUser,
};

export const mockBotStatus: BotStatus = {
  running: true,
  mode: 'yfinance',
  symbol: 'AAPL',
  trades_today: 5,
  total_trades: 150,
  uptime_seconds: 3600,
  last_trade_timestamp: '2026-02-13T10:30:00Z',
  last_update: new Date().toISOString(),
};

export const mockTrade: Trade = {
  id: '1',
  symbol: 'AAPL',
  entry_price: 150.0,
  exit_price: 152.5,
  quantity: 100,
  entry_time: '2026-02-13T09:00:00Z',
  exit_time: '2026-02-13T10:00:00Z',
  strategy: 'momentum',
  status: 'closed',
  pnl: 250.0,
  pnl_pct: 1.67,
  commission: 10.0,
};

export const mockTrades: Trade[] = [
  mockTrade,
  {
    ...mockTrade,
    id: '2',
    symbol: 'GOOGL',
    entry_price: 140.0,
    exit_price: 138.0,
    pnl: -280.0,
    pnl_pct: -2.0,
  },
];

export const mockTradesResponse: TradesResponse = {
  trades: mockTrades,
  total: 150,
  limit: 10,
  offset: 0,
  has_more: true,
};

export const mockStatistics: Statistics = {
  total_trades: 150,
  winning_trades: 92,
  losing_trades: 58,
  win_rate: 61.33,
  total_pnl: 5250.75,
  avg_pnl_per_trade: 35.01,
  best_trade: {
    ...mockTrade,
    pnl: 850.0,
    pnl_pct: 5.67,
  },
  worst_trade: {
    ...mockTrade,
    pnl: -650.0,
    pnl_pct: -4.33,
  },
  sharpe_ratio: 1.85,
  max_drawdown: 12.5,
};

export const mockApiError = {
  error: 'unauthorized',
  message: 'Invalid credentials',
  status_code: 401,
  timestamp: new Date().toISOString(),
};

/**
 * Create mock HTTP error response
 */
export const createMockHttpError = (
  statusCode: number,
  error: Partial<typeof mockApiError> = {}
) => ({
  response: {
    status: statusCode,
    data: {
      ...mockApiError,
      ...error,
      status_code: statusCode,
    },
  },
});
