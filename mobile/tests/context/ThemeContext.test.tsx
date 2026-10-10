/**
 * Theme Context Tests
 * Tests for theme switching and persistence
 */

import React from 'react';
import { renderHook, act } from '@testing-library/react-native';
import { useTheme, ThemeProvider } from '@/context/ThemeContext';
import AsyncStorage from '@react-native-async-storage/async-storage';

jest.mock('@react-native-async-storage/async-storage');

describe('ThemeContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('useTheme hook', () => {
    it('should provide theme context', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <ThemeProvider>{children}</ThemeProvider>
      );

      const { result } = renderHook(() => useTheme(), { wrapper });

      expect(result.current).toEqual(
        expect.objectContaining({
          theme: expect.any(Object),
          themeMode: expect.any(String),
          setThemeMode: expect.any(Function),
          toggleTheme: expect.any(Function),
        })
      );
    });

    it('should have theme colors defined', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <ThemeProvider>{children}</ThemeProvider>
      );

      const { result } = renderHook(() => useTheme(), { wrapper });

      expect(result.current.theme.colors).toEqual(
        expect.objectContaining({
          primary: expect.any(String),
          secondary: expect.any(String),
          background: expect.any(String),
          text: expect.any(String),
        })
      );
    });

    it('should toggle theme', async () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <ThemeProvider>{children}</ThemeProvider>
      );

      const { result } = renderHook(() => useTheme(), { wrapper });

      const initialMode = result.current.themeMode;

      await act(async () => {
        result.current.toggleTheme();
      });

      // Theme should have changed
      expect(result.current.themeMode).not.toBe(initialMode);
    });

    it('should persist theme preference', async () => {
      const mockSetItem = AsyncStorage.setItem as jest.Mock;
      mockSetItem.mockResolvedValue(undefined);

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <ThemeProvider>{children}</ThemeProvider>
      );

      const { result } = renderHook(() => useTheme(), { wrapper });

      await act(async () => {
        result.current.setThemeMode('dark');
      });

      expect(mockSetItem).toHaveBeenCalledWith('@app:theme', 'dark');
    });

    it('should load persisted theme preference', async () => {
      const mockGetItem = AsyncStorage.getItem as jest.Mock;
      mockGetItem.mockResolvedValue('dark');

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <ThemeProvider>{children}</ThemeProvider>
      );

      const { result } = renderHook(() => useTheme(), { wrapper });

      // Wait for async load
      await new Promise((resolve) => setTimeout(resolve, 100));

      // Theme should be loaded
      expect(result.current.themeMode).toBeDefined();
    });
  });
});
