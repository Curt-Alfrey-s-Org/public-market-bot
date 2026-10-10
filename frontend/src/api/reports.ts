/**
 * Reports API – decision report (candidates + per-symbol decisions)
 */

import apiClient from './client'

export interface DecisionRow {
  symbol: string
  signal: string
  action: string
  price: number | null
  volume: number | null
  reason: string
  cycle_number: number
  updated_at: string
}

export interface DecisionReportResponse {
  candidates: string[]
  decisions: DecisionRow[]
  cycle_number: number
  total_candidates: number
  evaluated_count?: number
  cycle_in_progress_no_data?: boolean
  last_cycle_timings?: Record<string, number> | null
}

export const reportsApi = {
  getDecisionReport(): Promise<DecisionReportResponse> {
    return apiClient.get('/api/reports/decisions').then((r) => r.data)
  },
}
