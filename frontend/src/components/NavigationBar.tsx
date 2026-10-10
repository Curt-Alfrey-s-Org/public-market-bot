import { Link, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getAuthHeaders } from '@/lib/authToken'

interface NavItem {
  path: string
  label: string
  icon: string
}

interface MLFilterSettings {
  enabled: boolean
  min_confidence: number
  min_win_prob: number
  filter_available: boolean
}

// Auth comes from the logged-in user's JWT (no API key in the bundle).
const authHeaders = (): Record<string, string> => getAuthHeaders() ?? {}

const navItems: NavItem[] = [
  { path: '/', label: 'Dashboard', icon: '📈' },
  { path: '/trades', label: 'Trades', icon: '💰' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
  { path: '/system', label: 'System', icon: '🖥️' },
  { path: '/ai', label: 'AI Assistant', icon: '🎓' },
  { path: '/tax', label: 'Tax Reports', icon: '📊' },
]

export default function NavigationBar() {
  const location = useLocation()
  // Lazy-load reset to avoid heavy imports here
  const [isResetting, setIsResetting] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [mlSettings, setMlSettings] = useState<MLFilterSettings | null>(null)
  const [isTogglingML, setIsTogglingML] = useState(false)

  // Load ML filter settings on mount
  useEffect(() => {
    const loadMLSettings = async () => {
      try {
        const response = await fetch('/api/settings/ml-filter', {
          headers: authHeaders(),
        })
        const data = await response.json()
        setMlSettings(data)
      } catch (e) {
        console.error('Failed to load ML filter settings:', e)
      }
    }
    loadMLSettings()
  }, [])

  const handleReset = async () => {
    setIsResetting(true)
    try {
      const mod = await import('@/api/trades')
      await mod.tradesApi.resetTrades(false)
    } catch (e: any) {
      console.error('Reset trades failed:', e?.message || e)
    } finally {
      setIsResetting(false)
      setShowConfirm(false)
      // Trigger hard refresh of critical queries by reloading page (simple and reliable)
      try { window.location.reload() } catch {}
    }
  }

  const handleToggleMLFilter = async () => {
    if (!mlSettings) return
    setIsTogglingML(true)
    try {
      const response = await fetch('/api/settings/ml-filter', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...authHeaders() } as Record<string, string>,
        body: JSON.stringify({
          enabled: !mlSettings.enabled
        })
      })
      const data = await response.json()
      if (data.settings) {
        setMlSettings(data.settings)
      }
    } catch (e: any) {
      console.error('Failed to toggle ML filter:', e?.message || e)
    } finally {
      setIsTogglingML(false)
    }
  }

  return (
    <nav className="bg-card/90 backdrop-blur-sm border-b border-border sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-2">
              <span className="text-2xl">📊</span>
              <span className="text-xl font-bold">Market Pie5 Bot</span>
            </Link>
          </div>

          {/* Navigation Items */}
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-primary text-primary-foreground shadow-md'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                  }`}
                >
                  <span className="mr-2">{item.icon}</span>
                  {item.label}
                </Link>
              )
            })}
            {/* Reset Trades button (top bar) */}
            <button
              onClick={() => setShowConfirm(true)}
              className="ml-2 px-3 py-2 rounded-lg text-sm font-medium bg-destructive text-destructive-foreground hover:bg-destructive/90"
              title="Reset trades and stats (yfinance/simulation mode)"
            >
              {isResetting ? 'Resetting…' : 'Reset Trades'}
            </button>

            {/* ML Filter toggle button */}
            {mlSettings && mlSettings.filter_available && (
              <button
                onClick={handleToggleMLFilter}
                disabled={isTogglingML}
                className={`ml-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  mlSettings.enabled
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-orange-600 text-white hover:bg-orange-700'
                } disabled:opacity-50`}
                title={mlSettings.enabled ? 'ML filter is ON (click to turn off)' : 'ML filter is OFF (click to turn on)'}
              >
                {isTogglingML ? 'Updating…' : `ML ${mlSettings.enabled ? 'ON' : 'OFF'}`}
              </button>
            )}
          </div>
        </div>
      </div>
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-card rounded-lg p-4 shadow-lg w-[320px]">
            <h2 className="text-lg font-semibold mb-2">Reset Trades</h2>
            <p className="text-sm text-muted-foreground mb-4">This clears all trades, stats, and resets the bot loop. Continue?</p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-3 py-2 rounded-lg text-sm bg-accent text-foreground hover:bg-accent/80"
              >
                Cancel
              </button>
              <button
                onClick={handleReset}
                disabled={isResetting}
                className="px-3 py-2 rounded-lg text-sm bg-destructive text-destructive-foreground hover:bg-destructive/90 disabled:opacity-50"
              >
                {isResetting ? 'Resetting…' : 'Reset'}
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}
