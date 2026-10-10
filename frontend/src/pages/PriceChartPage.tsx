import { useState } from 'react'
import PriceChart from '@/components/PriceChart'

export default function PriceChartPage() {
  const [symbol, setSymbol] = useState('AAPL')

  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Price Charts</h1>
            <p className="text-muted-foreground mt-1">
              View price charts for any symbol
            </p>
          </div>
          <div className="flex items-center gap-4">
            <input
              type="text"
              placeholder="Enter symbol (e.g., AAPL)"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="px-4 py-2 bg-background border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <button
              onClick={() => {
                // In production, this would fetch new chart data
              }}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              Load Chart
            </button>
          </div>
        </div>

        {/* Price Chart */}
        <PriceChart symbol={symbol} />
      </div>
    </div>
  )
}
