import apiClient from './client'

export interface AiMonitorSummary {
  llm_activity: { total_calls: number; errors: number }
  errors: {
    total_occurrences: number
    distinct_errors: number
    pending: number
    triaged: number
  }
}

export interface AiActivityRow {
  id: number
  created_at: string | null
  feature: string
  model: string
  prompt_summary: string | null
  duration_seconds: number | null
  eval_tokens: number
  prompt_tokens: number
  status: string
  error_message: string | null
}

export interface ErrorEventRow {
  id: number
  created_at: string | null
  error_type: string
  error_message: string | null
  path: string | null
  method: string | null
  request_id: string | null
  count: number
  first_seen: string | null
  last_seen: string | null
  triage_status: string
  triage_summary: string | null
  triage_model: string | null
  triaged_at: string | null
}

const BASE = '/api/admin/ai-monitor'

export const aiMonitorApi = {
  getSummary: () => apiClient.get<AiMonitorSummary>(`${BASE}/summary`),
  getActivity: (limit = 50) =>
    apiClient.get<AiActivityRow[]>(`${BASE}/activity`, { params: { limit } }),
  getErrors: (limit = 50) =>
    apiClient.get<ErrorEventRow[]>(`${BASE}/errors`, { params: { limit } }),
  triageNow: (limit = 10) =>
    apiClient.post<{ status: string; triaged: number }>(`${BASE}/errors/triage`, null, {
      params: { limit },
    }),
}
