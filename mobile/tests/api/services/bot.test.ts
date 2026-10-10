/**
 * Bot Service Tests
 * Tests for bot control API calls
 */

import { botService } from '@/api/services/bot';
import axios from 'axios';
import { mockBotStatus } from '../fixtures/mocks';

jest.mock('axios');

describe('Bot Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getBotStatus', () => {
    it('should fetch current bot status', async () => {
      const mockGet = jest.fn().mockResolvedValue({
        data: mockBotStatus,
      });
      (axios.get as jest.Mock) = mockGet;

      const result = await botService.getBotStatus();

      expect(mockGet).toHaveBeenCalledWith('/bot/status');
      expect(result).toEqual(mockBotStatus);
    });

    it('should handle status fetch errors', async () => {
      const mockGet = jest.fn().mockRejectedValue(new Error('Network error'));
      (axios.get as jest.Mock) = mockGet;

      await expect(botService.getBotStatus()).rejects.toThrow();
    });
  });

  describe('startBot', () => {
    it('should start trading bot', async () => {
      const mockPost = jest.fn().mockResolvedValue({
        data: { status: 'started', message: 'Bot started successfully' },
      });
      (axios.post as jest.Mock) = mockPost;

      const result = await botService.startBot();

      expect(mockPost).toHaveBeenCalledWith('/bot/start', {});
      expect(result.status).toBe('started');
    });

    it('should handle start errors', async () => {
      const mockPost = jest.fn().mockRejectedValue({
        response: { status: 400, data: { error: 'bot_already_running' } },
      });
      (axios.post as jest.Mock) = mockPost;

      await expect(botService.startBot()).rejects.toThrow();
    });
  });

  describe('stopBot', () => {
    it('should stop trading bot', async () => {
      const mockPost = jest.fn().mockResolvedValue({
        data: { status: 'stopped', message: 'Bot stopped successfully' },
      });
      (axios.post as jest.Mock) = mockPost;

      const result = await botService.stopBot();

      expect(mockPost).toHaveBeenCalledWith('/bot/stop', {});
      expect(result.status).toBe('stopped');
    });

    it('should handle stop errors', async () => {
      const mockPost = jest.fn().mockRejectedValue(new Error('Stop failed'));
      (axios.post as jest.Mock) = mockPost;

      await expect(botService.stopBot()).rejects.toThrow();
    });
  });
});
