/**
 * Hook for Real-time Stats Updates via WebSocket
 */

import { useQueryClient } from '@tanstack/react-query'
import { useWebSocket } from './useWebSocket'

const WS_URL =
  typeof import.meta.env.VITE_WS_URL === 'string' && import.meta.env.VITE_WS_URL
    ? import.meta.env.VITE_WS_URL
    : typeof window !== 'undefined'
      ? (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws'
      : ''

export function useRealtimeStats() {
  const queryClient = useQueryClient()

  const { isConnected } = useWebSocket({
    url: WS_URL,
    onMessage: (message) => {
      if (message.type === 'stats') {
        queryClient.invalidateQueries({ queryKey: ['stats'] })
      } else if (message.type === 'trade') {
        queryClient.invalidateQueries({ queryKey: ['trades'] })
        queryClient.invalidateQueries({ queryKey: ['stats'] })
        queryClient.invalidateQueries({ queryKey: ['bot-status'] })
      }
      // Do not invalidate bot-status on every "status" message (sent every 1s) — useBotStatus polls every 3s
    },
    onError: (error) => {
      if (import.meta.env.DEV) {
        console.error('WebSocket error:', error)
      }
    },
    onOpen: () => {
      if (import.meta.env.DEV) {
        console.log('WebSocket connected')
      }
    },
    onClose: () => {
      if (import.meta.env.DEV) {
        console.log('WebSocket disconnected')
      }
    },
  })

  return { isConnected }
}
