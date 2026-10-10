/**
 * Bot Control API functions
 */

import apiClient from './client'

export interface BotStatus {
  running: boolean
  mode: string
  last_update?: string
}

export const botApi = {
  getStatus: async (): Promise<BotStatus> => {
    const response = await apiClient.get<BotStatus>('/api/bot/status')
    return response.data
  },

  start: async (): Promise<{ message: string; status: string }> => {
    const response = await apiClient.post('/api/bot/start')
    return response.data
  },

  stop: async (): Promise<{ message: string; status: string }> => {
    const response = await apiClient.post('/api/bot/stop')
    return response.data
  },

  shutdown: async (): Promise<{ message: string; status: string }> => {
    const response = await apiClient.post('/api/bot/shutdown')
    return response.data
  },
}
