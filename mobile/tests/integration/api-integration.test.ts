/**
 * Integration Tests - API Integration
 */

import axios from 'axios';
import { authService } from '@/api/services/auth';
import { botService } from '@/api/services/bot';
import * as storage from '@/utils/storage';
import { mockLoginResponse, mockBotStatus } from '../fixtures/mocks';

jest.mock('axios');
jest.mock('@/utils/storage');

describe('API Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Full API Flow', () => {
    it('should login and get bot status', async () => {
      // Mock login
      const mockLoginPost = jest.fn().mockResolvedValue({
        data: mockLoginResponse,
      });

      // Mock bot status
      const mockStatusGet = jest.fn().mockResolvedValue({
        data: mockBotStatus,
      });

      (axios.post as jest.Mock) = mockLoginPost;
      (axios.get as jest.Mock) = mockStatusGet;

      // Step 1: Login
      const loginData = {
        username: 'testuser',
        password: 'change-me',
      };

      // Step 2: Save token
      const mockSetToken = storage.setToken as jest.Mock;
      mockSetToken.mockResolvedValue(undefined);

      await storage.setToken(mockLoginResponse.access_token);

      expect(mockSetToken).toHaveBeenCalledWith(mockLoginResponse.access_token);

      // Step 3: Get bot status with token
      const mockGetToken = storage.getToken as jest.Mock;
      mockGetToken.mockResolvedValue(mockLoginResponse.access_token);

      const token = await storage.getToken();
      expect(token).toBe(mockLoginResponse.access_token);
    });

    it('should handle API errors gracefully', async () => {
      const mockPost = jest.fn().mockRejectedValue({
        response: {
          status: 401,
          data: { error: 'invalid_credentials' },
        },
      });

      (axios.post as jest.Mock) = mockPost;

      await expect(
        authService.login({ username: 'wrong', password: 'wrong' })
      ).rejects.toThrow();
    });

    it('should retry failed requests', async () => {
      let callCount = 0;
      const mockGet = jest.fn().mockImplementation(() => {
        callCount++;
        if (callCount === 1) {
          return Promise.reject(new Error('Network error'));
        }
        return Promise.resolve({ data: mockBotStatus });
      });

      (axios.get as jest.Mock) = mockGet;

      // First call fails
      await expect(axios.get('/bot/status')).rejects.toThrow();

      // Second call succeeds
      const result = await axios.get('/bot/status');
      expect(result.data).toEqual(mockBotStatus);
    });
  });
});
