// Axios API client with interceptors for authentication

import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { API_CONFIG } from '@/constants/api';
import { getToken, setToken, removeToken } from '@/utils/storage';

const apiClient = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - inject Authorization header
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const token = await getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle 401 and token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // If 401 and not already retrying, attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const token = await getToken();
        if (token) {
          // Call refresh endpoint
          const refreshResponse = await axios.post(
            `${API_CONFIG.BASE_URL}/auth/refresh`,
            {},
            {
              headers: { Authorization: `Bearer ${token}` },
            }
          );

          const newToken = refreshResponse.data.access_token;
          await setToken(newToken);

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          }
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, remove token and redirect to login
        await removeToken();
        // You can dispatch a logout action here or use a navigation ref
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
