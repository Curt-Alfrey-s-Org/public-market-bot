/**
 * System API functions
 */

import apiClient from './client'

export interface SelfTestResult {
  name: string
  status: 'PASS' | 'FAIL'
  passed: boolean
  error?: string
}

export interface SystemHealthResponse {
  status: 'healthy' | 'degraded' | 'error'
  self_test: {
    passed: boolean
    total: number
    passed_count: number
    failed_count: number
    success_rate: number
    results: SelfTestResult[]
    timings?: {
      total_duration_ms: number
      total_duration_s: number
      start_time: string
      end_time: string
      test_timings?: Record<string, number>
    }
    error?: string
  }
  startup_timings?: Record<string, {
    duration_s: number
    duration_ms: number
    timestamp: string
  }>
  system?: {
    platform: string
    python_version: string
  }
  error?: string
}

export interface SystemInfoResponse {
  system: {
    platform: string
    platform_version?: string
    architecture?: string
    processor?: string
    python_version: string
  }
  resources: {
    cpu_count?: number
    memory_total?: number
    memory_available?: number
    memory_percent?: number
    disk_usage?: {
      total: number
      used: number
      free: number
      percent: number
    }
    note?: string
  }
  error?: string
}

export interface RunTestsResponse {
  success: boolean
  total: number
  passed: number
  failed: number
  warnings: number
  duration_s: number
  failed_tests?: Array<{
    name: string
    passed: boolean
    error?: string
  }>
  output?: string
  error?: string
  timestamp: string
  /** 'full_run' = user ran full test suite; 'health' = synced from health check. Red badge only when full_run failed. */
  source?: 'full_run' | 'health'
}

export const systemApi = {
  getHealth: async (): Promise<SystemHealthResponse> => {
    const response = await apiClient.get<SystemHealthResponse>('/api/system/health')
    return response.data
  },
  
  getSystemInfo: async (): Promise<SystemInfoResponse> => {
    const response = await apiClient.get<SystemInfoResponse>('/api/system')
    return response.data
  },
  
  runTests: async (): Promise<RunTestsResponse> => {
    // Backend default timeout is 300s; allow 310s so response can return before client times out
    const response = await apiClient.post<RunTestsResponse>('/api/system/run-tests', {}, { timeout: 310000 })
    return response.data
  },
}
