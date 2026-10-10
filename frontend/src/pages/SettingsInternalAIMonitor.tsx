/**
 * Admin AI Monitor — internal view of ALFa AI activity and automatic error
 * monitoring + triage. Admin-only; backend enforces the same via require_admin.
 */

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { aiMonitorApi, type ErrorEventRow } from '@/api/aiMonitor'
import { useAuth } from '@/context/AuthContext'

function TriageBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    triaged: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50',
    pending: 'bg-amber-500/20 text-amber-400 border-amber-500/50',
    error: 'bg-red-500/20 text-red-400 border-red-500/50',
    skipped: 'bg-slate-600/20 text-slate-400 border-slate-600/50',
  }
  const c = colors[status] ?? 'bg-slate-600/20 text-slate-400'
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium border ${c}`}>{status}</span>
  )
}

function StatCard({ label, value, tone }: { label: string; value: number | string; tone?: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
      <div className={`mt-1 text-2xl font-bold ${tone ?? 'text-white'}`}>{value}</div>
    </div>
  )
}

export default function SettingsInternalAIMonitor() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [expanded, setExpanded] = useState<number | null>(null)

  const isAdmin = user?.role === 'admin'

  const summary = useQuery({
    queryKey: ['ai-monitor', 'summary'],
    queryFn: async () => (await aiMonitorApi.getSummary()).data,
    refetchInterval: 30_000,
    enabled: isAdmin,
  })

  const errors = useQuery({
    queryKey: ['ai-monitor', 'errors'],
    queryFn: async () => (await aiMonitorApi.getErrors(100)).data,
    refetchInterval: 30_000,
    enabled: isAdmin,
  })

  const activity = useQuery({
    queryKey: ['ai-monitor', 'activity'],
    queryFn: async () => (await aiMonitorApi.getActivity(50)).data,
    refetchInterval: 30_000,
    enabled: isAdmin,
  })

  const triage = useMutation({
    mutationFn: async () => (await aiMonitorApi.triageNow(10)).data,
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-monitor'] })
    },
  })

  if (!isAdmin) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <div className="rounded-lg border border-red-800 bg-red-900/20 p-6 text-red-200">
          <h2 className="text-lg font-semibold">Admin only</h2>
          <p className="mt-2 text-sm">The AI Monitor is restricted to administrators.</p>
        </div>
      </div>
    )
  }

  const s = summary.data

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">AI Monitor</h1>
          <p className="mt-1 text-sm text-slate-400">
            ALFa AI (LiteLLM) activity and automatic error triage. Inference runs on the brain at
            <code className="mx-1 rounded bg-slate-800 px-1">192.0.2.30</code>.
          </p>
        </div>
        <button
          onClick={() => triage.mutate()}
          disabled={triage.isPending}
          className="rounded-md border border-sky-500/50 bg-sky-500/10 px-3 py-2 text-sm font-medium text-sky-300 hover:bg-sky-500/20 disabled:opacity-50"
        >
          {triage.isPending ? 'Triaging…' : 'Triage pending now'}
        </button>
      </header>

      {triage.data && (
        <div className="rounded-md border border-slate-800 bg-slate-900/60 p-3 text-sm text-slate-300">
          Triaged {triage.data.triaged} error(s).
        </div>
      )}

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="LLM calls" value={s?.llm_activity.total_calls ?? '—'} />
        <StatCard
          label="LLM errors"
          value={s?.llm_activity.errors ?? '—'}
          tone={(s?.llm_activity.errors ?? 0) > 0 ? 'text-red-400' : 'text-white'}
        />
        <StatCard
          label="Errors pending"
          value={s?.errors.pending ?? '—'}
          tone={(s?.errors.pending ?? 0) > 0 ? 'text-amber-400' : 'text-white'}
        />
        <StatCard label="Errors triaged" value={s?.errors.triaged ?? '—'} tone="text-emerald-400" />
      </section>

      {/* Captured errors + triage */}
      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">Captured errors</h2>
        {errors.isLoading ? (
          <div className="h-32 animate-pulse rounded bg-slate-800" />
        ) : !errors.data || errors.data.length === 0 ? (
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-6 text-sm text-slate-400">
            No errors captured. 🎉
          </div>
        ) : (
          <div className="space-y-2">
            {errors.data.map((e: ErrorEventRow) => (
              <div key={e.id} className="rounded-lg border border-slate-800 bg-slate-900/60">
                <button
                  onClick={() => setExpanded(expanded === e.id ? null : e.id)}
                  className="flex w-full flex-wrap items-center justify-between gap-2 p-3 text-left"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm text-red-300">{e.error_type}</span>
                      <TriageBadge status={e.triage_status} />
                      <span className="text-xs text-slate-500">×{e.count}</span>
                    </div>
                    <div className="mt-1 truncate text-xs text-slate-400">
                      {e.method} {e.path} — {e.error_message}
                    </div>
                  </div>
                  <span className="text-xs text-slate-500">{e.last_seen}</span>
                </button>
                {expanded === e.id && (
                  <div className="border-t border-slate-800 p-3 text-sm">
                    {e.triage_summary ? (
                      <div className="whitespace-pre-wrap rounded bg-slate-950/60 p-3 text-slate-200">
                        <div className="mb-1 text-xs uppercase tracking-wide text-sky-400">
                          AI triage{e.triage_model ? ` · ${e.triage_model}` : ''}
                        </div>
                        {e.triage_summary}
                      </div>
                    ) : (
                      <div className="text-xs text-slate-500">
                        No triage yet (pending the next batch or an enabled brain).
                      </div>
                    )}
                    <div className="mt-2 text-xs text-slate-500">
                      request_id: {e.request_id || '—'} · first seen: {e.first_seen}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Recent LLM activity */}
      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">Recent LLM activity</h2>
        {activity.isLoading ? (
          <div className="h-32 animate-pulse rounded bg-slate-800" />
        ) : !activity.data || activity.data.length === 0 ? (
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-6 text-sm text-slate-400">
            No LLM activity recorded yet.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="min-w-full divide-y divide-slate-800 text-sm">
              <thead className="bg-slate-900/80 text-left text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-3 py-2">Time</th>
                  <th className="px-3 py-2">Feature</th>
                  <th className="px-3 py-2">Model</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Dur (s)</th>
                  <th className="px-3 py-2">Tokens</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {activity.data.map((a) => (
                  <tr key={a.id}>
                    <td className="whitespace-nowrap px-3 py-2 text-xs text-slate-500">{a.created_at}</td>
                    <td className="px-3 py-2">{a.feature}</td>
                    <td className="px-3 py-2 font-mono text-xs">{a.model}</td>
                    <td className="px-3 py-2">
                      <TriageBadge status={a.status === 'success' ? 'triaged' : 'error'} />
                    </td>
                    <td className="px-3 py-2">{a.duration_seconds?.toFixed(1) ?? '—'}</td>
                    <td className="px-3 py-2 text-xs text-slate-500">
                      {a.prompt_tokens}/{a.eval_tokens}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
