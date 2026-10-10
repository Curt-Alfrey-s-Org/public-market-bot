/**
 * Storage Utility Tests
 * Tests for secure token storage
 */

import { getToken, setToken, removeToken } from '@/utils/storage';
import * as SecureStore from 'expo-secure-store';

jest.mock('expo-secure-store');

describe('storage utilities', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('setToken', () => {
    it('should save token to secure storage', async () => {
      const token = 'change-me';
      const mockSetItem = SecureStore.setItemAsync as jest.Mock;
      mockSetItem.mockResolvedValue(undefined);

      await setToken(token);

      expect(mockSetItem).toHaveBeenCalledWith('auth_token', token);
    });

    it('should handle storage errors gracefully', async () => {
      const mockSetItem = SecureStore.setItemAsync as jest.Mock;
      mockSetItem.mockRejectedValue(new Error('Storage failed'));

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      await setToken('token');

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });

  describe('getToken', () => {
    it('should retrieve token from secure storage', async () => {
      const token = 'change-me';
      const mockGetItem = SecureStore.getItemAsync as jest.Mock;
      mockGetItem.mockResolvedValue(token);

      const result = await getToken();

      expect(mockGetItem).toHaveBeenCalledWith('auth_token');
      expect(result).toBe(token);
    });

    it('should return null when no token exists', async () => {
      const mockGetItem = SecureStore.getItemAsync as jest.Mock;
      mockGetItem.mockResolvedValue(null);

      const result = await getToken();

      expect(result).toBeNull();
    });

    it('should handle retrieval errors gracefully', async () => {
      const mockGetItem = SecureStore.getItemAsync as jest.Mock;
      mockGetItem.mockRejectedValue(new Error('Retrieval failed'));

      const result = await getToken();

      expect(result).toBeNull();
    });
  });

  describe('removeToken', () => {
    it('should remove token from secure storage', async () => {
      const mockDeleteItem = SecureStore.deleteItemAsync as jest.Mock;
      mockDeleteItem.mockResolvedValue(undefined);

      await removeToken();

      expect(mockDeleteItem).toHaveBeenCalledWith('auth_token');
    });

    it('should handle deletion errors gracefully', async () => {
      const mockDeleteItem = SecureStore.deleteItemAsync as jest.Mock;
      mockDeleteItem.mockRejectedValue(new Error('Deletion failed'));

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      await removeToken();

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });
});
