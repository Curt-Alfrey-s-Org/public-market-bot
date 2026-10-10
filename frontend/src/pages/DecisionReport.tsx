import { useState, useMemo, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { reportsApi, type DecisionRow } from '@/api/reports'
import { useBotStatus } from '@/hooks/useBotStatus'

interface DecisionReportProps {
  sidebarOpen?: boolean
  onSidebarToggle?: () => void
}

type SortKey = 'symbol' | 'signal' | 'action' | 'price' | 'volume' | 'reason' | 'cycle_number' | 'updated_at'

const DECISION_REPORT_PREFS_KEY = 'decision_report_preferences'

function loadDecisionReportPrefs(): Partial<{
  filterSymbol: string
  filterSignal: string
  filterAction: string
  filterReason: string
  sortBy: SortKey
  sortOrder: 'asc' | 'desc'
}> {
  try {
    const raw = localStorage.getItem(DECISION_REPORT_PREFS_KEY)
    if (!raw) return {}
    const p = JSON.parse(raw) as Record<string, unknown>
    const validSortKeys: SortKey[] = ['symbol', 'signal', 'action', 'price', 'volume', 'reason', 'cycle_number', 'updated_at']
    return {
      filterSymbol: typeof p.filterSymbol === 'string' ? p.filterSymbol : undefined,
      filterSignal: typeof p.filterSignal === 'string' ? p.filterSignal : undefined,
      filterAction: typeof p.filterAction === 'string' ? p.filterAction : undefined,
      filterReason: typeof p.filterReason === 'string' ? p.filterReason : undefined,
      sortBy: typeof p.sortBy === 'string' && validSortKeys.includes(p.sortBy as SortKey) ? p.sortBy as SortKey : undefined,
      sortOrder: p.sortOrder === 'asc' || p.sortOrder === 'desc' ? p.sortOrder : undefined,
    }
  } catch {
    return {}
  }
}

function saveDecisionReportPrefs(prefs: Record<string, unknown>) {
  try {
    localStorage.setItem(DECISION_REPORT_PREFS_KEY, JSON.stringify(prefs))
  } catch {
    // ignore
  }
}

export default function DecisionReport({ sidebarOpen: _sidebarOpen, onSidebarToggle }: DecisionReportProps) {
  const { data: botStatus } = useBotStatus()
  const isBotRunning = botStatus?.running ?? false

  const [filterSymbol, setFilterSymbol] = useState(() => loadDecisionReportPrefs().filterSymbol ?? '')
  const [filterSignal, setFilterSignal] = useState(() => loadDecisionReportPrefs().filterSignal ?? '')
  const [filterAction, setFilterAction] = useState(() => loadDecisionReportPrefs().filterAction ?? '')
  const [filterReason, setFilterReason] = useState(() => loadDecisionReportPrefs().filterReason ?? '')
  const [sortBy, setSortBy] = useState<SortKey>(() => loadDecisionReportPrefs().sortBy ?? 'symbol')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>(() => loadDecisionReportPrefs().sortOrder ?? 'asc')

  useEffect(() => {
    saveDecisionReportPrefs({
      filterSymbol,
      filterSignal,
      filterAction,
      filterReason,
      sortBy,
      sortOrder,
    })
  }, [filterSymbol, filterSignal, filterAction, filterReason, sortBy, sortOrder])

  const { data, isLoading, error } = useQuery({
    queryKey: ['reports', 'decisions'],
    queryFn: () => reportsApi.getDecisionReport(),
    refetchInterval: isBotRunning ? 2500 : 10000,
    retry: 1,
    retryDelay: 1000,
    staleTime: 2000,
  })

  const filteredAndSorted = useMemo(() => {
    if (!data?.decisions) return []
    let rows: DecisionRow[] = [...data.decisions]
    if (filterSymbol.trim()) {
      const q = filterSymbol.trim().toLowerCase()
      rows = rows.filter((r) => r.symbol.toLowerCase().includes(q))
    }
    if (filterSignal) rows = rows.filter((r) => r.signal === filterSignal)
    if (filterAction) rows = rows.filter((r) => r.action === filterAction)
    if (filterReason) rows = rows.filter((r) => r.reason === filterReason)
    rows.sort((a, b) => {
      let va: string | number | null = (a as any)[sortBy]
      let vb: string | number | null = (b as any)[sortBy]
      if (va == null) va = ''
      if (vb == null) vb = ''
      if (typeof va === 'number' && typeof vb === 'number') {
        return sortOrder === 'asc' ? va - vb : vb - va
      }
      const sa = String(va)
      const sb = String(vb)
      const cmp = sa.localeCompare(sb, undefined, { numeric: true })
      return sortOrder === 'asc' ? cmp : -cmp
    })
    return rows
  }, [data?.decisions, filterSymbol, filterSignal, filterAction, filterReason, sortBy, sortOrder])

  const uniqueSignals = useMemo(() => {
    if (!data?.decisions) return []
    const set = new Set(data.decisions.map((r) => r.signal).filter(Boolean))
    return Array.from(set).sort()
  }, [data?.decisions])

  const uniqueActions = useMemo(() => {
    if (!data?.decisions) return []
    const set = new Set(data.decisions.map((r) => r.action).filter(Boolean))
    return Array.from(set).sort()
  }, [data?.decisions])

  const uniqueReasons = useMemo(() => {
    if (!data?.decisions) return []
    const set = new Set(data.decisions.map((r) => r.reason).filter(Boolean))
    return Array.from(set).sort()
  }, [data?.decisions])

  // Analysis: summarize signals, reasons, actions to see if the bot is doing what we want
  const analysis = useMemo(() => {
    if (!data?.decisions?.length) return null
    const decisions = data.decisions
    const bySignal: Record<string, number> = {}
    const byReason: Record<string, number> = {}
    const byAction: Record<string, number> = {}
    decisions.forEach((r) => {
      const sig = r.signal || '—'
      bySignal[sig] = (bySignal[sig] ?? 0) + 1
      const reason = r.reason || '—'
      byReason[reason] = (byReason[reason] ?? 0) + 1
      const action = r.action || '—'
      byAction[action] = (byAction[action] ?? 0) + 1
    })
    const holdCount = bySignal['HOLD'] ?? 0
    const buyCount = bySignal['BUY'] ?? 0
    const sellCount = bySignal['SELL'] ?? 0
    const filledCount = (byReason['Filled'] ?? byReason['executed'] ?? 0)
    const holdCountReason = (byReason['Hold'] ?? 0)  // we own the stock, keep position
    const noTradeCount = (byReason['No trade'] ?? 0)  // we don't own it, no entry
    const holdOrNoTradeTotal = holdCountReason + noTradeCount + (byReason['Hold (no trade)'] ?? byReason['strategy says hold'] ?? 0)
    const noMarketDataCount = (byReason['No market data'] ?? byReason['no price/volume'] ?? 0)
    const dataTimeoutCount = (byReason['Data timeout'] ?? byReason['timeout'] ?? 0)
    const executionErrorCount = (byReason['Execution error'] ?? byReason['error'] ?? 0)
    const total = decisions.length
    let insight = ''
    if (filledCount > 0) {
      insight = `Orders filled this cycle: ${filledCount}. Bot is acting on signals.`
    } else if (buyCount + sellCount > 0) {
      insight = `${buyCount} BUY / ${sellCount} SELL signals but no fills this cycle (positions or capital may block).`
    } else if (holdOrNoTradeTotal === total) {
      insight = holdCountReason > 0 && noTradeCount > 0
        ? `All HOLD: ${holdCountReason} Hold (keep position), ${noTradeCount} No trade (no entry).`
        : holdCountReason > 0
          ? 'All HOLD: keeping positions (strategy says hold).'
          : 'All HOLD: no entry (strategy says no trade).'
    } else if (noMarketDataCount > 0 && noMarketDataCount >= total * 0.5) {
      insight = `Many "No market data" (${noMarketDataCount}/${total}). Check data source or STRATEGY_MIN_BARS in Settings → Strategy.`
    } else if (dataTimeoutCount > 0 && dataTimeoutCount >= total * 0.5) {
      insight = `Many data timeouts (${dataTimeoutCount}/${total}). Data source may be slow; GET_STRATEGY_SIGNAL_TIMEOUT_SECONDS may need increase.`
    } else if (executionErrorCount > 0) {
      insight = `Execution errors (${executionErrorCount}). Check Logs for details.`
    } else {
      insight = `Summary: ${holdCount} HOLD, ${buyCount} BUY, ${sellCount} SELL. Use filters to drill down.`
    }
    return {
      bySignal,
      byReason,
      byAction,
      holdCount,
      buyCount,
      sellCount,
      filledCount,
      holdCountReason,
      noTradeCount,
      holdOrNoTradeTotal,
      noMarketDataCount,
      dataTimeoutCount,
      executionErrorCount,
      total,
      insight,
    }
  }, [data?.decisions])

  const toggleSort = (key: SortKey) => {
    if (sortBy === key) setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'))
    else {
      setSortBy(key)
      setSortOrder('asc')
    }
  }

  const formatPrice = (p: number | null) => (p != null ? `$${Number(p).toFixed(2)}` : '—')
  const formatVolume = (v: number | null) => (v != null ? v.toLocaleString() : '—')
  const formatTime = (s: string) => {
    if (!s) return '—'
    try {
      const d = new Date(s)
      return isNaN(d.getTime()) ? s : d.toLocaleTimeString()
    } catch {
      return s
    }
  }

  return (
    <div className="flex flex-col h-screen bg-black/90 text-foreground overflow-hidden">
      <header className="bg-card/50 backdrop-blur-sm border-b border-border px-6 py-4 flex items-center justify-between flex-shrink-0">
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
            <h1 className="text-2xl font-bold">Decision Report</h1>
            <p className="text-sm text-muted-foreground">
              Live view of candidate symbols and bot decisions (BUY / SHORT / HOLD). Filter and sort to see how the bot is working.
            </p>
          </div>
        </div>
        {data && (
          <div className="text-sm text-muted-foreground flex items-center gap-4">
            <span>Cycle #{data.cycle_number}</span>
            <span>{data.total_candidates} candidates</span>
            {isBotRunning && <span className="text-green-500">Bot running • live updates</span>}
          </div>
        )}
      </header>

      <main className="flex-1 overflow-hidden flex flex-col p-6">
        <div className="max-w-full space-y-4 flex flex-col h-full">
          {/* Banner when cycle running but no symbols evaluated yet (first symbol can take 1–2 min) */}
          {data?.cycle_in_progress_no_data && (
            <div className="flex-shrink-0 rounded-lg border border-amber-500/50 bg-amber-500/10 px-4 py-3 text-amber-200">
              <strong>Cycle in progress.</strong> First evaluation can take 1–2 minutes per symbol (fetching OHLCV and price). Check the <strong>Logs</strong> page for &quot;Evaluating symbol 1/N: …&quot; to confirm progress. If it stays stuck for 5+ minutes, restart the API server and <strong>Start</strong> the bot so the report uses the same instance; or set <code className="text-xs bg-black/30 px-1 rounded">GET_STRATEGY_SIGNAL_TIMEOUT_SECONDS=90</code> in .env and <strong>Restart</strong> so slow symbols show &quot;timeout&quot; and the table keeps updating.
            </div>
          )}

          {/* Analysis: is the bot doing what we want? */}
          {analysis && (
            <div className="flex-shrink-0 rounded-lg border border-border bg-card/80 p-4 space-y-3">
              <h3 className="text-sm font-semibold text-foreground">Decision analysis</h3>
              <div className="flex flex-wrap gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Signals: </span>
                  <span className="font-medium">{analysis.holdCount} HOLD</span>
                  {analysis.holdCountReason > 0 && analysis.noTradeCount > 0 && (
                    <span className="text-muted-foreground"> ({analysis.holdCountReason} Hold, {analysis.noTradeCount} No trade)</span>
                  )}
                  {analysis.buyCount > 0 && <>, <span className="text-green-500 font-medium">{analysis.buyCount} BUY</span></>}
                  {analysis.sellCount > 0 && <>, <span className="text-red-500 font-medium">{analysis.sellCount} SELL</span></>}
                </div>
                <div>
                  <span className="text-muted-foreground">Filled this cycle: </span>
                  <span className={analysis.filledCount > 0 ? 'text-green-500 font-medium' : 'text-muted-foreground'}>{analysis.filledCount}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Reasons: </span>
                  {Object.entries(analysis.byReason)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 5)
                    .map(([reason, count]) => (
                      <span key={reason} className="mr-2">
                        <span className="text-muted-foreground">{reason}</span> <span className="font-medium">{count}</span>
                      </span>
                    ))}
                </div>
              </div>
              <p className="text-sm text-muted-foreground border-l-2 border-primary/50 pl-3">{analysis.insight}</p>
            </div>
          )}

          {/* Last cycle timings (when BOT_TIMING=true) — performance check */}
          {data?.last_cycle_timings && Object.keys(data.last_cycle_timings).length > 0 && (
            <div className="flex-shrink-0 rounded-lg border border-border bg-card/80 p-4">
              <h3 className="text-sm font-semibold text-foreground mb-2">Last cycle timings (performance)</h3>
              <p className="text-xs text-muted-foreground mb-2">Enable <code className="bg-black/30 px-1 rounded">BOT_TIMING=true</code> in .env and restart the bot to see these.</p>
              <div className="flex flex-wrap gap-4 text-sm font-mono">
                {data.last_cycle_timings.total_cycle_s != null && (
                  <span><span className="text-muted-foreground">Total cycle:</span> <strong>{Number(data.last_cycle_timings.total_cycle_s).toFixed(2)}s</strong></span>
                )}
                {data.last_cycle_timings.get_strategy_signal_s != null && (
                  <span><span className="text-muted-foreground">Signals:</span> {Number(data.last_cycle_timings.get_strategy_signal_s).toFixed(2)}s</span>
                )}
                {data.last_cycle_timings.execute_trade_s != null && (
                  <span><span className="text-muted-foreground">Execute:</span> {Number(data.last_cycle_timings.execute_trade_s).toFixed(2)}s</span>
                )}
                {data.last_cycle_timings.ohlcv_s != null && (
                  <span><span className="text-muted-foreground">OHLCV:</span> {Number(data.last_cycle_timings.ohlcv_s).toFixed(2)}s</span>
                )}
                {data.last_cycle_timings.strategy_s != null && (
                  <span><span className="text-muted-foreground">Strategy:</span> {Number(data.last_cycle_timings.strategy_s).toFixed(2)}s</span>
                )}
                {data.last_cycle_timings.price_s != null && (
                  <span><span className="text-muted-foreground">Price:</span> {Number(data.last_cycle_timings.price_s).toFixed(2)}s</span>
                )}
                {data.last_cycle_timings.symbols != null && (
                  <span><span className="text-muted-foreground">Symbols:</span> {data.last_cycle_timings.symbols}</span>
                )}
                {data.last_cycle_timings.trades != null && (
                  <span><span className="text-muted-foreground">Trades:</span> {data.last_cycle_timings.trades}</span>
                )}
              </div>
            </div>
          )}

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3 flex-shrink-0" role="group" aria-label="Decision report filters">
            <input
              type="text"
              placeholder="Filter symbol..."
              value={filterSymbol}
              onChange={(e) => setFilterSymbol(e.target.value)}
              className="px-3 py-1.5 rounded-md border border-border bg-card text-foreground min-w-[120px]"
              title="Filter rows by symbol. Example: type AAPL to see only AAPL; leave empty for all symbols."
            />
            <select
              value={filterSignal}
              onChange={(e) => setFilterSignal(e.target.value)}
              className="px-3 py-1.5 rounded-md border border-border bg-card text-foreground"
              title="Filter by strategy signal. Example: choose BUY to see only rows where the bot decided BUY; All signals shows every signal."
            >
              <option value="">All signals</option>
              {uniqueSignals.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <select
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
              className="px-3 py-1.5 rounded-md border border-border bg-card text-foreground"
              title="Filter by action taken. Example: Order submitted = bot sent an order; Hold = no order; All actions shows every action."
            >
              <option value="">All actions</option>
              {uniqueActions.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
            <select
              value={filterReason}
              onChange={(e) => setFilterReason(e.target.value)}
              className="px-3 py-1.5 rounded-md border border-border bg-card text-foreground"
              title="Filter by reason text. Example: No trade, Hold, Order submitted; All reasons shows every reason."
            >
              <option value="">All reasons</option>
              {uniqueReasons.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          {/* Table */}
          <div className="flex-1 overflow-auto rounded-lg border border-border bg-card">
            {isLoading && !data && (
              <div className="p-12 text-center text-muted-foreground">Loading decision report…</div>
            )}
            {error && !data && (
              <div className="p-12 text-center text-muted-foreground">
                Report unavailable. Start the bot to see candidates and decisions.
              </div>
            )}
            {data && (
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-card border-b border-border">
                  <tr>
                    {(['symbol', 'signal', 'action', 'price', 'volume', 'reason', 'cycle_number', 'updated_at'] as SortKey[]).map((key) => (
                      <th
                        key={key}
                        className="text-left px-4 py-3 font-medium cursor-pointer hover:bg-accent/50 capitalize"
                        onClick={() => toggleSort(key)}
                        title={`Sort by ${key === 'updated_at' ? 'updated time' : key.replace('_', ' ')}. Click to toggle ascending/descending.`}
                      >
                        {key === 'updated_at' ? 'Updated' : key.replace('_', ' ')}
                        {sortBy === key && (sortOrder === 'asc' ? ' ↑' : ' ↓')}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredAndSorted.length === 0 && (
                    <tr>
                      <td colSpan={8} className="px-4 py-8 text-center text-muted-foreground">
                        No rows match filters or no candidates yet. Start the bot to see live decisions.
                      </td>
                    </tr>
                  )}
                  {filteredAndSorted.map((row) => (
                    <tr key={row.symbol} className="border-b border-border/50 hover:bg-accent/20">
                      <td className="px-4 py-2 font-medium">{row.symbol}</td>
                      <td className="px-4 py-2">{row.signal}</td>
                      <td className="px-4 py-2">{row.action}</td>
                      <td className="px-4 py-2 tabular-nums">{formatPrice(row.price)}</td>
                      <td className="px-4 py-2 tabular-nums">{formatVolume(row.volume)}</td>
                      <td className="px-4 py-2 text-muted-foreground">{row.reason}</td>
                      <td className="px-4 py-2">{row.cycle_number}</td>
                      <td className="px-4 py-2 text-muted-foreground">{formatTime(row.updated_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
