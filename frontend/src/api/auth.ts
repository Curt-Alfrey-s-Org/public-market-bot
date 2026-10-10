/**
 * Auth API: Centralized authentication with JWT
 * ============================================
 * Integrates with centralized auth-service via bot API proxy
 */

import apiClient from './client'

export interface TokenResponse {
  access_token: string
  token_type: string
  role: string
  user: string
}

export interface MeResponse {
  role: string
  sub: string
}

export interface CentralizedLoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user_id: string
  organization_id: string
  expires_in: number
}

/** Shape returned by POST /api/auth/login (api/routes/auth.py LoginResponse). */
interface LegacyLoginResponse {
  success: boolean
  token?: string | null
  access_token?: string | null
  user?: string | null
  role?: string | null
  message?: string | null
}

// Legacy login (env-based + DB users). The backend answers 200 with
// success=false on bad credentials and returns the JWT as `token`; map that to
// TokenResponse and reject on failure so the app never "logs in" without a
// real session token (the API now requires it on every request).
export async function login(username: string, password: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<LegacyLoginResponse>('/api/auth/login', {
    username: username.trim(),
    password,
  })
  const accessToken = data?.access_token || data?.token
  if (!data?.success || !accessToken) {
    const err = new Error(data?.message || 'Invalid username or password') as Error & {
      response?: { data?: { detail?: string } }
    }
    err.response = { data: { detail: data?.message || 'Invalid username or password' } }
    throw err
  }
  return {
    access_token: accessToken,
    token_type: 'change-me',
    role: data.role || '',
    user: data.user || username.trim(),
  }
}

export async function me(): Promise<MeResponse> {
  const { data } = await apiClient.get<MeResponse>('/api/auth/me')
  return data
}

// ===== CENTRALIZED AUTH METHODS (NEW) =====

export const authApi = {
  /**
   * Register new user via centralized auth-service
   */
  registerCentralized: async (
    username: string, 
    email: string, 
    password: string, 
    licenseKey: string = 'FREE-TRIAL-2024'
  ) => {
    const response = await fetch(`${apiClient.defaults.baseURL}/api/auth/register-centralized`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        username, 
        email, 
        password, 
        captcha_token: 'change-me',
        license_key: licenseKey 
      })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Registration failed')
    }
    
    return response.json()
  },

  /**
   * Login via centralized auth-service
   */
  loginCentralized: async (username: string, password: string): Promise<CentralizedLoginResponse> => {
    const response = await fetch(`${apiClient.defaults.baseURL}/api/auth/login-centralized`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }
    
    const data = await response.json()
    
    // Store tokens
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user_id', data.user_id)
    localStorage.setItem('organization_id', data.organization_id)
    
    return data
  },

  verifyEmailCentralized: async (token: string) => {
    const response = await fetch(`${apiClient.defaults.baseURL}/api/auth/verify-email-centralized`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Verification failed')
    }
    
    return response.json()
  },

  refreshTokenCentralized: async (): Promise<CentralizedLoginResponse> => {
    const refreshToken = localStorage.getItem('refresh_token')
    
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }
    
    const response = await fetch(`${apiClient.defaults.baseURL}/api/auth/refresh-centralized`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    })
    
    if (!response.ok) {
      localStorage.clear()
      window.location.href = '/login'
      throw new Error('Token refresh failed')
    }
    
    const data = await response.json()
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    
    return data
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('organization_id')
    localStorage.removeItem('market_bot_auth') // Legacy
  },

  // ===== TWO-FACTOR AUTHENTICATION (Phase 6) =====

  setup2FA: async () => {
    const token = localStorage.getItem('access_token')
    const response = await fetch(`${apiClient.defaults.baseURL}/api/auth/2fa/setup`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({})
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '2FA setup failed')
    }

    return response.json()
  },

  verify2FASetup: async (code: string) => {
    const token = localStorage.getItem('access_token')
    const response = await fetch(`${apiClient.defaults.baseURL}/api/auth/2fa/verify-setup`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ code })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '2FA verification failed')
    }

    return response.json()
  },

  verify2FALogin: async (userId: string, code: string): Promise<CentralizedLoginResponse> => {
    const response = await fetch(`${apiClient.defaults.baseURL}/api/auth/2fa/verify-login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, code })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '2FA verification failed')
    }

    const data = await response.json()

    // Store tokens
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)

    return data
  },

  get2FAStatus: async () => {
    const token = localStorage.getItem('access_token')
    const response = await fetch(`${apiClient.defaults.baseURL}/api/auth/2fa/status`, {
      method: 'GET',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '2FA status check failed')
    }

    return response.json()
  },

  disable2FA: async () => {
    const token = localStorage.getItem('access_token')
    const response = await fetch(`${apiClient.defaults.baseURL}/api/auth/2fa/disable`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({})
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '2FA disable failed')
    }

    return response.json()
  }
}
