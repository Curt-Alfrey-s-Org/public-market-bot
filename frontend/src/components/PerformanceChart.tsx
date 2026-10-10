import { useQuery } from '@tanstack/react-query'
import { statsApi } from '@/api/stats'
import { useMemo, useState, useEffect, memo, useCallback } from 'react'
import { useBotStatus } from '@/hooks/useBotStatus'

const MAX_POINTS = 60

interface PerformanceChartProps {
  type: 'equity' | 'pnl'
  height?: number
}

function PerformanceChart({ type, height = 300 }: PerformanceChartProps) {
  const { data: botStatus } = useBotStatus()
  const { data: stats, isLoading, error, dataUpdatedAt } = useQuery({
    queryKey: ['stats'],
    queryFn: statsApi.getStats,
    refetchInterval: 5000,
    retry: 1,
    retryDelay: 1000,
    staleTime: 500,
  })
  const [series, setSeries] = useState<{ date: Date; value: number }[]>([])

  // Memoize series update logic
  const handleStatsUpdate = useCallback(() => {
    if (!stats) return
    const now = new Date()
    const raw = type === 'equity' ? stats.capital : stats.total_pnl
    const value = typeof raw === 'number' && Number.isFinite(raw) ? raw : 0
    setSeries((prev) => [...prev, { date: now, value }].slice(-MAX_POINTS))
  }, [stats, type])

  // Append a point on every stats refetch so the curve updates even when values are unchanged
  useEffect(() => {
    handleStatsUpdate()
  }, [dataUpdatedAt, handleStatsUpdate])

  const chartData = useMemo(() => {
    if (series.length > 0) return series
    if (stats) {
      const raw = type === 'equity' ? stats.capital : stats.total_pnl
      const value = typeof raw === 'number' && Number.isFinite(raw) ? raw : 0
      return [{ date: new Date(), value }]
    }
    return []
  }, [series, stats, type])

  if (isLoading) {
    return (
      <div className="w-full rounded-lg p-4 sm:p-6 flex items-center justify-center min-h-[250px] sm:min-h-[300px]">
        <p className="text-muted-foreground">Loading chart data...</p>
      </div>
    )
  }

  // Show empty state instead of error messages
  if (error) {
    return (
      <div className="w-full rounded-lg p-4 sm:p-6 flex items-center justify-center min-h-[250px] sm:min-h-[300px]">
        <p className="text-muted-foreground">No chart data available</p>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="w-full rounded-lg p-4 sm:p-6 flex items-center justify-center min-h-[250px] sm:min-h-[300px]">
        <p className="text-muted-foreground">No data available</p>
      </div>
    )
  }

  const divisor = Math.max(1, chartData.length - 1)
  const values = chartData.map((d) => (typeof d.value === 'number' && Number.isFinite(d.value) ? d.value : 0))
  const maxValue = values.length ? Math.max(...values) : 0
  const minValue = values.length ? Math.min(...values) : 0
  const range = maxValue - minValue || 1
  const chartHeight = height || 300

  return (
    <div className="w-full flex flex-col h-full" key={`chart-${type}-${chartData.length}`}>
      <div className="flex items-center justify-between mb-3 sm:mb-4">
        <h3 className="text-base sm:text-lg font-semibold">
          {type === 'equity' ? 'Equity Curve' : 'P&L Trend'}
        </h3>
        <span className="text-xs text-muted-foreground">{chartData.length} point{chartData.length !== 1 ? 's' : ''}</span>
      </div>
      <div className="relative flex-grow min-h-[250px] sm:min-h-[300px]">
        <svg width="100%" height={chartHeight} className="overflow-visible">
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
            <line
              key={ratio}
              x1="0"
              y1={ratio * chartHeight}
              x2="100%"
              y2={ratio * chartHeight}
              stroke="currentColor"
              strokeOpacity={0.1}
              strokeWidth={1}
            />
          ))}
          
          {/* Chart line - key so React updates when points change */}
          <polyline
            key={`line-${chartData.length}-${chartData[chartData.length - 1]?.value ?? 0}`}
            points={chartData
              .map((d, i) => {
                const x = (i / divisor) * 100
                const y = chartHeight - ((d.value - minValue) / range) * chartHeight
                return `${x}%,${y}`
              })
              .join(' ')}
            fill="none"
            stroke="hsl(var(--primary))"
            strokeWidth={2}
          />
          
          {/* Area fill */}
          <polygon
            points={`0,${chartHeight} ${chartData
              .map((d, i) => {
                const x = (i / divisor) * 100
                const y = chartHeight - ((d.value - minValue) / range) * chartHeight
                return `${x}%,${y}`
              })
              .join(' ')} 100%,${chartHeight}`}
            fill="hsl(var(--primary))"
            fillOpacity={0.1}
          />
        </svg>
        
        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between text-xs text-muted-foreground px-1 sm:px-2">
          <span>{type === 'equity' ? `$${Number(maxValue).toFixed(0)}` : `+$${Number(maxValue).toFixed(0)}`}</span>
          <span>{type === 'equity' ? `$${Number(minValue).toFixed(0)}` : `-$${Math.abs(Number(minValue)).toFixed(0)}`}</span>
        </div>
      </div>
      
      <p className="text-xs text-muted-foreground mt-2 sm:mt-3 text-center">
        {type === 'equity' 
          ? `Current Capital: $${(Number(stats.capital) || 0).toFixed(2)}`
          : `Total P&L: $${(Number(stats.total_pnl) || 0).toFixed(2)}`}
      </p>
    </div>
  )
}

// Export memoized component to prevent unnecessary re-renders
export default memo(PerformanceChart)
