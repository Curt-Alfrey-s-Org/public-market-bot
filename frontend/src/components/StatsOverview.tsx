import { useQuery } from '@tanstack/react-query'
import { statsApi } from '@/api/stats'
import StatCard from './StatCard'
import { useBotStatus } from '@/hooks/useBotStatus'
import { useState, useEffect } from 'react'

export default function StatsOverview() {
  const { data: _botStatus } = useBotStatus()
  const { data: stats, isLoading, error, isError, dataUpdatedAt, isFetching } = useQuery({
    queryKey: ['stats'],
    queryFn: statsApi.getStats,
    refetchInterval: 5000, // Same when running or not; WebSocket "stats" also triggers refetch
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 5000), // Exponential backoff
    staleTime: 500,
    refetchOnWindowFocus: false,
  })
  const [justPulsed, setJustPulsed] = useState(false)
  useEffect(() => {
    if (!dataUpdatedAt) return
    setJustPulsed(true)
    const t = setTimeout(() => setJustPulsed(false), 400)
    return () => clearTimeout(t)
  }, [dataUpdatedAt])

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8"></div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4">
          {[1, 2, 3, 4, 5, 6, 7].map((i) => (
            <div key={i} className="rounded-lg p-4 sm:p-6 animate-pulse">
              <div className="h-4 bg-muted rounded w-3/4 mb-4"></div>
              <div className="h-8 bg-muted rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Show empty/default state instead of error messages
  if (isError && error) {
    // Show empty state instead of error messages
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4">
          {[1, 2, 3, 4, 5, 6, 7].map((i) => (
            <div key={i} className="rounded-lg p-4 sm:p-6 bg-muted/20 border border-border/50">
              <div className="h-4 bg-muted rounded w-3/4 mb-4"></div>
              <div className="h-8 bg-muted rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!stats) {
    return null
  }

  const lastUpdated = dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : ''

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <h2 className="text-xl sm:text-2xl font-bold">Stats Overview</h2>
        <span className="text-xs text-muted-foreground shrink-0">
          {isFetching ? 'Updating…' : lastUpdated ? `Updated ${lastUpdated}` : ''}
        </span>
      </div>
      <div
        className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4 transition-all duration-300 ${
          justPulsed ? 'ring-2 ring-primary/40 ring-offset-2 ring-offset-background rounded-lg' : ''
        }`}
      >
        <StatCard
          title="Total Capital"
          value={`$${(Number(stats.capital) ?? 0).toFixed(2)}`}
          change={stats.capital_change}
          changePct={stats.capital_change_pct}
          icon="💰"
        />
        <StatCard
          title="Available Capital"
          value={`$${(Number(stats.allocation) ?? 0).toFixed(2)}`}
          icon="💵"
        />
        <StatCard
          title="Win Rate"
          value={`${(Number(stats.win_rate) ?? 0).toFixed(1)}%`}
          icon="🎯"
        />
        <StatCard
          title="Profit Factor"
          value={(Number(stats.profit_factor) ?? 0).toFixed(2)}
          icon="📈"
        />
        <StatCard
          title="Monthly Return"
          value={`${(Number(stats.monthly_return_pct) ?? 0).toFixed(2)}%`}
          change={stats.monthly_return_pct}
          changePct={stats.monthly_return_pct}
          icon="📅"
        />
        <StatCard
          title="Total Trades"
          value={String(stats.total_trades ?? 0)}
          icon="💼"
        />
        <StatCard
          title="Open Positions"
          value={String(stats.open_positions ?? 0)}
          icon="🔓"
        />
      </div>
    </div>
  )
}
