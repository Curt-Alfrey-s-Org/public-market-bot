import { Trade } from '@/api/trades'

interface TradeDetailsModalProps {
  trade: Trade
  isOpen: boolean
  onClose: () => void
}

export default function TradeDetailsModal({ trade, isOpen, onClose }: TradeDetailsModalProps) {
  if (!isOpen) return null

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value)
  }

  const calculateHoldDuration = () => {
    if (!trade.exit_timestamp) return null
    const entry = new Date(trade.entry_timestamp)
    const exit = new Date(trade.exit_timestamp)
    const diff = exit.getTime() - entry.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    return `${days}d ${hours}h ${minutes}m`
  }

  const isPositive = trade.pnl !== undefined && trade.pnl > 0
  const isNegative = trade.pnl !== undefined && trade.pnl < 0

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-card border border-border rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div>
            <h2 className="text-2xl font-bold">{trade.symbol}</h2>
            <p className="text-sm text-muted-foreground mt-1">Trade Details</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-accent rounded-lg transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Status Badge */}
          <div className="flex items-center gap-4">
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${
                trade.status === 'open'
                  ? 'bg-blue-500/20 text-blue-600'
                  : 'bg-gray-500/20 text-gray-600'
              }`}
            >
              {trade.status.toUpperCase()}
            </span>
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${
                trade.side === 'long'
                  ? 'bg-green-500/20 text-green-600'
                  : 'bg-red-500/20 text-red-600'
              }`}
            >
              {trade.side.toUpperCase()}
            </span>
          </div>

          {/* Trade Information */}
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Entry Price</h3>
              <p className="text-lg font-semibold">{formatCurrency(trade.entry_price)}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Exit Price</h3>
              <p className="text-lg font-semibold">
                {trade.exit_price ? formatCurrency(trade.exit_price) : '-'}
              </p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Quantity</h3>
              <p className="text-lg font-semibold">{trade.quantity}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">P&L</h3>
              <p
                className={`text-lg font-semibold ${
                  isPositive
                    ? 'text-green-600'
                    : isNegative
                    ? 'text-red-600'
                    : 'text-muted-foreground'
                }`}
              >
                {trade.pnl !== undefined
                  ? `${isPositive ? '+' : ''}${formatCurrency(trade.pnl)}`
                  : '-'}
              </p>
            </div>
          </div>

          {/* Timestamps */}
          <div className="border-t border-border pt-6 space-y-4">
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Entry Time</h3>
              <p className="text-sm">{formatDate(trade.entry_timestamp)}</p>
            </div>
            {trade.exit_timestamp && (
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Exit Time</h3>
                <p className="text-sm">{formatDate(trade.exit_timestamp)}</p>
              </div>
            )}
            {trade.exit_timestamp && (
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Hold Duration</h3>
                <p className="text-sm font-semibold">{calculateHoldDuration()}</p>
              </div>
            )}
          </div>

          {/* Strategy */}
          {trade.strategy && (
            <div className="border-t border-border pt-6">
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Strategy</h3>
              <p className="text-sm font-semibold">{trade.strategy}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end p-6 border-t border-border">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
