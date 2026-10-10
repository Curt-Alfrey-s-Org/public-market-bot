import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { systemApi, RunTestsResponse } from '@/api/system'

interface SelfTestPanelProps {
  isOpen: boolean
  onClose: () => void
  currentStatus: boolean | null
  passedCount?: number
  totalCount?: number
  /** When true, Run Full Test Suite is disabled (bot must be stopped first). */
  botRunning?: boolean
}

export default function SelfTestPanel({ isOpen, onClose, currentStatus, passedCount, totalCount, botRunning = false }: SelfTestPanelProps) {
  const queryClient = useQueryClient()
  const [testResults, setTestResults] = useState<RunTestsResponse | null>(null)

  const runTestsMutation = useMutation({
    mutationFn: systemApi.runTests,
    onSuccess: (data) => {
      setTestResults(data)
      // Store last result so "View Fail Details" can show it; tag as full run so badge can show red only when this failed
      queryClient.setQueryData(['last-test-result'], { ...data, source: 'full_run' as const })
      // Refresh health status
      queryClient.invalidateQueries({ queryKey: ['system-health'] })
    },
  })

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-card border border-border rounded-lg w-full max-w-2xl max-h-[80vh] overflow-hidden shadow-xl mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 className="text-lg font-bold">Self-Test Results</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-accent rounded transition-colors"
            aria-label="Close panel"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[60vh]">
          {/* Current Status */}
          <div className="mb-4 p-3 rounded-lg bg-muted/30">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Current Status:</span>
              <div className="flex items-center gap-2">
                {currentStatus === true && (
                  <span className="flex items-center gap-1 text-green-500">
                    <div className="w-2 h-2 rounded-full bg-green-500"></div>
                    PASS ({passedCount}/{totalCount})
                  </span>
                )}
                {currentStatus === false && (
                  <span className="flex items-center gap-1 text-red-500">
                    <div className="w-2 h-2 rounded-full bg-red-500"></div>
                    FAIL ({passedCount}/{totalCount})
                  </span>
                )}
                {currentStatus === null && (
                  <span className="flex items-center gap-1 text-yellow-500">
                    <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
                    Unknown
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Run Tests Button - only when bot is stopped */}
          {botRunning && (
            <div className="mb-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-200 text-sm">
              Stop the bot before running the full test suite.
            </div>
          )}
          <button
            onClick={() => runTestsMutation.mutate()}
            disabled={runTestsMutation.isPending || botRunning}
            className="w-full mb-4 px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {runTestsMutation.isPending ? (
              <>
                <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin"></div>
                Running Tests...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Run Full Test Suite
              </>
            )}
          </button>

          {/* Test Results */}
          {testResults && (
            <div className="space-y-4">
              {/* Summary */}
              <div className={`p-4 rounded-lg border ${testResults.success ? 'border-green-500/30 bg-green-500/10' : 'border-red-500/30 bg-red-500/10'}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">
                    {testResults.success ? '✓ All Tests Passed' : '✗ Some Tests Failed'}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {testResults.duration_s}s
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-2 text-sm">
                  <div className="text-center p-2 rounded bg-muted/30">
                    <div className="font-bold text-lg">{testResults.total}</div>
                    <div className="text-muted-foreground text-xs">Total</div>
                  </div>
                  <div className="text-center p-2 rounded bg-green-500/20">
                    <div className="font-bold text-lg text-green-500">{testResults.passed}</div>
                    <div className="text-muted-foreground text-xs">Passed</div>
                  </div>
                  <div className="text-center p-2 rounded bg-red-500/20">
                    <div className="font-bold text-lg text-red-500">{testResults.failed}</div>
                    <div className="text-muted-foreground text-xs">Failed</div>
                  </div>
                  <div className="text-center p-2 rounded bg-yellow-500/20">
                    <div className="font-bold text-lg text-yellow-500">{testResults.warnings}</div>
                    <div className="text-muted-foreground text-xs">Warnings</div>
                  </div>
                </div>
              </div>

              {/* Failed Tests Details */}
              {testResults.failed_tests && testResults.failed_tests.length > 0 && (
                <div className="space-y-2">
                  <h3 className="font-semibold text-red-500">Failed Tests:</h3>
                  <div className="space-y-2">
                    {testResults.failed_tests.map((test, index) => (
                      <div key={index} className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                        <div className="font-medium text-red-400">✗ {test.name}</div>
                        {test.error && (
                          <div className="mt-1 text-sm text-muted-foreground break-words">
                            {test.error}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Error */}
              {testResults.error && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                  <div className="font-medium text-red-400">Error:</div>
                  <div className="mt-1 text-sm text-muted-foreground">{testResults.error}</div>
                </div>
              )}
            </div>
          )}

          {/* Mutation Error */}
          {runTestsMutation.isError && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
              <div className="font-medium text-red-400">Failed to run tests</div>
              <div className="mt-1 text-sm text-muted-foreground">
                {(runTestsMutation.error as Error)?.message || 'Unknown error'}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-muted text-muted-foreground rounded-lg hover:bg-muted/80 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
