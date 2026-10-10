// Bot control API service

import apiClient from '../client';
import { BotStatusResponse, BotControlResponse } from '@/types';

export const botService = {
  /**
   * Get current bot status
   */
  getStatus: async (): Promise<BotStatusResponse> => {
    const response = await apiClient.get<BotStatusResponse>('/bot/status');
    return response.data;
  },

  /**
   * Start the trading bot
   */
  start: async (): Promise<BotControlResponse> => {
    const response = await apiClient.post<BotControlResponse>('/bot/start');
    return response.data;
  },

  /**
   * Stop the trading bot
   */
  stop: async (): Promise<BotControlResponse> => {
    const response = await apiClient.post<BotControlResponse>('/bot/stop');
    return response.data;
  },
};
