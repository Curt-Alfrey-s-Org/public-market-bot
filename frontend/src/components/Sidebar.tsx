import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import MessageBox from './MessageBox'
import SelfTestPanel from './SelfTestPanel'
import FailDetailsPopup from './FailDetailsPopup'
import { systemApi, type RunTestsResponse, type SystemHealthResponse } from '@/api/system'
import { useBotStatus } from '@/hooks/useBotStatus'
import { useAuth } from '@/context/AuthContext'

/** Convert health self_test result to RunTestsResponse so View Fail Details can show startup or health-check results */
function healthToLastTestResult(health: SystemHealthResponse): RunTestsResponse | null {
  const st = health?.self_test
  if (!st || !Array.isArray(st.results)) return null
  const failed_tests = st.results
    .filter((r: { passed?: boolean }) => !r.passed)
    .map((r: { name: string; error?: string }) => ({ name: r.name, passed: false, error: r.error }))
  const total = st.total ?? 0
  const passed = st.passed_count ?? 0
  const failed = st.failed_count ?? failed_tests.length
  const durationMs = st.timings?.total_duration_ms ?? 0
  return {
    success: st.passed ?? false,
    total,
    passed,
    failed,
    warnings: 0,
    duration_s: durationMs / 1000,
    failed_tests: failed_tests.length > 0 ? failed_tests : undefined,
    timestamp: new Date().toISOString(),
    source: 'health',
  }
}

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
  avatarUrl?: string
  /** When true, hide avatar (none for pics). */
  avatarNone?: boolean
}

const DEFAULT_AVATAR = '/assets/avatar-default.png'

