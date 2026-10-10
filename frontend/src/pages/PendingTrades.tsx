import { useQuery } from '@tanstack/react-query'
import { pendingTradesApi, PendingTrade } from '@/api/pendingTrades'
import PendingTradeCard from '@/components/PendingTradeCard'

interface PendingTradesProps {
  sidebarOpen?: boolean
  onSidebarToggle?: () => void
}

export default function PendingTrades({ sidebarOpen: _sidebarOpen, onSidebarToggle }: PendingTradesProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['pending-trades'],
    queryFn: () => pendingTradesApi.getPendingTrades(),
    refetchInterval: 2000, // Refresh every 2 seconds to update countdown
    retry: 1,
    retryDelay: 1000,
    staleTime: 1000,
  })

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
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          )}
          <h1 className="text-2xl font-bold">Pending Trades - Manual Approval</h1>
        </div>
        <div className="text-sm text-muted-foreground">
          {data?.total || 0} pending {data?.total === 1 ? 'trade' : 'trades'}
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 overflow-y-auto p-6">
        {isLoading && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading pending trades...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-600/10 border border-red-600 rounded-lg p-4 mb-4">
            <p className="text-red-500 font-semibold">Error loading pending trades</p>
            <p className="text-sm text-muted-foreground mt-1">
              {error instanceof Error ? error.message : 'Unknown error occurred'}
            </p>
          </div>
        )}

        {!isLoading && !error && (!data || data.pending_trades.length === 0) && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-6xl mb-4">📋</div>
              <h2 className="text-2xl font-bold mb-2">No Pending Trades</h2>
              <p className="text-muted-foreground">
                When manual approval mode is enabled, pending trades will appear here for your review.
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Enable <code className="bg-muted px-2 py-1 rounded">MANUAL_TRADE_APPROVAL_MODE=true</code> in your .env file to use this feature.
              </p>
            </div>
          </div>
        )}

        {!isLoading && !error && data && data.pending_trades.length > 0 && (
          <div className="max-w-6xl mx-auto">
            <div className="mb-4 p-4 bg-blue-600/10 border border-blue-600 rounded-lg">
              <p className="text-sm">
                <strong>Manual Approval Mode Active:</strong> Review each trade below and approve or reject based on the bot's reasoning.
                Trades expire after 5 minutes if not acted upon.
              </p>
            </div>
            
            {data.pending_trades.map((trade: PendingTrade) => (
              <PendingTradeCard key={trade.trade_id} trade={trade} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
