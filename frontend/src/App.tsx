import { useEffect, useState, lazy, Suspense } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import VideoBackground from './components/VideoBackground'
import SplashScreen from './components/SplashScreen'
import BackgroundControls from './components/BackgroundControls'
import Sidebar from './components/Sidebar'
import ConnectionStatus from './components/ConnectionStatus'
import BotControls from './components/BotControls'
import ErrorBoundary from './components/ErrorBoundary'
import NetworkErrorHandler from './components/NetworkErrorHandler'
import PageLoader from './components/PageLoader'
import PageErrorFallback from './components/PageErrorFallback'
import { AuthProvider } from './context/AuthContext'
import { AlfaWidgetShell } from './components/AlfaWidgetShell'
import { getAppearance, setAppearance as saveAppearance } from './lib/appearance'
import './App.css'

// Lazy-loaded pages (code splitting)
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Trades = lazy(() => import('./pages/Trades'))
const Settings = lazy(() => import('./pages/Settings'))
const System = lazy(() => import('./pages/System'))
const UserSettings = lazy(() => import('./features/admin').then((m) => ({ default: m.UserSettings })))
const HealthDashboard = lazy(() => import('./features/admin').then((m) => ({ default: m.HealthDashboard })))
const AI = lazy(() => import('./pages/AI'))
const TaxReports = lazy(() => import('./pages/TaxReports'))
const DecisionReport = lazy(() => import('./pages/DecisionReport'))
const Logs = lazy(() => import('./pages/Logs'))
const PendingTrades = lazy(() => import('./pages/PendingTrades'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const VerifyEmailPage = lazy(() => import('./pages/VerifyEmailPage'))
const AIMonitor = lazy(() => import('./pages/SettingsInternalAIMonitor'))
const AlfaChatPopupPage = lazy(() => import('./pages/AlfaChatPopupPage'))

// Create a client for React Query with better error handling
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: (failureCount, error: any) => {
        // Don't retry on network errors (API not available)
        if (!error.response && (error.code === 'ECONNABORTED' || error.message?.includes('Network'))) {
          return false
        }
        // Retry up to 1 time for other errors
        return failureCount < 1
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
      staleTime: 5000,
      gcTime: 10000,
      refetchInterval: false, // Disable auto-refetch by default, let components set it
      // Prevent errors from causing crashes
      throwOnError: false,
    },
    mutations: {
      // Don't retry mutations on network errors
      retry: (failureCount, error: any) => {
        if (!error.response && (error.code === 'ECONNABORTED' || error.message?.includes('Network'))) {
          return false
        }
        return failureCount < 1
      },
      throwOnError: false,
    },
  },
})

