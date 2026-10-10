/**
 * WebSocket Hook for Real-time Updates
 */

import { useEffect, useRef, useState, useCallback } from 'react'

interface WebSocketMessage {
  type: string
  data: any
}

interface UseWebSocketOptions {
  url: string
  onMessage?: (message: WebSocketMessage) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  onClose?: () => void
  reconnectInterval?: number
  reconnectAttempts?: number
}

export function useWebSocket({
  url,
  onMessage,
  onError,
  onOpen,
  onClose,
  reconnectInterval = 3000,
  reconnectAttempts = 5,
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false)
  const [reconnectCount, setReconnectCount] = useState(0)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const shouldReconnectRef = useRef(true)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        setReconnectCount(0)
        onOpen?.()
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          onMessage?.(message)
        } catch (error) {
          if (import.meta.env.DEV) {
            console.error('Error parsing WebSocket message:', error)
          }
        }
      }

      ws.onerror = (error) => {
        onError?.(error)
      }

      ws.onclose = () => {
        setIsConnected(false)
        onClose?.()

        // Attempt to reconnect
        if (shouldReconnectRef.current && reconnectCount < reconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectCount((prev) => prev + 1)
            connect()
          }, reconnectInterval)
        }
      }
    } catch (error) {
      if (import.meta.env.DEV) {
        console.error('WebSocket connection error:', error)
      }
    }
  }, [url, onMessage, onError, onOpen, onClose, reconnectInterval, reconnectAttempts, reconnectCount])

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

  const send = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      if (import.meta.env.DEV) {
        console.warn('WebSocket is not connected')
      }
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    isConnected,
    send,
    disconnect,
    reconnect: connect,
  }
}
