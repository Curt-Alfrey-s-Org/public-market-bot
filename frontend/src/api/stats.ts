/**
 * Stats API functions
 */

import apiClient from './client'

export interface MonthlyReturn {
  month: string
  return_pct: number
  pnl: number
  capital: number
}

export interface Stats {
  capital: number
  capital_change: number
  capital_change_pct: number
  allocation: number
  win_rate: number
  total_trades: number
  open_positions: number
  total_pnl: number
  profit_factor: number
  monthly_return_pct: number
  monthly_returns: MonthlyReturn[]
}

export const statsApi = {
  getStats: async (): Promise<Stats> => {
    const response = await apiClient.get<Stats>('/api/stats')
    return response.data
  },
}
