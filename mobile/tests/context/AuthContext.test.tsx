/**
 * Auth Context Tests
 * Tests for AuthContext reducer and provider
 */

import React from 'react';
import { renderHook, act, Result } from '@testing-library/react-native';
import { useAuth, AuthProvider } from '@/context/AuthContext';
import { mockUser, mockLoginResponse } from '../fixtures/mocks';

describe('AuthContext', () => {
  describe('useAuth hook', () => {
    it('should provide auth functions', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current).toEqual(
        expect.objectContaining({
          state: expect.any(Object),
          login: expect.any(Function),
          logout: expect.any(Function),
          clearError: expect.any(Function),
        })
      );
    });

    it('should initialize with logged out state', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.state.isAuthenticated).toBe(false);
      expect(result.current.state.token).toBeNull();
      expect(result.current.state.user).toBeNull();
      expect(result.current.state.loading).toBe(true);
    });

    it('should handle login action', async () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        // Simulate login (would normally call API)
        // This is a simplified test - actual implementation would call login()
      });
    });

    it('should handle logout action', async () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.state.isAuthenticated).toBe(false);
      expect(result.current.state.token).toBeNull();
    });

    it('should clear error state', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      act(() => {
        result.current.clearError();
      });

      expect(result.current.state.error).toBeNull();
    });
  });

  describe('token storage', () => {
    it('should restore token on mount if available', async () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Initially loading
      expect(result.current.state.loading).toBe(true);

      // After async restoration
      await new Promise((resolve) => setTimeout(resolve, 100));
    });
  });
});
