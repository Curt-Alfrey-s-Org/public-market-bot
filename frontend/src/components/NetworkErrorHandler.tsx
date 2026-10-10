/**
 * Network Error Handler Component
 * Shows a banner when API is unreachable and prevents infinite error loops
 */

import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/api/client'

let networkErrorShown = false

export default function NetworkErrorHandler() {
  
  // Check API health
  const { isError, error } = useQuery({
    queryKey: ['api-health-check'],
    queryFn: async () => {
      const response = await apiClient.get('/api/health', { timeout: 3000 })
      return response.data
    },
    retry: false, // Don't retry health checks
    refetchInterval: 10000, // Check every 10 seconds
    refetchOnWindowFocus: false,
    staleTime: 5000,
    // Prevent errors from causing crashes
    throwOnError: false,
  })

  useEffect(() => {
    if (isError && error) {
      const isNetworkError = !(error as any).response && 
                            ((error as any).code === 'ECONNABORTED' || 
                             (error as any).message?.includes('Network') ||
                             (error as any).message?.includes('timeout'))
      
      if (isNetworkError && !networkErrorShown) {
        networkErrorShown = true
        
        // Reset after 30 seconds to allow retry
        setTimeout(() => {
          networkErrorShown = false
        }, 30000)
      } else if (!isNetworkError) {
        // API is responding
        networkErrorShown = false
      }
    } else {
      // No error
      networkErrorShown = false
    }
  }, [isError, error])

  // Don't show error banner - just track state silently
  // The ConnectionStatus component will show subtle indicator
  return null
}