function AppRoutes() {
  const location = useLocation()
  const [showSplash, setShowSplash] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    // Start closed on mobile/tablet, open on desktop
    if (typeof window !== 'undefined') {
      return window.innerWidth >= 768
    }
    return true
  })
  const [videoEnabled, setVideoEnabled] = useState(true)
  const [videoOpacity, setVideoOpacity] = useState(0.4)
  const [appearance, setAppearance] = useState(getAppearance)

  // Refresh appearance when changed from Settings (custom event)
  useEffect(() => {
    const onAppearanceChange = () => setAppearance(getAppearance())
    window.addEventListener('appearance-changed', onAppearanceChange)
    return () => window.removeEventListener('appearance-changed', onAppearanceChange)
  }, [])

  // Enable dark mode by default
  useEffect(() => {
    document.documentElement.classList.add('dark')
    document.body.classList.add('dark')
  }, [])

  // Load opacity/enabled from localStorage (position/scale/fit live in appearance)
  useEffect(() => {
    const savedEnabled = localStorage.getItem('videoBackgroundEnabled')
    const savedOpacity = localStorage.getItem('videoBackgroundOpacity')
    if (savedEnabled !== null) setVideoEnabled(savedEnabled === 'true')
    if (savedOpacity !== null) setVideoOpacity(parseFloat(savedOpacity))
  }, [])

  useEffect(() => {
    localStorage.setItem('videoBackgroundEnabled', videoEnabled.toString())
  }, [videoEnabled])

  useEffect(() => {
    localStorage.setItem('videoBackgroundOpacity', videoOpacity.toString())
  }, [videoOpacity])

  // When user logs out, show splash/login again
  useEffect(() => {
    const onLogout = () => setShowSplash(true)
    window.addEventListener('auth-logout', onLogout)
    return () => window.removeEventListener('auth-logout', onLogout)
  }, [])

  if (location.pathname === '/alfa-chat') {
    return (
      <Suspense fallback={<PageLoader />}>
        <AlfaChatPopupPage />
      </Suspense>
    )
  }

  const bgPosX = appearance.backgroundPositionX ?? 0
  const bgPosY = appearance.backgroundPositionY ?? 0
  const bgScale = appearance.backgroundScale ?? 1
  const bgObjectFit = (appearance.backgroundObjectFit ?? 'cover') as 'cover' | 'contain' | 'fill' | 'none' | 'scale-down'

  const handleBackgroundPositionChange = (x: number, y: number) => {
    saveAppearance({ backgroundPositionX: x, backgroundPositionY: y })
  }
  const handleBackgroundScaleChange = (s: number) => {
    saveAppearance({ backgroundScale: s })
  }
  const handleBackgroundObjectFitChange = (fit: 'cover' | 'contain' | 'fill' | 'none' | 'scale-down') => {
    saveAppearance({ backgroundObjectFit: fit })
  }

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
                {/* Auth routes: register, verify-email, or splash (login) */}
        {showSplash && (
          <Routes>
            <Route path="/register" element={<Suspense fallback={<PageLoader />}><RegisterPage /></Suspense>} />
            <Route path="/verify-email" element={<Suspense fallback={<PageLoader />}><VerifyEmailPage /></Suspense>} />
            <Route path="*" element={
              <SplashScreen
                splashUrl={appearance.splashUrl}
                splashType={appearance.splashType}
                onEnter={() => setShowSplash(false)}
              />
            } />
          </Routes>
        )}

        {/* Video / Image Background */}
        {!showSplash && (
          <>
            <VideoBackground
              backgroundUrl={appearance.backgroundUrl}
              backgroundType={appearance.backgroundType}
              enabled={videoEnabled}
              opacity={videoOpacity}
              scale={bgScale}
              objectFit={bgObjectFit}
              positionX={bgPosX}
              positionY={bgPosY}
            />
            
            {/* Background Controls */}
            <BackgroundControls
              opacity={videoOpacity}
              onOpacityChange={setVideoOpacity}
              enabled={videoEnabled}
              onEnabledChange={setVideoEnabled}
              scale={bgScale}
              onScaleChange={handleBackgroundScaleChange}
              objectFit={bgObjectFit}
              onObjectFitChange={handleBackgroundObjectFitChange}
              positionX={bgPosX}
              positionY={bgPosY}
              onPositionChange={handleBackgroundPositionChange}
            />
          </>
        )}
        
        {/* Network Error Handler */}
        {!showSplash && <NetworkErrorHandler />}
        
        {/* Main App - Dark Mode Container */}
        {!showSplash && (
          <AlfaWidgetShell>
          <div className="flex flex-col h-screen bg-slate-950 text-slate-50 overflow-hidden dark">
            {/* Mobile Header */}
            <header className="w-screen md:hidden fixed top-0 left-0 right-0 bg-slate-950 border-b border-slate-800 h-16 flex items-center px-4 z-40 shadow-lg">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 hover:bg-slate-800 text-slate-50 rounded-lg transition-colors flex-shrink-0"
                aria-label="Toggle menu"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                  {sidebarOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
              <div className="flex-1 text-center">
                <h1 className="font-semibold text-sm text-slate-50">Market Bot</h1>
              </div>
              <div className="w-10 flex-shrink-0" />
            </header>

            {/* Main Content Area */}
            <div className="relative z-10 min-h-full flex md:pt-0 pt-16">
              {/* Sidebar */}
              <Sidebar
                isOpen={sidebarOpen}
                onToggle={() => setSidebarOpen(!sidebarOpen)}
                avatarUrl={appearance.avatarUrl}
                avatarNone={appearance.avatarNone}
              />

              {/* Mobile Sidebar Overlay */}
              {sidebarOpen && (
                <div
                  className="md:hidden fixed inset-0 bg-black/50 z-30"
                  onClick={() => setSidebarOpen(false)}
                  style={{ top: '64px' }}
                  aria-hidden="true"
                />
              )}
            
            {/* Page Content */}
            <div
              id="main-content"
              className="flex-1 min-w-0 min-h-0 overflow-hidden transition-all duration-300 main-with-alfa-dock bg-slate-950/95 backdrop-blur-sm"
            >
              <header className="sticky top-16 md:top-0 z-30 bg-card/70 backdrop-blur-sm border-b border-border px-2 sm:px-4 md:px-6 py-2 sm:py-3 flex items-center justify-between gap-2 sm:gap-3 min-h-fit">
                <div className="flex items-center gap-2 sm:gap-3">
                  <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="p-1.5 md:p-2 hover:bg-accent rounded-lg transition-colors flex-shrink-0"
                    aria-label="Toggle menu"
                  >
                    <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
                      {sidebarOpen ? (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      ) : (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                      )}
                    </svg>
                  </button>
                  <div className="hidden sm:block text-xs sm:text-sm font-semibold text-muted-foreground">Bot Controls</div>
                </div>
                <div className="flex items-center gap-2 sm:gap-3 flex-wrap justify-end">
                  <ConnectionStatus />
                  <BotControls />
                </div>
              </header>
              <Routes>
                <Route
                  path="/"
                  element={
                    <ErrorBoundary fallback={<PageErrorFallback />}>
                      <Suspense fallback={<PageLoader />}>
                        <Dashboard sidebarOpen={sidebarOpen} onSidebarToggle={() => setSidebarOpen(!sidebarOpen)} />
                      </Suspense>
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/trades"
                  element={
                    <ErrorBoundary fallback={<PageErrorFallback />}>
                      <Suspense fallback={<PageLoader />}>
                        <Trades sidebarOpen={sidebarOpen} onSidebarToggle={() => setSidebarOpen(!sidebarOpen)} />
                      </Suspense>
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/settings"
                  element={
                    <ErrorBoundary fallback={<PageErrorFallback />}>
                      <Suspense fallback={<PageLoader />}>
                        <Settings sidebarOpen={sidebarOpen} onSidebarToggle={() => setSidebarOpen(!sidebarOpen)} />
                      </Suspense>
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/logs"
                  element={
                    <ErrorBoundary fallback={<PageErrorFallback />}>
                      <Suspense fallback={<PageLoader />}>
                        <Logs sidebarOpen={sidebarOpen} onSidebarToggle={() => setSidebarOpen(!sidebarOpen)} />
                      </Suspense>
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/system"
                  element={
                    <ErrorBoundary fallback={<PageErrorFallback />}>
                      <Suspense fallback={<PageLoader />}>
                        <System sidebarOpen={sidebarOpen} onSidebarToggle={() => setSidebarOpen(!sidebarOpen)} />
                      </Suspense>
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/ai"
                  element={
                    <ErrorBoundary fallback={<PageErrorFallback />}>
                      <Suspense fallback={<PageLoader />}>
                        <AI sidebarOpen={sidebarOpen} onSidebarToggle={() => setSidebarOpen(!sidebarOpen)} />
                      </Suspense>
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/tax"
                  element={
                    <ErrorBoundary fallback={<PageErrorFallback />}>
                      <Suspense fallback={<PageLoader />}>
                        <TaxReports sidebarOpen={sidebarOpen} onSidebarToggle={() => setSidebarOpen(!sidebarOpen)} />
                      </Suspense>
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/reports/decisions"
                  element={
                    <ErrorBoundary fallback={<PageErrorFallback />}>
                      <Suspense fallback={<PageLoader />}>
                        <DecisionReport sidebarOpen={sidebarOpen} onSidebarToggle={() => setSidebarOpen(!sidebarOpen)} />
                      </Suspense>
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/pending-trades"
                  element={
                    <ErrorBoundary fallback={<PageErrorFallback />}>
                      <Suspense fallback={<PageLoader />}>
                        <PendingTrades sidebarOpen={sidebarOpen} onSidebarToggle={() => setSidebarOpen(!sidebarOpen)} />
                      </Suspense>
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/admin/health"
                  element={
                    <ErrorBoundary fallback={<PageErrorFallback />}>
                      <Suspense fallback={<PageLoader />}>
                        <HealthDashboard />
                      </Suspense>
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/admin/user-settings"
                  element={
                    <ErrorBoundary fallback={<PageErrorFallback />}>
                      <Suspense fallback={<PageLoader />}>
                        <UserSettings />
                      </Suspense>
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/admin/ai-monitor"
                  element={
                    <ErrorBoundary fallback={<PageErrorFallback />}>
                      <Suspense fallback={<PageLoader />}>
                        <AIMonitor />
                      </Suspense>
                    </ErrorBoundary>
                  }
                />
              </Routes>
              </div>
            </div>
          </div>
          </AlfaWidgetShell>
        )}
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}

export default App
