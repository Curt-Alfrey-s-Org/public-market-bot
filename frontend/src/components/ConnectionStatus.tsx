/**
 * Connection Status Indicator
 * Shows API connection status (checks HTTP health endpoint)
 */

import { useQuery } from '@tanstack/react-query'
import apiClient from '@/api/client'

export default function ConnectionStatus() {
  // Check API health instead of WebSocket
  const { data, isLoading, isError } = useQuery({
    queryKey: ['api-health'],
    queryFn: async () => {
      const response = await apiClient.get('/api/health', {
        timeout: 5000, // 5 second timeout (increased from 3s to handle slow responses)
      })
      return response.data
    },
    refetchInterval: 5000, // Check every 5 seconds
    retry: 1, // Reduced from 2 to fail faster
    retryDelay: 1000, // Fixed 1 second delay (simpler than exponential backoff)
    staleTime: 4000, // Increased from 3000ms
    refetchOnWindowFocus: false,
    // Don't fail immediately on first error
    retryOnMount: true,
    // Keep previous data while refetching to prevent flickering (React Query v5)
    placeholderData: (previousData) => previousData,
  })

  // Consider connected if we have data OR if we're loading (optimistic)
  const isConnected = !isError && (data || isLoading)

  // Show subtle status indicator - no error messages
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-muted/50">
      <div
        className={`w-2 h-2 rounded-full transition-colors ${
          isConnected ? 'bg-green-500 animate-pulse' : isLoading ? 'bg-yellow-500' : 'bg-gray-400'
        }`}
        title={isConnected ? 'API Connected' : isLoading ? 'Connecting...' : 'API Offline'}
      />
      <span className="text-xs font-medium text-muted-foreground">
        {isLoading ? 'Connecting...' : isConnected ? 'Online' : 'Offline'}
      </span>
    </div>
  )
}
