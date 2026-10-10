import { useState, memo, useCallback, useMemo } from 'react'

interface PriceChartProps {
  symbol: string
  height?: number
}

function PriceChart({ symbol, height = 400 }: PriceChartProps) {
  const [timeframe, setTimeframe] = useState<'1D' | '1W' | '1M' | '3M'>('1D')

  // Memoize chart data calculation to avoid recalculation on every render
  const chartData = useMemo(() => [
    { time: '09:30', price: 150.0 },
    { time: '10:00', price: 151.5 },
    { time: '10:30', price: 150.8 },
    { time: '11:00', price: 152.3 },
    { time: '11:30', price: 151.9 },
    { time: '12:00', price: 152.5 },
    { time: '12:30', price: 153.1 },
    { time: '13:00', price: 152.8 },
    { time: '13:30', price: 153.5 },
    { time: '14:00', price: 154.0 },
    { time: '14:30', price: 153.7 },
    { time: '15:00', price: 154.2 },
    { time: '15:30', price: 154.5 },
  ], [symbol, timeframe])

  // Memoize calculations to prevent recalculation
  const { maxPrice, minPrice, range } = useMemo(() => {
    const max = Math.max(...chartData.map(d => d.price))
    const min = Math.min(...chartData.map(d => d.price))
    return {
      maxPrice: max,
      minPrice: min,
      range: (max - min) || 1
    }
  }, [chartData])
  
  // Memoize timeframe handler
  const handleTimeframeChange = useCallback((tf: '1D' | '1W' | '1M' | '3M') => {
    setTimeframe(tf)
  }, [])

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">{symbol}</h3>
          <p className="text-sm text-muted-foreground">Price Chart</p>
        </div>
        <div className="flex gap-2">
          {(['1D', '1W', '1M', '3M'] as const).map((tf) => (
            <button
              key={tf}
              onClick={() => handleTimeframeChange(tf)}
              className={`px-3 py-1 text-sm rounded transition-colors ${
                timeframe === tf
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted hover:bg-accent'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      <div className="relative" style={{ height: `${height}px` }}>
        <svg width="100%" height={height} className="overflow-visible">
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
            <line
              key={ratio}
              x1="0"
              y1={ratio * height}
              x2="100%"
              y2={ratio * height}
              stroke="currentColor"
              strokeOpacity={0.1}
              strokeWidth={1}
            />
          ))}

          {/* Price line */}
          <polyline
            points={chartData
              .map((d, i) => {
                const x = (i / (chartData.length - 1)) * 100
                const y = height - ((d.price - minPrice) / range) * height
                return `${x}%,${y}`
              })
              .join(' ')}
            fill="none"
            stroke="hsl(var(--primary))"
            strokeWidth={2}
          />

          {/* Data points */}
          {chartData.map((d, i) => {
            const x = (i / (chartData.length - 1)) * 100
            const y = height - ((d.price - minPrice) / range) * height
            return (
              <circle
                key={i}
                cx={`${x}%`}
                cy={y}
                r={3}
                fill="hsl(var(--primary))"
              />
            )
          })}
        </svg>

        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between text-xs text-muted-foreground px-2">
          <span>${maxPrice.toFixed(2)}</span>
          <span>${minPrice.toFixed(2)}</span>
        </div>

        {/* X-axis labels */}
        <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-muted-foreground px-2 pb-2">
          <span>{chartData[0].time}</span>
          <span>{chartData[Math.floor(chartData.length / 2)].time}</span>
          <span>{chartData[chartData.length - 1].time}</span>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm">
        <div>
          <span className="text-muted-foreground">Current: </span>
          <span className="font-semibold">
            ${chartData[chartData.length - 1].price.toFixed(2)}
          </span>
        </div>
        <div className="flex gap-4">
          <div>
            <span className="text-muted-foreground">High: </span>
            <span className="text-green-600">${maxPrice.toFixed(2)}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Low: </span>
            <span className="text-red-600">${minPrice.toFixed(2)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

// Export memoized component to prevent unnecessary re-renders
export default memo(PriceChart)
