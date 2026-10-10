import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/api/client'
import { toast } from '@/lib/toast'
import ConfirmDialog from './ConfirmDialog'
import { useBotStatus, type BotStatus } from '@/hooks/useBotStatus'

export default function BotControls() {
  const queryClient = useQueryClient()
  const [showShutdownDialog, setShowShutdownDialog] = useState(false)

  // Use shared bot status hook to prevent duplicate polling
  const { data: status, isLoading, isError } = useBotStatus()

  // Start bot mutation — fetch latest mode from server then start so Start runs the displayed mode (e.g. yfinance)
  const startMutation = useMutation({
    mutationFn: async () => {
      const latest = await queryClient.fetchQuery<BotStatus>({ queryKey: ['bot-status'] })
      const mode = latest?.mode
      const body = mode ? { mode } : {}
      const response = await apiClient.post('/api/bot/start', body)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bot-status'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      queryClient.invalidateQueries({ queryKey: ['messages'] })
    },
    onError: (error: any) => {
      // Silent error handling - no user-facing error messages
      if (import.meta.env.DEV) {
        console.debug('Start error (silent):', error.message || 'Unknown error')
      }
    },
  })

  // Stop bot mutation
  const stopMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/api/bot/stop')
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bot-status'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
    onError: (error: any) => {
      // Silent error handling
      if (import.meta.env.DEV) {
        console.debug('Stop error (silent):', error.message || 'Unknown error')
      }
    },
  })

  // Restart bot: stop, wait, then start (e.g. after changing Settings)
  const restartMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post('/api/bot/stop')
      await new Promise((r) => setTimeout(r, 2000)) // allow bot loop to exit
      const latest = await queryClient.fetchQuery<BotStatus>({ queryKey: ['bot-status'] })
      const mode = latest?.mode
      const body = mode ? { mode } : {}
      const response = await apiClient.post('/api/bot/start', body)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bot-status'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      queryClient.invalidateQueries({ queryKey: ['messages'] })
      toast.success('Bot restarted')
    },
    onError: (error: any) => {
      toast.error(`Restart failed: ${error.message || 'Unknown error'}`)
    },
  })

  // Shutdown server mutation (shuts down bot AND API server)
  const shutdownServerMutation = useMutation({
    mutationFn: async () => {
      console.log('[Shutdown] Starting shutdown request...')
      try {
        const response = await apiClient.post('/api/bot/shutdown-server', {}, {
          timeout: 5000, // 5 second timeout
        })
        console.log('[Shutdown] Response received:', response.data)
        return response.data
      } catch (error: any) {
        console.log('[Shutdown] Error caught:', error)
        // If we get an error, it might be because server is shutting down
        // That's actually expected, so don't treat it as a real error
        if (error.code === 'ECONNRESET' || error.message?.includes('fetch') || error.message?.includes('Network') || error.message?.includes('Failed to fetch')) {
          console.log('[Shutdown] Connection error (expected during shutdown), treating as success')
          return { message: 'Server shutdown initiated', status: 'shutting_down' }
        }
        console.error('[Shutdown] Unexpected error:', error)
        throw error
      }
    },
    onSuccess: (data) => {
      console.log('[Shutdown] Success callback:', data)
      setShowShutdownDialog(false)
      toast.success('Server shutdown initiated')
      queryClient.cancelQueries()
      // Replace page with shutdown message, then try to close the tab (browsers often allow close only for script-opened windows)
      const shutdownMessage = `
        <!DOCTYPE html><html><head><meta charset="utf-8"><title>Server shut down</title>
        <style>body{font-family:system-ui,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;background:#0a0a0a;color:#e5e5e5;text-align:center;padding:2rem;}h1{font-size:1.5rem;}p{color:#a3a3a3;}</style>
        </head><body><div><h1>Server shut down</h1><p>You can close this tab.</p></div></body></html>`
      document.open()
      document.write(shutdownMessage)
      document.close()
      setTimeout(() => {
        window.close()
      }, 500)
    },
    onError: (error: any) => {
      console.error('[Shutdown] Error callback:', error)
      // Show error to user if it's not a connection error
      if (!error.code || (error.code !== 'ECONNRESET' && !error.message?.includes('fetch') && !error.message?.includes('Network'))) {
        toast.error(`Shutdown failed: ${error.message || 'Unknown error'}`)
      }
      setShowShutdownDialog(false)
      queryClient.cancelQueries()
    },
  })

  const isRunning = status?.running || false
  const mode = status?.mode || 'unknown'
  // Normalize display: dryrun-live/dry_run -> Dry Run Live, yfinance -> YFinance
  const modeLabel = (mode === 'dryrun-live' || mode === 'dry_run') ? 'Dry Run Live' : (mode === 'yfinance' ? 'YFinance' : mode.charAt(0).toUpperCase() + mode.slice(1))
  
  // Show disabled state instead of error message when API is unreachable
  const isOffline = isError && !status

  return (
    <div className="flex items-center gap-4 flex-wrap">
      {/* Mode Display: when stopped, show which mode will run when you Start */}
      <div className="flex items-center gap-2 px-3 py-2 bg-muted rounded-lg">
        <span className="text-sm font-medium">{isRunning ? 'Mode:' : 'Mode (when started):'}</span>
        <span className="text-sm font-semibold">{modeLabel}</span>
      </div>

      {/* Status Indicator */}
      <div className="flex items-center gap-2" role="status" aria-live="polite">
        <div
          className={`w-3 h-3 rounded-full ${
            isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
          }`}
        />
        <span className="text-sm font-medium">
          {isRunning ? 'Running' : 'Stopped'}
        </span>
      </div>

      {/* Control Buttons */}
      <div className="flex items-center gap-2">
        {!isRunning ? (
          <>
            <button
              onClick={() => startMutation.mutate()}
              disabled={startMutation.isPending || isLoading || isOffline}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              aria-busy={startMutation.isPending}
              title={isOffline ? 'API Offline — start the API with ./start_api.sh' : 'Start the bot (Restart appears after the bot is running)'}
            >
              {startMutation.isPending ? (
                <span className="inline-flex items-center">
                  <svg className="w-4 h-4 mr-2 animate-spin" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                  </svg>
                  Starting...
                </span>
              ) : (
                'Start'
              )}
            </button>
            <button
              onClick={() => {
                console.log('[Shutdown] Button clicked, opening dialog')
                setShowShutdownDialog(true)
              }}
              disabled={shutdownServerMutation.isPending}
              className="px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              aria-busy={shutdownServerMutation.isPending}
              title="Shutdown bot and API server (closes terminal)"
            >
              {shutdownServerMutation.isPending ? (
                <span className="inline-flex items-center">
                  <svg className="w-4 h-4 mr-2 animate-spin" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                  </svg>
                  Shutting down...
                </span>
              ) : (
                'Shutdown'
              )}
            </button>
            <span className="text-xs text-muted-foreground hidden sm:inline" title="Restart appears after you start the bot">
              Restart appears after Start
            </span>
          </>
        ) : (
          <>
            <button
              onClick={() => stopMutation.mutate()}
              disabled={stopMutation.isPending || restartMutation.isPending}
              className="px-4 py-2 bg-accent text-foreground border border-border rounded-lg hover:bg-accent/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              aria-busy={stopMutation.isPending}
            >
              {stopMutation.isPending ? (
                <span className="inline-flex items-center">
                  <svg className="w-4 h-4 mr-2 animate-spin" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                  </svg>
                  Stopping...
                </span>
              ) : (
                'Stop'
              )}
            </button>
            <button
              onClick={() => restartMutation.mutate()}
              disabled={restartMutation.isPending || stopMutation.isPending}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              aria-busy={restartMutation.isPending}
              title="Stop then start the bot (e.g. after changing Settings)"
            >
              {restartMutation.isPending ? (
                <span className="inline-flex items-center">
                  <svg className="w-4 h-4 mr-2 animate-spin" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                  </svg>
                  Restarting...
                </span>
              ) : (
                'Restart'
              )}
            </button>
            <button
              onClick={() => {
                console.log('[Shutdown] Button clicked, opening dialog')
                setShowShutdownDialog(true)
              }}
              disabled={shutdownServerMutation.isPending}
              className="px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              aria-busy={shutdownServerMutation.isPending}
              title="Shutdown bot and API server (closes terminal)"
            >
              {shutdownServerMutation.isPending ? (
                <span className="inline-flex items-center">
                  <svg className="w-4 h-4 mr-2 animate-spin" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                  </svg>
                  Shutting down...
                </span>
              ) : (
                'Shutdown'
              )}
            </button>
          </>
        )}
      </div>

      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showShutdownDialog}
        title="Shutdown"
        message="Are you sure you want to shutdown? This will stop the bot, close the API server, and you will need to restart it manually. The website will disconnect."
        confirmText="Shutdown"
        cancelText="Cancel"
        variant="destructive"
        onConfirm={() => {
          console.log('[Shutdown] Confirm button clicked, calling mutation')
          shutdownServerMutation.mutate()
        }}
        onCancel={() => {
          console.log('[Shutdown] Cancel button clicked')
          setShowShutdownDialog(false)
        }}
      />
    </div>
  )
}
