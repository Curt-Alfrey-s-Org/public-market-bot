/**
 * Auth Service Tests
 * Tests for authentication API calls
 */

import { authService } from '@/api/services/auth';
import axios from 'axios';
import * as storage from '@/utils/storage';
import { mockLoginResponse, mockUser } from '../fixtures/mocks';

jest.mock('axios');
jest.mock('@/utils/storage');

describe('Auth Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('login', () => {
    it('should login with credentials', async () => {
      const mockPost = jest.fn().mockResolvedValue({
        data: mockLoginResponse,
      });
      (axios.post as jest.Mock) = mockPost;

      const result = await authService.login({
        username: 'testuser',
        password: 'change-me',
      });

      expect(mockPost).toHaveBeenCalledWith('/auth/login', expect.any(Object));
      expect(result).toEqual({
        token: mockLoginResponse.access_token,
        user: mockLoginResponse.user,
      });
    });

    it('should handle login errors', async () => {
      const mockPost = jest.fn().mockRejectedValue({
        response: { status: 401, data: { error: 'invalid_credentials' } },
      });
      (axios.post as jest.Mock) = mockPost;

      await expect(
        authService.login({ username: 'wrong', password: 'wrong' })
      ).rejects.toThrow();
    });
  });

  describe('refresh', () => {
    it('should refresh token', async () => {
      const newToken = 'change-me';
      const mockPost = jest.fn().mockResolvedValue({
        data: { access_token: newToken },
      });
      (axios.post as jest.Mock) = mockPost;

      const result = await authService.refresh();

      expect(mockPost).toHaveBeenCalledWith('/auth/refresh', {});
      expect(result).toBe(newToken);
    });

    it('should handle refresh errors', async () => {
      const mockPost = jest.fn().mockRejectedValue({
        response: { status: 401 },
      });
      (axios.post as jest.Mock) = mockPost;

      await expect(authService.refresh()).rejects.toThrow();
    });
  });

  describe('logout', () => {
    it('should clear token from storage', async () => {
      const mockRemoveToken = storage.removeToken as jest.Mock;
      mockRemoveToken.mockResolvedValue(undefined);

      await authService.logout();

      expect(mockRemoveToken).toHaveBeenCalled();
    });
  });
});
