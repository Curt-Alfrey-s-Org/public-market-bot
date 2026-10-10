/**
 * Login form — User/Admin only. Guest access is disabled.
 */

import { useState, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'

interface LoginFormProps {
  onSubmit: (username: string, password: string) => Promise<{ success: boolean; message?: string }>
  onSuccess: () => void
}

export default function LoginForm({ onSubmit, onSuccess }: LoginFormProps) {
  useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    if (!username.trim()) {
      setError('Username is required')
      return
    }
    if (!password) {
      setError('Password is required')
      return
    }
    setLoading(true)
    try {
      const res = await onSubmit(username.trim(), password)
      if (res.success) {
        onSuccess()
      } else {
        setError(res.message || 'Invalid username or password')
      }
    } catch {
      setError('Login failed')
    } finally {
      setLoading(false)
    }
  }

  const isEmailVerificationError = error && /verif/i.test(error)

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-sm mx-auto bg-slate-900/95 backdrop-blur border border-slate-700 rounded-2xl shadow-2xl p-8"
    >
      <div className="text-center mb-6">
        <h2 className="text-xl font-bold text-white">Sign In</h2>
        <p className="text-slate-400 text-sm mt-1">
          Sign in to continue.
        </p>
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 text-sm">
          {error}
          {isEmailVerificationError && (
            <p className="mt-2 text-slate-300 text-xs">
              Check your inbox or <Link to="/verify-email" className="underline text-sky-400">request a new verification link</Link>.
            </p>
          )}
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label htmlFor="username" className="block text-sm font-medium text-slate-300 mb-2">
            Username
          </label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoFocus
            className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-600 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
            disabled={loading}
          />
        </div>
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
            Password
          </label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            placeholder="••••••••"
            className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-600 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
            disabled={loading}
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 px-4 rounded-lg font-semibold text-white bg-sky-600 hover:bg-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </div>

      <p className="mt-4 text-center text-sm text-slate-400">
        Don&apos;t have an account? <Link to="/register" className="text-sky-400 hover:underline">Sign Up</Link>
      </p>
    </form>
  )
}
