/**
 * Shared hook for bot status
 * Prevents duplicate polling by multiple components
 */

import { useQuery } from '@tanstack/react-query'
import apiClient from '@/api/client'

export interface BotStatus {
  running: boolean
  mode: string
}

export function useBotStatus() {
  return useQuery<BotStatus>({
    queryKey: ['bot-status'],
    queryFn: async () => {
      const response = await apiClient.get('/api/bot/status', {
        timeout: 5000, // 5 second timeout
      })
      return response.data
    },
    refetchInterval: (query) => {
      // Stop polling if we have a network error
      if (query.state.error && (query.state.error as any).isNetworkError) {
        return false // Stop polling on network errors
      }
      return 3000 // Refresh every 3 seconds
    },
    retry: (failureCount, error: any) => {
      // Don't retry on network errors
      if (error.isNetworkError || (!error.response && (error.code === 'ECONNABORTED' || error.message?.includes('Network')))) {
        return false
      }
      return failureCount < 2
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 5000), // Exponential backoff
    staleTime: 2000,
    gcTime: 10000, // Keep in cache for 10 seconds
    refetchOnWindowFocus: false,
    refetchOnMount: true,
    // Prevent errors from causing crashes
    throwOnError: false,
  })
}
