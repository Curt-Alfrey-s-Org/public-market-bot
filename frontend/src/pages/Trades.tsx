import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { tradesApi, Trade } from '@/api/trades'
import TradeTable from '@/components/TradeTable'
import TradeFilters from '@/components/TradeFilters'
import TradeDetailsModal from '@/components/TradeDetailsModal'

interface TradesProps {
  sidebarOpen?: boolean
  onSidebarToggle?: () => void
}

export default function Trades({ sidebarOpen: _sidebarOpen, onSidebarToggle }: TradesProps) {
  const [filters, setFilters] = useState<{
    symbol?: string
    side?: 'long' | 'short'
    status?: 'open' | 'closed'
  }>({})
  
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['trades', filters],
    queryFn: () => tradesApi.getTrades({ ...filters, limit: 100 }),
    refetchInterval: 5000, // Refresh every 5 seconds
    retry: 1,
    retryDelay: 1000,
    staleTime: 3000,
  })

  const handleTradeClick = (trade: Trade) => {
    setSelectedTrade(trade)
    setIsModalOpen(true)
  }

  const handleFilterChange = (newFilters: typeof filters) => {
    setFilters(newFilters)
  }

  return (
    <div className="flex flex-col h-screen bg-black/90 text-foreground overflow-hidden">
      {/* Header */}
      <header className="bg-card/50 backdrop-blur-sm border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          {onSidebarToggle && (
            <button
              onClick={onSidebarToggle}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              aria-label="Toggle menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          )}
          <div>
            <h1 className="text-2xl font-bold">Trade Log</h1>
            <p className="text-sm text-muted-foreground">
              View and analyze all trading activity
            </p>
          </div>
        </div>
        {data && (
          <div className="text-sm text-muted-foreground">
            Total: {data.total} trades
          </div>
        )}
      </header>

      {/* Content */}
      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Filters */}
          <TradeFilters filters={filters} onFilterChange={handleFilterChange} />

        {/* Trade Table */}
        {isLoading && (
          <div className="bg-card border border-border rounded-lg p-12 text-center">
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-muted rounded w-3/4 mx-auto"></div>
              <div className="h-4 bg-muted rounded w-1/2 mx-auto"></div>
            </div>
          </div>
        )}

        {/* Show empty state instead of error messages */}
        {error && !isLoading && !data && (
          <div className="bg-card border border-border rounded-lg p-12 text-center">
            <div className="text-muted-foreground">
              <p className="text-lg mb-2">No trades available</p>
              <p className="text-sm">Trades will appear here once the bot is running</p>
            </div>
          </div>
        )}

        {data && !isLoading && (
          <TradeTable
            trades={data.trades}
            onTradeClick={handleTradeClick}
          />
        )}

        {/* Trade Details Modal */}
        {selectedTrade && (
          <TradeDetailsModal
            trade={selectedTrade}
            isOpen={isModalOpen}
            onClose={() => {
              setIsModalOpen(false)
              setSelectedTrade(null)
            }}
          />
        )}
        </div>
      </main>
    </div>
  )
}
