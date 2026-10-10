/**
 * API client: timeouts, correlation-friendly logging, throttled toasts for polling,
 * token refresh, and rejection with real Axios errors (preserves error.response for React Query).
 */

import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { toast } from '@/lib/toast'

/** Raw env base (e.g. https://api.example.com or empty for same-origin). */
const _raw = import.meta.env.VITE_API_URL
const API_BASE_URL =
  typeof _raw === 'string' && _raw.trim() !== '' ? _raw.replace(/\/+$/, '') : ''

// No backend API key in the bundle (anything in VITE_* is public). Every request
// authenticates with the logged-in user's JWT; the server enforces roles.

const CONNECTION_TOAST_THROTTLE_MS = 60_000
let lastConnectionErrorToastAt = 0

function isPollingEndpoint(url: string): boolean {
  const u = url.replace(/\?.*/, '')
  return (
    u.endsWith('/health') ||
    u.endsWith('/health/detailed') ||
    u.endsWith('/system/health') ||
    u.endsWith('/bot/status')
  )
}

function shouldShowConnectionToast(url: string): boolean {
  if (!isPollingEndpoint(url)) return true
  const now = Date.now()
  if (now - lastConnectionErrorToastAt < CONNECTION_TOAST_THROTTLE_MS) return false
  lastConnectionErrorToastAt = now
  return true
}

function getApiErrorDetail(data: unknown): string | undefined {
  if (!data || typeof data !== 'object') return undefined
  const d = data as Record<string, unknown>
  if (typeof d.message === 'string') return d.message
  if (typeof d.detail === 'string') return d.detail
  const err = d.error
  if (err && typeof err === 'object' && 'message' in err) {
    const m = (err as { message?: string }).message
    if (typeof m === 'string') return m
  }
  return undefined
}

function isIdempotentMethod(method: string): boolean {
  return method === 'GET' || method === 'HEAD' || method === 'OPTIONS'
}

type ConfigWithMeta = InternalAxiosRequestConfig & { metadata?: { startTime: number } }

let retryCount = 0
const MAX_RETRIES = 3
const RETRY_DELAY = 1000

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

apiClient.interceptors.request.use(
  (config) => {
    const c = config as ConfigWithMeta
    c.metadata = { startTime: Date.now() }

    try {
      const accessToken = localStorage.getItem('access_token')
      if (accessToken) {
        c.headers.Authorization = `Bearer ${accessToken}`
      } else {
        const raw =
          localStorage.getItem('market_bot_auth') ||
          localStorage.getItem('contracts_bot_auth') ||
          localStorage.getItem('credit_bot_auth')
        if (raw) {
          const parsed = JSON.parse(raw) as { token?: string }
          if (parsed?.token) {
            c.headers.Authorization = `Bearer ${parsed.token}`
          }
        }
      }
    } catch (e) {
      console.error('[API] Error parsing auth:', e)
    }
    return c
  },
  (error) => Promise.reject(error)
)

apiClient.interceptors.response.use(
  (response) => {
    retryCount = 0
    const cfg = response.config as ConfigWithMeta
    const start = cfg.metadata?.startTime
    const duration = start ? Date.now() - start : undefined
    const rid = response.headers?.['x-request-id'] ?? response.headers?.['X-Request-ID']
    if (import.meta.env.DEV) {
      console.debug('[API]', response.config.method?.toUpperCase(), response.config.url, response.status, duration, rid)
    }
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as ConfigWithMeta | undefined
    const startTime = originalRequest?.metadata?.startTime
    const duration = startTime ? Date.now() - startTime : undefined
    const method = originalRequest?.method?.toUpperCase() || 'GET'
    const url = originalRequest?.url || 'unknown'
    const status = error.response?.status

    if (error.response?.status === 405) {
      if (import.meta.env.DEV) {
        console.warn('[API] 405 — request may not reach API (proxy/tunnel)', { url, method })
      }
      return Promise.reject(error)
    }

    if (status === 401 && originalRequest && !(originalRequest as { _retry?: boolean })._retry) {
      ;(originalRequest as { _retry?: boolean })._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const refreshUrl = `${API_BASE_URL || ''}/api/auth/refresh-centralized`
          const response = await fetch(refreshUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          })

          if (response.ok) {
            const data = (await response.json()) as { access_token: string; refresh_token: string }
            localStorage.setItem('access_token', data.access_token)
            localStorage.setItem('refresh_token', data.refresh_token)
            originalRequest.headers = originalRequest.headers || {}
            originalRequest.headers.Authorization = `Bearer ${data.access_token}`
            return apiClient(originalRequest)
          }
        }
      } catch (refreshError) {
        console.error('[API] Token refresh failed:', refreshError)
      }

      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('market_bot_auth')
      localStorage.removeItem('contracts_bot_auth')
      localStorage.removeItem('credit_bot_auth')
      toast.authError('Your session has expired. Please log in again.')
      try {
        window.dispatchEvent(new CustomEvent('auth-401'))
      } catch {
        /* ignore */
      }
      return Promise.reject(error)
    }

    if (status === 403) {
      toast.apiError(403, undefined, getApiErrorDetail(error.response?.data))
      return Promise.reject(error)
    }

    if (status === 429) {
      const cfg = originalRequest
      if (cfg && retryCount < MAX_RETRIES) {
        retryCount++
        const delay = RETRY_DELAY * Math.pow(2, retryCount)
        await new Promise((r) => setTimeout(r, delay))
        return apiClient(cfg)
      }
      toast.apiError(429, undefined, getApiErrorDetail(error.response?.data))
      return Promise.reject(error)
    }

    if (status !== undefined && status >= 500) {
      const cfg = originalRequest
      // Only replay idempotent requests. A 500 from POST/PUT/DELETE (bot start,
      // trade approve, settings save...) may come after the server already acted,
      // so re-sending it could repeat the action.
      if (cfg && isIdempotentMethod(method) && retryCount < MAX_RETRIES) {
        retryCount++
        const delay = RETRY_DELAY * Math.pow(2, retryCount)
        await new Promise((r) => setTimeout(r, delay))
        return apiClient(cfg)
      }
      if (shouldShowConnectionToast(url)) {
        toast.apiError(status, undefined, getApiErrorDetail(error.response?.data))
      }
      if (import.meta.env.DEV) {
        console.error('[API] Server error', { url, method, status, duration, data: error.response?.data })
      }
      return Promise.reject(error)
    }

    if (status !== undefined && status >= 400) {
      toast.apiError(status, undefined, getApiErrorDetail(error.response?.data))
      return Promise.reject(error)
    }

    if (!error.response) {
      const isTimeout = error.code === 'ECONNABORTED' || error.message?.includes('timeout')
      if (isTimeout) {
        if (shouldShowConnectionToast(url)) toast.timeoutError()
      } else if (shouldShowConnectionToast(url)) {
        toast.networkError()
      }
      if (import.meta.env.DEV) {
        console.error('[API] Network error', { url, method, code: error.code, duration })
      }
      return Promise.reject(error)
    }

    return Promise.reject(error)
  }
)

export default apiClient
