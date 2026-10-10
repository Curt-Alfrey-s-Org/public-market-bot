// Authentication API service

import apiClient from '../client';
import { LoginRequest, LoginResponse, RefreshResponse } from '@/types';
import { setToken } from '@/utils/storage';

export const authService = {
  /**
   * Login with username and password
   */
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/login', credentials);
    
    // Store token after successful login
    if (response.data.access_token) {
      await setToken(response.data.access_token);
    }
    
    return response.data;
  },

  /**
   * Refresh access token
   */
  refresh: async (): Promise<RefreshResponse> => {
    const response = await apiClient.post<RefreshResponse>('/auth/refresh');
    
    // Update token
    if (response.data.access_token) {
      await setToken(response.data.access_token);
    }
    
    return response.data;
  },
};
