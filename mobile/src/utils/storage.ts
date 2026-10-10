// Secure token storage utilities using expo-secure-store

import * as SecureStore from 'expo-secure-store';

const TOKEN_KEY = 'change-me';

export const getToken = async (): Promise<string | null> => {
  try {
    return await SecureStore.getItemAsync(TOKEN_KEY);
  } catch (error) {
    console.error('Error retrieving token:'change-me'Error storing token:'change-me'Error removing token:', error);
    throw error;
  }
};
