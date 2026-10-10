/**
 * Test Utilities - Helper functions for testing
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react-native';
import { AuthProvider } from '@/context/AuthContext';
import { ThemeProvider } from '@/context/ThemeContext';
import { ToastProvider } from '@/context/ToastContext';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

interface AllTheProvidersProps {
  children: React.ReactNode;
}

const AllTheProviders: React.FC<AllTheProvidersProps> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ThemeProvider>
          <ToastProvider>{children}</ToastProvider>
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react-native';
export { customRender as render };

/**
 * Wait for async operations
 */
export const waitForAsync = () =>
  new Promise((resolve) => setTimeout(resolve, 0));

/**
 * Create mock token
 */
export const createMockToken = (overrides = {}) => {
  const now = Math.floor(Date.now() / 1000);
  return {
    sub: '123',
    username: 'testuser',
    iat: now,
    exp: now + 86400, // 24 hours
    type: 'access',
    ...overrides,
  };
};

/**
 * Encode mock JWT token
 */
export const createMockJWT = (payload = {}) => {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const body = btoa(JSON.stringify(createMockToken(payload)));
  const signature = btoa('mock-signature');
  return `${header}.${body}.${signature}`;
};
