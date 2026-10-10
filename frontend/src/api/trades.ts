/**
 * Trades API functions
 */

import apiClient from './client'

export interface Trade {
  symbol: string
  side: 'long' | 'short'
  entry_price: number
  exit_price?: number
  quantity: number
  pnl?: number
  status: 'open' | 'closed'
  entry_timestamp: string
  exit_timestamp?: string
  strategy?: string
}

export interface TradesResponse {
  trades: Trade[]
  total: number
}

export interface TradesFilters {
  symbol?: string
  side?: 'long' | 'short'
  status?: 'open' | 'closed'
  limit?: number
}

export const tradesApi = {
  getTrades: async (filters?: TradesFilters): Promise<TradesResponse> => {
    const params = new URLSearchParams()
    if (filters?.symbol) params.append('symbol', filters.symbol)
    if (filters?.side) params.append('side', filters.side)
    if (filters?.status) params.append('status', filters.status)
    if (filters?.limit) params.append('limit', filters.limit.toString())
    
    const response = await apiClient.get<TradesResponse>(`/api/trades?${params.toString()}`)
    return response.data
  },
  resetTrades: async (sessionOnly: boolean = false): Promise<{ message: string }> => {
    const params = new URLSearchParams()
    params.append('session_only', String(sessionOnly))
    const response = await apiClient.post(`/api/trades/reset?${params.toString()}`)
    return response.data
  }
}
