/**
 * Messages API functions
 */

import apiClient from './client'

export interface Message {
  timestamp: string
  message: string
  category: 'trading_paused' | 'alerts' | 'info' | 'warning' | 'capital_schedule'
  details?: any
}

export interface MessagesResponse {
  messages: Message[]
  total: number
}

export const messagesApi = {
  getMessages: async (category?: string, limit?: number): Promise<MessagesResponse> => {
    const params = new URLSearchParams()
    if (category) params.append('category', category)
    if (limit) params.append('limit', limit.toString())
    
    const response = await apiClient.get<MessagesResponse>(`/api/messages?${params.toString()}`)
    return response.data
  },
}
