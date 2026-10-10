import { useState, useMemo, memo, useCallback, useDeferredValue } from 'react'
import { Trade } from '@/api/trades'

interface TradeTableProps {
  trades: Trade[]
  onTradeClick: (trade: Trade) => void
}

type SortField = 'symbol' | 'side' | 'entry_price' | 'exit_price' | 'pnl' | 'status' | 'entry_timestamp' | 'exit_timestamp'
type SortDirection = 'asc' | 'desc'

// Memoized row component to prevent unnecessary re-renders
const TradeRow = memo(function TradeRow({
  trade,
  index,
  onTradeClick,
  formatCurrency,
  formatDate,
}: {
  trade: Trade
  index: number
  onTradeClick: (trade: Trade) => void
  formatCurrency: (value: number) => string
  formatDate: (dateString: string) => string
}) {
  const isPositive = trade.pnl !== undefined && trade.pnl > 0
  const isNegative = trade.pnl !== undefined && trade.pnl < 0
  
  return (
    <tr
      onClick={() => onTradeClick(trade)}
      className="hover:bg-accent/50 cursor-pointer transition-colors"
    >
      <td className="px-4 py-3 font-medium">{trade.symbol}</td>
      <td className="px-4 py-3">
        <span
          className={`px-2 py-1 rounded text-xs font-medium ${
            trade.side === 'long'
              ? 'bg-green-500/20 text-green-600'
              : 'bg-red-500/20 text-red-600'
          }`}
        >
          {trade.side.toUpperCase()}
        </span>
      </td>
      <td className="px-4 py-3">{formatCurrency(trade.entry_price)}</td>
      <td className="px-4 py-3">
        {trade.exit_price ? formatCurrency(trade.exit_price) : '-'}
      </td>
      <td className="px-4 py-3">
        {trade.pnl !== undefined ? (
          <span
            className={`font-semibold ${
              isPositive
                ? 'text-green-600'
                : isNegative
                ? 'text-red-600'
                : 'text-muted-foreground'
            }`}
          >
            {isPositive ? '+' : ''}
            {formatCurrency(trade.pnl)}
          </span>
        ) : (
          '-'
        )}
      </td>
      <td className="px-4 py-3">
        <span
          className={`px-2 py-1 rounded text-xs font-medium ${
            trade.status === 'open'
              ? 'bg-blue-500/20 text-blue-600'
              : 'bg-gray-500/20 text-gray-600'
          }`}
        >
          {trade.status.toUpperCase()}
        </span>
      </td>
      <td className="px-4 py-3 text-sm text-muted-foreground">
        {formatDate(trade.entry_timestamp)}
      </td>
    </tr>
  )
})

function TradeTable({ trades, onTradeClick }: TradeTableProps) {
  const [sortField, setSortField] = useState<SortField>('entry_timestamp')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  
  // Use deferred value to debounce sorting updates
  const deferredTrades = useDeferredValue(trades)

  const sortedTrades = useMemo(() => {
    return [...deferredTrades].sort((a, b) => {
      let aValue: any = a[sortField]
      let bValue: any = b[sortField]

      // Handle dates
      if (sortField === 'entry_timestamp' || sortField === 'exit_timestamp') {
        aValue = new Date(aValue || 0).getTime()
        bValue = new Date(bValue || 0).getTime()
      }

      // Handle numbers
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue
      }

      // Handle strings
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue)
      }

      return 0
    })
  }, [deferredTrades, sortField, sortDirection])

  // Memoize handlers to avoid recreating on every render
  const handleSort = useCallback((field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }, [sortField, sortDirection])

  const formatDate = useCallback((dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }, [])

  const formatCurrency = useCallback((value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value)
  }, [])
  
  // Memoize onTradeClick wrapper
  const handleTradeClick = useCallback((trade: Trade) => {
    onTradeClick(trade)
  }, [onTradeClick])

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null
    return sortDirection === 'asc' ? '↑' : '↓'
  }

  if (trades.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-12 text-center">
        <p className="text-muted-foreground">No trades found</p>
      </div>
    )
  }

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr>
              <th
                className="px-4 py-3 text-left text-sm font-semibold cursor-pointer hover:bg-muted transition-colors"
                onClick={() => handleSort('symbol')}
              >
                Symbol <SortIcon field="symbol" />
              </th>
              <th
                className="px-4 py-3 text-left text-sm font-semibold cursor-pointer hover:bg-muted transition-colors"
                onClick={() => handleSort('side')}
              >
                Side <SortIcon field="side" />
              </th>
              <th
                className="px-4 py-3 text-left text-sm font-semibold cursor-pointer hover:bg-muted transition-colors"
                onClick={() => handleSort('entry_price')}
              >
                Entry Price <SortIcon field="entry_price" />
              </th>
              <th
                className="px-4 py-3 text-left text-sm font-semibold cursor-pointer hover:bg-muted transition-colors"
                onClick={() => handleSort('exit_price')}
              >
                Exit Price <SortIcon field="exit_price" />
              </th>
              <th
                className="px-4 py-3 text-left text-sm font-semibold cursor-pointer hover:bg-muted transition-colors"
                onClick={() => handleSort('pnl')}
              >
                P&L <SortIcon field="pnl" />
              </th>
              <th
                className="px-4 py-3 text-left text-sm font-semibold cursor-pointer hover:bg-muted transition-colors"
                onClick={() => handleSort('status')}
              >
                Status <SortIcon field="status" />
              </th>
              <th
                className="px-4 py-3 text-left text-sm font-semibold cursor-pointer hover:bg-muted transition-colors"
                onClick={() => handleSort('entry_timestamp')}
              >
                Entry Time <SortIcon field="entry_timestamp" />
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {sortedTrades.map((trade, index) => (
              <TradeRow
                key={trade.entry_timestamp + trade.symbol}
                trade={trade}
                index={index}
                onTradeClick={handleTradeClick}
                formatCurrency={formatCurrency}
                formatDate={formatDate}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Export memoized component to prevent unnecessary re-renders
export default memo(TradeTable)
