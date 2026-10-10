// Statistics API service

import apiClient from '../client';
import { StatisticsResponse } from '@/types';

export const statsService = {
  /**
   * Get trading statistics and analytics
   */
  getStats: async (): Promise<StatisticsResponse> => {
    const response = await apiClient.get<StatisticsResponse>('/stats');
    return response.data;
  },
};
