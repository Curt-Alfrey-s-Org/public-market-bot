/**
 * Auth Context — handles user authentication for this app.
 * Uses legacy /api/auth/login first; centralized auth when available.
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { login as apiLogin, me as apiMe } from '@/api/auth'

const STORAGE_KEY = 'market_bot_auth'

/** Roles the backend issues for web logins. The server enforces permissions; the UI just mirrors them. */
export type AuthRole = 'admin' | 'director' | 'user'

export interface AuthUser {
  user: string
  role: AuthRole
  token?: string
}

/** Map a server-provided role to a known role, or null for anything else (never upgrade to admin). */
export function toAuthRole(role: unknown): AuthRole | null {
  return role === 'admin' || role === 'director' || role === 'user' ? role : null
}

interface AuthContextValue {
  user: AuthUser | null
  loading: boolean
  login: (username: string, password: string) => Promise<{ success: boolean; message?: string }>
  logout: () => Promise<void>
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

function loadStoredAuth(): AuthUser | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    const role = toAuthRole(parsed?.role)
    if (parsed?.user && role) {
      return {
        user: parsed.user,
        role,
        token: parsed.token,
      }
    }
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    localStorage.removeItem(STORAGE_KEY)
  }
  return null
}

function saveAuth(u: AuthUser | null) {
  if (u) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      user: u.user,
      role: u.role,
      token: u.token,
    }))
  } else {
    localStorage.removeItem(STORAGE_KEY)
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = loadStoredAuth()
    if (!stored?.token) {
      setUser(stored)
      setLoading(false)
      return
    }
    apiMe()
      .then((me) => {
        const role = toAuthRole(me.role)
        if (!role) {
          // Unknown/guest role from the server: treat as signed out rather than guessing.
          setUser(null)
          saveAuth(null)
          return
        }
        setUser({ ...stored, role })
        saveAuth({ ...stored, role })
      })
      .catch(() => {
        setUser(null)
        saveAuth(null)
      })
      .finally(() => setLoading(false))
  }, [])

  // API client clears tokens and dispatches auth-401 after failed refresh; sync React state
  useEffect(() => {
    const onSessionExpired = () => {
      setUser(null)
      saveAuth(null)
    }
    window.addEventListener('auth-401', onSessionExpired)
    return () => window.removeEventListener('auth-401', onSessionExpired)
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    try {
      // Use legacy login (env-based: ADMIN_USERNAME, ADMIN_PASSWORD, etc.)
      // Fallback when centralized auth-service is unavailable or credentials not registered there
      const res = await apiLogin(username.trim(), password)
      // Use the role the server issued. Previously any non-admin/director role was
      // shown as 'admin' in the UI (security review 2026-09-25 follow-up).
      const role = toAuthRole(res.role)
      if (!role) {
        return { success: false, message: 'This account role cannot sign in to the web app' }
      }
      const newUser: AuthUser = {
        user: res.user,
        role,
        token: res.access_token,
      }
      setUser(newUser)
      saveAuth(newUser)
      return { success: true }
    } catch (err) {
      return {
        success: false,
        message: err && typeof err === 'object' && 'response' in err
          ? (err as any).response?.data?.detail || 'Invalid username or password'
          : 'Login failed',
      }
    }
  }, [])

  const logout = useCallback(async () => {
    setUser(null)
    saveAuth(null)
    window.dispatchEvent(new CustomEvent('auth-logout'))
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