export default function Sidebar({ isOpen, onToggle, avatarUrl = DEFAULT_AVATAR, avatarNone = false }: SidebarProps) {
  const location = useLocation()
  const queryClient = useQueryClient()
  const { user, logout } = useAuth()
  const [showTestPanel, setShowTestPanel] = useState(false)
  const [showFailDetails, setShowFailDetails] = useState(false)
  
  // Bot status (needed to disable Run Test when bot is running)
  const { data: botStatus } = useBotStatus()

  // Fetch system health for status indicators
  const { data: health } = useQuery({
    queryKey: ['system-health'],
    queryFn: systemApi.getHealth,
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: 1,
    retryDelay: 1000,
    staleTime: 10000,
  })

  // Subscribe to last-test-result so badge and "View Fail Details" use the same source (avoids red badge when full run passed).
  const { data: lastTestResult } = useQuery({
    queryKey: ['last-test-result'],
    queryFn: () => Promise.resolve(null as RunTestsResponse | null),
    staleTime: Infinity,
    gcTime: Infinity,
  })

  // Sync startup/health self-test results into last-test-result so View Fail Details can show them.
  // Only set when there is no existing result, so "Run Test" button result is not overwritten by health refetch.
  useEffect(() => {
    if (!health) return
    const existing = queryClient.getQueryData<RunTestsResponse>(['last-test-result'])
    if (existing != null) return // Keep button-run result; don't overwrite with health
    const lastResult = healthToLastTestResult(health)
    if (lastResult) {
      queryClient.setQueryData(['last-test-result'], lastResult)
    }
  }, [health, queryClient])

  // Badge: red only when user ran full test suite and it failed. On first load (health failed) show yellow so we don't greet with red.
  const last = lastTestResult as (RunTestsResponse & { source?: 'full_run' | 'health' }) | null | undefined
  const hasFullRunResult = last != null && last.source === 'full_run'
  const selfTestPassed =
    hasFullRunResult
      ? last!.success
      : health?.self_test?.passed === true
        ? true
        : null
  const passedCount = hasFullRunResult ? last!.passed : health?.self_test?.passed_count
  const totalCount = hasFullRunResult ? last!.total : health?.self_test?.total

  const HOME_URL = 'https://example.com'
  const menuItems = [
    { path: '/', label: 'Dashboard', icon: '📈' },
    { path: '/trades', label: 'Trades', icon: '💰' },
    { path: '/pending-trades', label: 'Pending Trades', icon: '⏳' },
    { path: '/settings', label: 'Settings', icon: '⚙️' },
    { path: '/logs', label: 'Logs', icon: '📝' },
    { path: '/system', label: 'System', icon: '🖥️' },
    { path: '/ai', label: 'AI Assistant', icon: '🎓' },
    { path: '/tax', label: 'Tax Reports', icon: '📊' },
    { path: '/reports/decisions', label: 'Decision Report', icon: '📋' },
    { path: '/admin/health', label: 'Health Dashboard', icon: '🏥' },
    { path: '/admin/ai-monitor', label: 'AI Monitor', icon: '🧠' },
    { path: '/admin/user-settings', label: 'User Settings', icon: '👤' },
  ]

  return (
    <aside
      className={`fixed md:static left-0 md:top-auto top-16 md:top-0 h-[calc(100vh-64px)] md:h-full bg-card/95 border-r border-border transition-all duration-300 z-30 md:z-50 ${
        isOpen ? 'w-64 md:w-64 max-w-[85vw] md:max-w-none' : 'w-0 md:w-64 overflow-hidden md:overflow-auto'
      }`}
      aria-label="Main navigation"
    >
      <div className="h-full flex flex-col">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-border flex items-center justify-between gap-2">
          {isOpen && (
            <>
              <div className="flex items-center gap-2 min-w-0">
                {!avatarNone && (
                  <img
                    src={avatarUrl}
                    alt="Avatar"
                    className="w-9 h-9 rounded-full object-cover flex-shrink-0 border-2 border-border"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = DEFAULT_AVATAR
                    }}
                  />
                )}
                <h2 className="text-lg font-bold truncate">Menu</h2>
              </div>
              <button
                onClick={onToggle}
                className="p-1 hover:bg-accent rounded transition-colors transition-opacity"
                aria-label="Close menu"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </>
          )}
        </div>

        {/* Navigation */}
        {isOpen && (
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            <a
              href={HOME_URL}
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors hover:bg-accent text-foreground border border-border/50 mb-2"
            >
              <span className="text-xl">🏠</span>
              <span className="font-medium">Home</span>
            </a>
            {menuItems.map((item) => {
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-accent text-foreground'
                  }`}
                >
                  <span className="text-xl">{item.icon}</span>
                  <span className="font-medium">{item.label}</span>
                </Link>
              )
            })}
            
            {/* Messages & Alerts Section - Below Tax Reports */}
            <div className="mt-4 pt-4 border-t border-border">
              <MessageBox />
            </div>
          </nav>
        )}

        {/* Footer with Status Indicators */}
        {isOpen && (
          <div className="p-4 border-t border-border">
            {/* Self-Test Status */}
            <div className="mb-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-muted-foreground">Self-Test:</span>
                <div className="flex items-center gap-2">
                  {selfTestPassed === true && (
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" title="All tests passed"></div>
                      <span className="text-xs text-green-500">PASS</span>
                    </div>
                  )}
                  {selfTestPassed === false && (
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 rounded-full bg-red-500" title="Some tests failed"></div>
                      <span className="text-xs text-red-500">FAIL</span>
                    </div>
                  )}
                  {selfTestPassed === null && (
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" title="Testing..."></div>
                      <span className="text-xs text-yellow-500">...</span>
                    </div>
                  )}
                  {/* Run Test Button */}
                  <button
                    onClick={() => setShowTestPanel(true)}
                    className="ml-1 px-2 py-0.5 text-[10px] bg-primary/20 hover:bg-primary/30 text-primary rounded transition-colors"
                    title="Run full self-test suite"
                  >
                    Run Test
                  </button>
                </div>
              </div>
              {(passedCount != null && totalCount != null) && (
                <div className="text-[10px] text-muted-foreground/70 mb-1">
                  {passedCount}/{totalCount} passed
                  {health?.self_test?.timings != null && ` • ${Number(health.self_test.timings.total_duration_ms).toFixed(0)}ms`}
                </div>
              )}
              {/* View Fail Details Button */}
              <button
                onClick={() => setShowFailDetails(true)}
                className="w-full mt-1 px-2 py-1 text-[10px] bg-muted/50 hover:bg-muted text-muted-foreground rounded transition-colors"
                title="Show popup of test fail details for analysis"
              >
                View Fail Details
              </button>
            </div>
            
            {/* User & Log out */}
            {user && (
              <div className="mb-3 pt-3 border-t border-border">
                <p className="text-xs text-muted-foreground">Signed in as <span className="font-medium text-foreground">{user.user}</span> ({user.role})</p>
                <button
                  onClick={() => logout()}
                  className="mt-2 w-full py-1.5 text-xs bg-muted/50 hover:bg-muted text-muted-foreground rounded transition-colors"
                >
                  Log out
                </button>
              </div>
            )}
            {/* System Info */}
            <div className="text-sm text-muted-foreground">
              <p>Market Pie5 Bot</p>
              <p className="text-xs mt-1">v1.0.0</p>
            </div>
          </div>
        )}
      </div>

      {/* Self-Test Panel Modal */}
      <SelfTestPanel
        isOpen={showTestPanel}
        onClose={() => setShowTestPanel(false)}
        currentStatus={selfTestPassed}
        passedCount={health?.self_test?.passed_count}
        totalCount={health?.self_test?.total}
        botRunning={botStatus?.running ?? false}
      />
      {/* Fail Details Popup */}
      <FailDetailsPopup isOpen={showFailDetails} onClose={() => setShowFailDetails(false)} />
    </aside>
  )
}
