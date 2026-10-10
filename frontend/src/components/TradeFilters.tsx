import { useState } from 'react'

export interface TradeFilterValues {
  symbol?: string
  side?: 'long' | 'short'
  status?: 'open' | 'closed'
}
interface TradeFiltersProps {
  filters: TradeFilterValues
  onFilterChange: (filters: TradeFilterValues) => void
}

export default function TradeFilters({ filters, onFilterChange }: TradeFiltersProps) {
  const [localFilters, setLocalFilters] = useState(filters)

  const handleChange = (key: keyof TradeFilterValues, value: string) => {
    const newFilters = {
      ...localFilters,
      [key]: value === '' ? undefined : value,
    }
    setLocalFilters(newFilters)
    onFilterChange(newFilters)
  }

  const clearFilters = () => {
    const cleared: TradeFilterValues = {}
    setLocalFilters(cleared)
    onFilterChange(cleared)
  }

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex-1 min-w-[200px]">
          <label className="block text-sm font-medium mb-2">Symbol</label>
          <input
            type="text"
            placeholder="Filter by symbol (e.g., AAPL)"
            value={localFilters.symbol || ''}
            onChange={(e) => handleChange('symbol', e.target.value)}
            className="w-full px-3 py-2 bg-background border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <div className="min-w-[150px]">
          <label className="block text-sm font-medium mb-2">Side</label>
          <select
            value={localFilters.side || ''}
            onChange={(e) => handleChange('side', e.target.value)}
            className="w-full px-3 py-2 bg-background border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">All</option>
            <option value="long">Long</option>
            <option value="short">Short</option>
          </select>
        </div>

        <div className="min-w-[150px]">
          <label className="block text-sm font-medium mb-2">Status</label>
          <select
            value={localFilters.status || ''}
            onChange={(e) => handleChange('status', e.target.value)}
            className="w-full px-3 py-2 bg-background border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">All</option>
            <option value="open">Open</option>
            <option value="closed">Closed</option>
          </select>
        </div>

        <div className="flex items-end">
          <button
            onClick={clearFilters}
            className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Clear Filters
          </button>
        </div>
      </div>
    </div>
  )
}
