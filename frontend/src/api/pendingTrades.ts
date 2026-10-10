import apiClient from './client'

export interface PendingTradeReasoning {
  symbol: string
  action: string
  price: number
  quantity: number
  allocation: number
  timestamp: string
  strategy_signals: {
    combined_signal?: string
    individual_signals?: Record<string, { signal: string; weight: number }>
    signal_strength?: number
  }
  ml_filter: {
    filtered?: boolean
    confidence?: number
    win_probability?: number
    recommendation?: string
  }
  portfolio_optimization: {
    optimized_allocation?: number
    current_allocation?: number
    method?: string
    available_capital?: number
    recommendation?: string
  }
  risk_analysis: {
    potential_loss?: number
    risk_limit?: number
    risk_ratio?: number
    stop_loss_percent?: number
    within_risk_limit?: boolean
    risk_assessment?: string
  }
  market_conditions: {
    volatility?: number
    volume?: number
    price?: number
    volatility_assessment?: string
    liquidity_assessment?: string
  }
  capital_status: {
    available_capital?: number
    total_capital?: number
    allocation_percentage?: number
    next_settlement_date?: string
    next_settlement_amount?: number
    sufficient_capital?: boolean
  }
  monthly_progress: {
    current_return?: number
    target_return?: number
    days_remaining?: number
    progress_percentage?: number
    on_track?: boolean
    needs_catch_up?: boolean
  }
  auto_mode_decision: string
  auto_mode_reasons: string[]
}

export interface AutoModeDetails {
  would_execute: boolean
  decision: string
  reasons: string[]
  expected_allocation: number
  expected_quantity: number
  expected_price: number
}

export interface PendingTrade {
  trade_id: string
  symbol: string
  action: string
  price: number
  quantity: number
  allocation: number
  volume?: number
  reasoning: PendingTradeReasoning
  auto_mode_details: AutoModeDetails
  timestamp: string
  expires_at: string
  status: string
}

export interface PendingTradesResponse {
  pending_trades: PendingTrade[]
  total: number
}

export interface ApproveTradeRequest {
  trade_id: string
}

export interface RejectTradeRequest {
  trade_id: string
  reason?: string
}

export const pendingTradesApi = {
  /**
   * Get all pending trades awaiting approval
   */
  async getPendingTrades(): Promise<PendingTradesResponse> {
    const response = await apiClient.get<PendingTradesResponse>('/api/pending-trades')
    return response.data
  },

  /**
   * Approve a pending trade and execute it
   */
  async approveTrade(tradeId: string): Promise<any> {
    const response = await apiClient.post('/api/pending-trades/approve', {
      trade_id: tradeId,
    } as ApproveTradeRequest)
    return response.data
  },

  /**
   * Reject a pending trade
   */
  async rejectTrade(tradeId: string, reason?: string): Promise<any> {
    const response = await apiClient.post('/api/pending-trades/reject', {
      trade_id: tradeId,
      reason,
    } as RejectTradeRequest)
    return response.data
  },
}
