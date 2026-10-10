/**
 * Health Dashboard - API status, DB latency, Redis, uptime, error logs
 */

import { useQuery } from '@tanstack/react-query'
import { healthApi, type HealthDetailedResponse } from '@/api/health'

function formatUptime(seconds: number) {
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  return `${d}d ${h}h`
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    healthy: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50',
    degraded: 'bg-amber-500/20 text-amber-400 border-amber-500/50',
    unhealthy: 'bg-red-500/20 text-red-400 border-red-500/50',
    not_configured: 'bg-slate-600/20 text-slate-400 border-slate-600/50',
    skipped: 'bg-slate-600/20 text-slate-400 border-slate-600/50',
  }
  const c = colors[status] ?? 'bg-slate-600/20 text-slate-400'
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium border ${c}`}>
      {status}
    </span>
  )
}

export function HealthDashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['health-detailed'],
    queryFn: async () => {
      const { data: res } = await healthApi.getDetailed()
      return res
    },
    refetchInterval: 30_000,
  })

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-700 rounded w-1/3" />
          <div className="h-48 bg-slate-800 rounded" />
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <div className="rounded-lg border border-red-800 bg-red-900/20 p-6 text-red-200">
          <h2 className="text-lg font-semibold">Failed to load health status</h2>
          <p className="mt-2 text-sm">{error instanceof Error ? error.message : 'Unknown error'}</p>
        </div>
      </div>
    )
  }

  const h = data as HealthDetailedResponse

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <header>
        <h1 className="text-2xl font-bold text-white">Health & Monitoring</h1>
        <p className="mt-1 text-slate-400">
          API status, database latency, Redis connection, uptime, and error logs
        </p>
      </header>

      {/* Summary row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">API Status</p>
          <p className="mt-2">
            <StatusBadge status={h.status} />
          </p>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Uptime</p>
          <p className="mt-2 text-lg font-semibold text-white">
            {h.uptime_seconds != null ? formatUptime(h.uptime_seconds) : '—'}
          </p>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Database</p>
          <p className="mt-2 flex items-center gap-2">
            <StatusBadge status={h.database?.status ?? 'unknown'} />
            {h.database?.latency_ms != null && (
              <span className="text-sm text-slate-400">{h.database.latency_ms} ms</span>
            )}
          </p>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Redis</p>
          <p className="mt-2 flex items-center gap-2">
            <StatusBadge status={h.redis?.status ?? 'unknown'} />
            {h.redis?.latency_ms != null && (
              <span className="text-sm text-slate-400">{h.redis.latency_ms} ms</span>
            )}
          </p>
        </div>
      </div>

      {/* Database details */}
      {h.database?.error && (
        <div className="rounded-lg border border-amber-800 bg-amber-900/20 p-4">
          <h3 className="font-medium text-amber-200">Database Error</h3>
          <p className="mt-1 font-mono text-sm text-slate-300">{h.database.error}</p>
        </div>
      )}

      {/* Redis details */}
      {h.redis?.error && h.redis.status !== 'not_configured' && (
        <div className="rounded-lg border border-amber-800 bg-amber-900/20 p-4">
          <h3 className="font-medium text-amber-200">Redis Error</h3>
          <p className="mt-1 font-mono text-sm text-slate-300">{h.redis.error}</p>
        </div>
      )}

      {/* Error logs */}
      {Array.isArray(h.error_logs) && h.error_logs.length > 0 && (
        <div className="rounded-lg border border-slate-700 bg-slate-900/80 p-4">
          <h3 className="font-medium text-red-300">Recent Error Logs</h3>
          <ul className="mt-2 max-h-48 overflow-y-auto space-y-1 font-mono text-xs text-slate-400">
            {h.error_logs.map((line, i) => (
              <li key={i} className="truncate">
                {line}
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="text-xs text-slate-500">
        Last updated: {h.timestamp} · Service: {h.service} v{h.version}
      </p>
    </div>
  )
}
