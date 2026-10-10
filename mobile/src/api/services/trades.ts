// Trades API service

import apiClient from '../client';
import { TradesResponse, TradeDetail } from '@/types';

export const tradesService = {
  /**
   * Get paginated list of trades
   */
  getTrades: async (limit: number = 20, offset: number = 0): Promise<TradesResponse> => {
    const response = await apiClient.get<TradesResponse>('/trades', {
      params: { limit, offset },
    });
    return response.data;
  },

  /**
   * Get detailed information for a specific trade
   */
  getTrade: async (id: string): Promise<TradeDetail> => {
    const response = await apiClient.get<TradeDetail>(`/trades/${id}`);
    return response.data;
  },
};
