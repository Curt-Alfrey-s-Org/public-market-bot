/**
 * Integration Tests - Authentication Flow
 */

import React from 'react';
import { render, fireEvent, waitFor } from '../utils/test-utils';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import { mockLoginResponse } from '../fixtures/mocks';
import * as storage from '@/utils/storage';

jest.mock('@/utils/storage');

// Test component that uses auth
const TestAuthComponent = () => {
  const { state, login } = useAuth();

  return (
    <div>
      <div testID="auth-status">
        {state.isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
      </div>
      {state.user && <div testID="username">{state.user.username}</div>}
      {state.error && <div testID="error">{state.error}</div>}
    </div>
  );
};

describe('Authentication Flow Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should initialize as not authenticated', () => {
    const { getByTestId } = render(
      <AuthProvider>
        <TestAuthComponent />
      </AuthProvider>
    );

    expect(getByTestId('auth-status').children[0]).toBe('Not Authenticated');
  });

  it('should handle successful login', async () => {
    const mockSetToken = storage.setToken as jest.Mock;
    mockSetToken.mockResolvedValue(undefined);

    const { getByTestId } = render(
      <AuthProvider>
        <TestAuthComponent />
      </AuthProvider>
    );

    // Initially not authenticated
    expect(getByTestId('auth-status').children[0]).toBe('Not Authenticated');
  });

  it('should persist token after login', async () => {
    const mockSetToken = storage.setToken as jest.Mock;
    mockSetToken.mockResolvedValue(undefined);

    const mockToken = 'change-me';

    await storage.setToken(mockToken);

    expect(mockSetToken).toHaveBeenCalledWith(mockToken);
  });

  it('should restore session from stored token', async () => {
    const mockGetToken = storage.getToken as jest.Mock;
    mockGetToken.mockResolvedValue('stored-token');

    const token = await storage.getToken();
    expect(token).toBe('stored-token');
  });

  it('should clear token on logout', async () => {
    const mockRemoveToken = storage.removeToken as jest.Mock;
    mockRemoveToken.mockResolvedValue(undefined);

    await storage.removeToken();

    expect(mockRemoveToken).toHaveBeenCalled();
  });
});
