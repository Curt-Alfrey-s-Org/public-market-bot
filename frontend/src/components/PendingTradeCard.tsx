import { useState } from 'react'
import { PendingTrade } from '@/api/pendingTrades'
import { pendingTradesApi } from '@/api/pendingTrades'
import { useQueryClient } from '@tanstack/react-query'

interface PendingTradeCardProps {
  trade: PendingTrade
}

export default function PendingTradeCard({ trade }: PendingTradeCardProps) {
  const [isProcessing, setIsProcessing] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [showRejectInput, setShowRejectInput] = useState(false)
  const queryClient = useQueryClient()

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value)
  }

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(2)}%`
  }

  const getTimeRemaining = () => {
    const expiresAt = new Date(trade.expires_at)
    const now = new Date()
    const diff = expiresAt.getTime() - now.getTime()
    
    if (diff <= 0) return 'Expired'
    
    const minutes = Math.floor(diff / 60000)
    const seconds = Math.floor((diff % 60000) / 1000)
    return `${minutes}m ${seconds}s`
  }

  const handleApprove = async () => {
    setIsProcessing(true)
    try {
      await pendingTradesApi.approveTrade(trade.trade_id)
      queryClient.invalidateQueries({ queryKey: ['pending-trades'] })
    } catch (error) {
      console.error('Error approving trade:', error)
      alert('Failed to approve trade. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleReject = async () => {
    if (showRejectInput && !rejectReason.trim()) {
      alert('Please provide a reason for rejection')
      return
    }
    
    setIsProcessing(true)
    try {
      await pendingTradesApi.rejectTrade(trade.trade_id, rejectReason || undefined)
      queryClient.invalidateQueries({ queryKey: ['pending-trades'] })
      setShowRejectInput(false)
      setRejectReason('')
    } catch (error) {
      console.error('Error rejecting trade:', error)
      alert('Failed to reject trade. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }

  const reasoning = trade.reasoning
  const autoMode = trade.auto_mode_details

  return (
    <div className="bg-card border border-border rounded-lg p-6 mb-4 shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-4 border-b border-border">
        <div>
          <h3 className="text-xl font-bold text-foreground">
            {trade.action} {trade.symbol}
          </h3>
          <p className="text-sm text-muted-foreground">
            Trade ID: {trade.trade_id}
          </p>
        </div>
        <div className="text-right">
          <div className="text-sm text-muted-foreground">Expires in</div>
          <div className="text-lg font-bold text-warning">{getTimeRemaining()}</div>
        </div>
      </div>

      {/* Trade Details */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div>
          <div className="text-sm text-muted-foreground">Price</div>
          <div className="text-lg font-semibold">{formatCurrency(trade.price)}</div>
        </div>
        <div>
          <div className="text-sm text-muted-foreground">Quantity</div>
          <div className="text-lg font-semibold">{trade.quantity.toFixed(4)}</div>
        </div>
        <div>
          <div className="text-sm text-muted-foreground">Allocation</div>
          <div className="text-lg font-semibold">{formatCurrency(trade.allocation)}</div>
        </div>
        <div>
          <div className="text-sm text-muted-foreground">Total Value</div>
          <div className="text-lg font-semibold">
            {formatCurrency(trade.price * trade.quantity)}
          </div>
        </div>
      </div>

      {/* Auto Mode Decision */}
      <div className={`mb-4 p-4 rounded-lg border ${
        autoMode.would_execute 
          ? 'bg-green-600/10 border-green-600' 
          : 'bg-red-600/10 border-red-600'
      }`}>
        <div className="flex items-center gap-2 mb-2">
          <span className="font-bold">Auto Mode Decision:</span>
          <span className={`font-bold ${
            autoMode.would_execute ? 'text-green-500' : 'text-red-500'
          }`}>
            {autoMode.decision}
          </span>
        </div>
        <div className="text-sm text-muted-foreground">
          {autoMode.reasons.length > 0 ? (
            <ul className="list-disc list-inside">
              {autoMode.reasons.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          ) : (
            'No specific reasons provided'
          )}
        </div>
      </div>

      {/* Reasoning Breakdown */}
      <div className="mb-4 space-y-3">
        {/* Strategy Signals */}
        {reasoning.strategy_signals && Object.keys(reasoning.strategy_signals).length > 0 && (
          <div className="p-3 bg-muted/50 rounded">
            <div className="font-semibold mb-1">Strategy Signals</div>
            <div className="text-sm">
              <div>Combined Signal: <span className="font-semibold">{reasoning.strategy_signals.combined_signal || 'N/A'}</span></div>
              {reasoning.strategy_signals.signal_strength !== undefined && (
                <div>Signal Strength: {formatPercent(reasoning.strategy_signals.signal_strength)}</div>
              )}
            </div>
          </div>
        )}

        {/* ML Filter */}
        {reasoning.ml_filter && Object.keys(reasoning.ml_filter).length > 0 && (
          <div className="p-3 bg-muted/50 rounded">
            <div className="font-semibold mb-1">ML Filter</div>
            <div className="text-sm">
              <div>Recommendation: <span className={`font-semibold ${
                reasoning.ml_filter.recommendation === 'ACCEPT' ? 'text-success' : 'text-destructive'
              }`}>{reasoning.ml_filter.recommendation || 'N/A'}</span></div>
              {reasoning.ml_filter.confidence !== undefined && (
                <div>Confidence: {formatPercent(reasoning.ml_filter.confidence)}</div>
              )}
              {reasoning.ml_filter.win_probability !== undefined && (
                <div>Win Probability: {formatPercent(reasoning.ml_filter.win_probability)}</div>
              )}
            </div>
          </div>
        )}

        {/* Risk Analysis */}
        {reasoning.risk_analysis && Object.keys(reasoning.risk_analysis).length > 0 && (
          <div className="p-3 bg-muted/50 rounded">
            <div className="font-semibold mb-1">Risk Analysis</div>
            <div className="text-sm">
              <div>Risk Assessment: <span className={`font-semibold ${
                reasoning.risk_analysis.risk_assessment === 'LOW' ? 'text-green-500' :
                reasoning.risk_analysis.risk_assessment === 'MEDIUM' ? 'text-yellow-500' : 'text-red-500'
              }`}>{reasoning.risk_analysis.risk_assessment || 'N/A'}</span></div>
              {reasoning.risk_analysis.potential_loss !== undefined && (
                <div>Potential Loss: {formatCurrency(reasoning.risk_analysis.potential_loss)}</div>
              )}
              {reasoning.risk_analysis.within_risk_limit !== undefined && (
                <div>Within Risk Limit: <span className={reasoning.risk_analysis.within_risk_limit ? 'text-green-500' : 'text-red-500'}>
                  {reasoning.risk_analysis.within_risk_limit ? 'Yes' : 'No'}
                </span></div>
              )}
            </div>
          </div>
        )}

        {/* Market Conditions */}
        {reasoning.market_conditions && Object.keys(reasoning.market_conditions).length > 0 && (
          <div className="p-3 bg-muted/50 rounded">
            <div className="font-semibold mb-1">Market Conditions</div>
            <div className="text-sm">
              <div>Volatility: <span className="font-semibold">{reasoning.market_conditions.volatility_assessment || 'N/A'}</span></div>
              <div>Liquidity: <span className="font-semibold">{reasoning.market_conditions.liquidity_assessment || 'N/A'}</span></div>
              {reasoning.market_conditions.volume !== undefined && (
                <div>Volume: {reasoning.market_conditions.volume.toLocaleString()}</div>
              )}
            </div>
          </div>
        )}

        {/* Capital Status */}
        {reasoning.capital_status && Object.keys(reasoning.capital_status).length > 0 && (
          <div className="p-3 bg-muted/50 rounded">
            <div className="font-semibold mb-1">Capital Status</div>
            <div className="text-sm">
              <div>Available Capital: {formatCurrency(reasoning.capital_status.available_capital || 0)}</div>
              <div>Sufficient Capital: <span className={reasoning.capital_status.sufficient_capital ? 'text-success' : 'text-destructive'}>
                {reasoning.capital_status.sufficient_capital ? 'Yes' : 'No'}
              </span></div>
              {reasoning.capital_status.allocation_percentage !== undefined && (
                <div>Allocation: {reasoning.capital_status.allocation_percentage.toFixed(2)}%</div>
              )}
            </div>
          </div>
        )}

        {/* Monthly Progress */}
        {reasoning.monthly_progress && Object.keys(reasoning.monthly_progress).length > 0 && (
          <div className="p-3 bg-muted/50 rounded">
            <div className="font-semibold mb-1">Monthly Progress</div>
            <div className="text-sm">
              <div>Current Return: {reasoning.monthly_progress.current_return?.toFixed(2) || '0.00'}%</div>
              <div>Target Return: {reasoning.monthly_progress.target_return?.toFixed(2) || '0.00'}%</div>
              <div>Days Remaining: {reasoning.monthly_progress.days_remaining || 0}</div>
              <div>On Track: <span className={reasoning.monthly_progress.on_track ? 'text-green-500' : 'text-red-500'}>
                {reasoning.monthly_progress.on_track ? 'Yes' : 'No'}
              </span></div>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 pt-4 border-t border-border">
        <button
          onClick={handleApprove}
          disabled={isProcessing}
          className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? 'Processing...' : 'Approve & Execute'}
        </button>
        {!showRejectInput ? (
          <button
            onClick={() => setShowRejectInput(true)}
            disabled={isProcessing}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Reject
          </button>
        ) : (
          <div className="flex-1 flex gap-2">
            <input
              type="text"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Rejection reason (optional)"
              className="flex-1 px-3 py-2 bg-background border border-border rounded-lg text-foreground"
            />
            <button
              onClick={handleReject}
              disabled={isProcessing}
              className="bg-destructive hover:bg-destructive/90 text-white font-semibold py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Confirm Reject
            </button>
            <button
              onClick={() => {
                setShowRejectInput(false)
                setRejectReason('')
              }}
              className="bg-muted hover:bg-muted/80 text-foreground font-semibold py-2 px-4 rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
