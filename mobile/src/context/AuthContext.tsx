// Authentication context with reducer pattern

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { authService } from '@/api/services/auth';
import { getToken, removeToken } from '@/utils/storage';
import { User, LoginRequest } from '@/types';

// State types
interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}

// Action types
type AuthAction =
  | { type: 'LOGIN_REQUEST' }
  | { type: 'LOGIN_SUCCESS'; payload: { token: string; user: User } }
  | { type: 'LOGIN_ERROR'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'REFRESH_TOKEN'; payload: string }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_LOADING'; payload: boolean };

// Initial state
const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
  loading: true,
  error: null,
};

// Reducer
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'LOGIN_REQUEST':
      return { ...state, loading: true, error: null };
    
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload.user,
        token: action.payload.token,
        loading: false,
        error: null,
      };
    
    case 'LOGIN_ERROR':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        token: null,
        loading: false,
        error: action.payload,
      };
    
    case 'LOGOUT':
      return {
        ...initialState,
        loading: false,
      };
    
    case 'REFRESH_TOKEN':
      return {
        ...state,
        token: action.payload,
      };
    
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    
    default:
      return state;
  }
};

// Context type
interface AuthContextType {
  state: AuthState;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider component
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Check for stored token on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = await getToken();
        if (token) {
          // Token exists, verify by refreshing
          await refreshToken();
        } else {
          dispatch({ type: 'SET_LOADING', payload: false });
        }
      } catch (error) {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    checkAuth();
  }, []);

  const login = async (credentials: LoginRequest) => {
    dispatch({ type: 'LOGIN_REQUEST' });
    try {
      const response = await authService.login(credentials);
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: {
          token: response.access_token,
          user: response.user,
        },
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Login failed. Please try again.';
      dispatch({ type: 'LOGIN_ERROR', payload: errorMessage });
      throw error;
    }
  };

  const logout = async () => {
    await removeToken();
    dispatch({ type: 'LOGOUT' });
  };

  const refreshToken = async () => {
    try {
      const response = await authService.refresh();
      dispatch({ type: 'REFRESH_TOKEN', payload: response.access_token });
      dispatch({ type: 'SET_LOADING', payload: false });
    } catch (error) {
      await logout();
      throw error;
    }
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value: AuthContextType = {
    state,
    login,
    logout,
    refreshToken,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
