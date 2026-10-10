import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/api/client'
import { toast } from '@/lib/toast'

interface AIPageProps {
  sidebarOpen?: boolean
  onSidebarToggle?: () => void
}

interface LastAnalysis {
  status: 'success' | 'error'
  response?: string
  error?: string
  total_trades?: number
  win_rate?: number
}

export default function AIPage({ sidebarOpen: _sidebarOpen, onSidebarToggle }: AIPageProps) {
  const queryClient = useQueryClient()
  const [lastAnalysis, setLastAnalysis] = useState<LastAnalysis | null>(null)

  // Fetch AI performance summary
  const { data: aiSummary, isLoading } = useQuery({
    queryKey: ['ai-summary'],
    queryFn: async () => {
      const response = await apiClient.get('/api/ai/summary')
      return response.data
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const totalTrades = aiSummary?.total_trades ?? 0
  const canRequestAnalysis = totalTrades >= 10

  const requestMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/api/ai/request')
      return response.data as LastAnalysis
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['ai-summary'] })
      setLastAnalysis({
        status: data.status === 'success' ? 'success' : 'error',
        response: data.response,
        error: data.error,
        total_trades: data.total_trades,
        win_rate: data.win_rate,
      })
      if (data.status === 'success') toast.success('AI analysis complete')
      else toast.error(data.error || 'AI analysis failed')
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail ?? err?.message ?? 'Request failed'
      setLastAnalysis({ status: 'error', error: String(detail) })
      toast.error(detail)
    },
  })

  const handleRequest = () => {
    if (!canRequestAnalysis) return
    requestMutation.mutate()
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
            <h1 className="text-2xl font-bold">AI Assistant</h1>
            <p className="text-sm text-muted-foreground">
              Factual performance narratives (LLM) and backtest-driven parameter suggestions
            </p>
          </div>
        </div>
        <button
          onClick={handleRequest}
          disabled={!canRequestAnalysis || requestMutation.isPending}
          className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold"
          title={!canRequestAnalysis ? 'Need at least 10 trades. Run bot in yfinance mode first.' : ''}
        >
          {requestMutation.isPending ? 'Analyzing...' : 'Request AI Analysis'}
        </button>
      </header>

      {/* Content */}
      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-7xl mx-auto space-y-6">

        {/* AI Summary */}
        {isLoading && (
          <div className="bg-card border border-border rounded-lg p-12 text-center">
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-muted rounded w-3/4 mx-auto"></div>
              <div className="h-4 bg-muted rounded w-1/2 mx-auto"></div>
            </div>
          </div>
        )}

        {aiSummary && (
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Performance Summary</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Win Rate</p>
                  <p className="text-2xl font-bold">{aiSummary.win_rate?.toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Trades</p>
                  <p className="text-2xl font-bold">{aiSummary.total_trades || 0}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total P&L</p>
                  <p className="text-2xl font-bold">
                    ${aiSummary.total_pnl?.toFixed(2) || '0.00'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Performance narrative</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Plain-English summary of your stats. Does not change bot settings. Parameter tuning uses backtest heuristics, not the LLM.
          </p>
          <div className="space-y-4">
            {lastAnalysis?.status === 'success' && lastAnalysis.response ? (
              <div className="rounded-lg bg-muted/50 p-4 text-sm whitespace-pre-wrap">
                {lastAnalysis.response}
              </div>
            ) : lastAnalysis?.status === 'error' && lastAnalysis.error ? (
              <div className="rounded-lg bg-destructive/10 text-destructive p-4">
                {lastAnalysis.error}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <p>Click &quot;Request AI Analysis&quot; for a factual performance narrative</p>
                <p className="text-sm mt-2">Requires ALFa AI brain (LiteLLM) when insights are enabled</p>
              </div>
            )}
          </div>
        </div>

        {/* Minimum Trades Warning */}
        {aiSummary && totalTrades < 10 && (
          <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <span className="text-yellow-600">⚠️</span>
              <p className="text-sm">
                Minimum 10 trades required for AI analysis. Current: {totalTrades} trades. Run the bot in <strong>yfinance</strong> mode, then Start, to collect trade data.
              </p>
            </div>
          </div>
        )}
        </div>
      </main>
    </div>
  )
}
