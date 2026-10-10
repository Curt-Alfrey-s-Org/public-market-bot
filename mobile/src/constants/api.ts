// API Configuration Constants

export const API_CONFIG = {
  BASE_URL: process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8004/api/v1',
  TIMEOUT: 30000,  // 30 seconds
  RETRY_ATTEMPTS: 3,
} as const;

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REFRESH: '/auth/refresh',
  },
  BOT: {
    STATUS: '/bot/status',
    START: '/bot/start',
    STOP: '/bot/stop',
  },
  TRADES: {
    LIST: '/trades',
    DETAIL: '/trades/:id',
  },
  STATS: '/statistics',
  SETTINGS: '/settings',
} as const;
