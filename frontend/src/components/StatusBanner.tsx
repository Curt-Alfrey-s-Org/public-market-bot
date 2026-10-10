import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useBotStatus } from '@/hooks/useBotStatus'
import { settingsApi, Settings } from '@/api/settings'

export default function StatusBanner() {
  const { data: status, isError } = useBotStatus()
  const { data: settings } = useQuery<Settings>({
    queryKey: ['settings'],
    queryFn: settingsApi.getSettings,
    staleTime: 0,
    gcTime: 0,
    refetchOnMount: true,
    refetchOnWindowFocus: false,
  })

  const isRunning = !!status?.running
  const isOffline = isError && !status
  const mode = status?.mode || 'unknown'
  const modeLabel = (mode === 'dryrun-live' || mode === 'dry_run')
    ? 'Dry Run Live'
    : (mode === 'yfinance' ? 'YFinance' : (mode ? mode.charAt(0).toUpperCase() + mode.slice(1) : 'Unknown'))

  const mlEnabled = (settings as Settings | undefined)?.ENABLE_ML_SIGNAL_FILTER === 'true'
  const capital = (settings as Settings | undefined)?.BOT_TOTAL_CAPITAL
  const capitalLabel = useMemo(() => {
    if (!capital) return '—'
    try {
      const n = typeof capital === 'string' ? parseFloat(capital) : capital
      return n.toLocaleString(undefined, { maximumFractionDigits: 0 })
    } catch {
      return String(capital)
    }
  }, [capital])

  return (
    <div className="mb-4 sm:mb-6 bg-card border border-border rounded-lg p-3 sm:p-4" role="status" aria-live="polite">
      {/* API Offline Banner */}
      {isOffline && (
        <div className="mb-3 flex items-center justify-between bg-destructive/10 border border-destructive rounded p-2">
          <div className="text-xs sm:text-sm text-destructive">
            API Offline — start the API on the server and refresh.
          </div>
          <a
            href="https://github.com/"
            target="_blank"
            rel="noreferrer"
            className="text-xs sm:text-sm underline"
          >
            View start instructions
          </a>
        </div>
      )}
      <div className="flex flex-wrap items-center gap-3 sm:gap-4">
        <div className="flex items-center gap-2 px-2 py-1 bg-muted rounded">
          <span className="text-xs sm:text-sm font-medium">Mode</span>
          <span className="text-xs sm:text-sm font-semibold">{modeLabel}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-3 h-3 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></span>
          <span className="text-xs sm:text-sm font-medium">{isRunning ? 'Running' : 'Stopped'}</span>
        </div>
        <div className="flex items-center gap-2 px-2 py-1 bg-muted rounded">
          <span className="text-xs sm:text-sm">ML Filter</span>
          <span className={`text-xs sm:text-sm font-semibold ${mlEnabled ? 'text-green-400' : 'text-yellow-400'}`}>{mlEnabled ? 'On' : 'Off'}</span>
        </div>
        <div className="flex items-center gap-2 px-2 py-1 bg-muted rounded">
          <span className="text-xs sm:text-sm">Capital</span>
          <span className="text-xs sm:text-sm font-semibold">${capitalLabel}</span>
        </div>
      </div>
    </div>
  )
}
