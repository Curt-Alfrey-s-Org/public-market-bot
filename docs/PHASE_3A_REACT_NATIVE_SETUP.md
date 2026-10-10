# Phase 3-A: React Native Infrastructure Setup

**Status:** Ready for implementation  
**Estimated Time:** 10-15 hours (2-3 days)  
**Dependencies:** Phase 2 complete (API v1 endpoints + auth ready)

---

## Overview

Phase 3-A establishes the complete Expo React Native project with:
- Project initialization with Expo Router
- Core infrastructure (API client, storage, auth context)
- Navigation structure (auth stack + app tabs)
- Reusable components and utilities
- TypeScript configuration
- Development environment setup

---

## Step 1: Initialize Expo Project (1-2 hours)

### Create Project

```bash
cd /home/operator/market-pie5-bot
npx create-expo-app mobile --template tabs
cd mobile
```

### Verify Structure

```
mobile/
├── app/
│   ├── (tabs)/
│   │   ├── index.tsx
│   │   └── explore.tsx
│   ├── _layout.tsx
│   └── +not-found.tsx
├── assets/
├── components/
├── constants/
├── hooks/
├── package.json
├── tsconfig.json
├── app.json
└── ... (Expo config files)
```

### Update `package.json`

```json
{
  "name": "market-bot-mobile",
  "version": "1.0.0",
  "description": "AI-powered market trading bot mobile app",
  "main": "expo-router/entry",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web",
    "test": "jest --watchAll",
    "lint": "eslint .",
    "type-check": "tsc --noEmit",
    "prebuild": "expo prebuild",
    "eas-build": "eas build --platform all",
    "eas-submit": "eas submit --platform all"
  },
  "dependencies": {
    "expo": "~52.0.0",
    "expo-router": "~4.0.0",
    "react": "18.3.1",
    "react-native": "0.76.1"
  },
  "devDependencies": {
    "@babel/core": "^7.25.2",
    "@types/react": "~18.3.12",
    "@types/react-native": "~0.73.0",
    "typescript": "~5.3.3"
  }
}
```

### Update `app.json`

```json
{
  "expo": {
    "name": "Market Bot",
    "slug": "market-bot-mobile",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/images/icon.png",
    "scheme": "marketbot",
    "userInterfaceStyle": "automatic",
    "newArchEnabled": true,
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.alfaquantum.marketbot"
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/images/adaptive-icon.png",
        "backgroundColor": "#ffffff"
      },
      "package": "com.alfaquantum.marketbot"
    },
    "web": {
      "bundler": "metro",
      "output": "static",
      "favicon": "./assets/images/favicon.png"
    },
    "plugins": [
      "expo-router",
      "expo-secure-store"
    ],
    "experiments": {
      "typedRoutes": true
    }
  }
}
```

---

## Step 2: Install Core Dependencies (1-2 hours)

### Production Dependencies

```bash
npm install \
  expo-router@~4.0.0 \
  expo-secure-store@~14.0.0 \
  @react-native-async-storage/async-storage@^2.1.0 \
  axios@^1.7.0 \
  @tanstack/react-query@^5.62.0 \
  zustand@^5.0.0 \
  react-hook-form@^7.54.0 \
  zod@^3.24.0 \
  date-fns@^4.1.0 \
  react-native-svg@^15.9.0 \
  lodash@^4.17.21
```

### Development Dependencies

```bash
npm install --save-dev \
  @types/lodash@^4.17.0 \
  @testing-library/react-native@^12.9.0 \
  @testing-library/jest-native@^5.4.3 \
  jest@^29.7.0 \
  jest-expo@~52.0.0 \
  @typescript-eslint/eslint-plugin@^8.18.0 \
  @typescript-eslint/parser@^8.18.0 \
  eslint@^9.17.0 \
  prettier@^3.4.2
```

### Verify Installation

```bash
npm list | grep -E "expo-router|expo-secure-store|axios|react-query"
```

---

## Step 3: Configure TypeScript & Tooling (1 hour)

### `tsconfig.json`

```json
{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true,
    "jsx": "react-native",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "forceConsistentCasingInFileNames": true,
    "moduleResolution": "node",
    "noEmit": true,
    "isolatedModules": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"],
      "@/api/*": ["./src/api/*"],
      "@/components/*": ["./src/components/*"],
      "@/context/*": ["./src/context/*"],
      "@/hooks/*": ["./src/hooks/*"],
      "@/utils/*": ["./src/utils/*"],
      "@/types/*": ["./src/types/*"],
      "@/constants/*": ["./src/constants/*"]
    }
  },
  "include": [
    "**/*.ts",
    "**/*.tsx",
    ".expo/types/**/*.ts",
    "expo-env.d.ts"
  ],
  "exclude": [
    "node_modules"
  ]
}
```

### `.eslintrc.json`

```json
{
  "extends": ["expo", "prettier"],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint"],
  "rules": {
    "react/react-in-jsx-scope": "off",
    "no-unused-vars": "off",
    "@typescript-eslint/no-unused-vars": ["warn", { "argsIgnorePattern": "^_" }],
    "prettier/prettier": "warn"
  }
}
```

### `.prettierrc`

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": false,
  "printWidth": 100,
  "tabWidth": 2,
  "arrowParens": "always"
}
```

### `jest.config.js`

```javascript
module.exports = {
  preset: "jest-expo",
  transformIgnorePatterns: [
    "node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg)"
  ],
  collectCoverageFrom: [
    "src/**/*.{ts,tsx}",
    "!src/**/*.d.ts",
    "!src/**/__tests__/**"
  ],
  setupFilesAfterEnv: ["@testing-library/jest-native/extend-expect"]
};
```

---

## Step 4: Create Directory Structure (1 hour)

### Reorganize Project

```bash
mkdir -p src/{api,context,hooks,components,utils,types,constants}
mkdir -p src/api/services
mkdir -p src/components/{ui,bot}
```

### Final Structure

```
mobile/
├── app/
│   ├── (auth)/
│   │   ├── _layout.tsx
│   │   └── login.tsx
│   ├── (tabs)/
│   │   ├── _layout.tsx
│   │   ├── index.tsx         # Home/Dashboard
│   │   ├── trades.tsx        # Trade history
│   │   ├── stats.tsx         # Statistics
│   │   └── settings.tsx      # Settings
│   ├── _layout.tsx           # Root layout
│   └── +not-found.tsx
├── src/
│   ├── api/
│   │   ├── client.ts
│   │   ├── services/
│   │   │   ├── auth.ts
│   │   │   ├── bot.ts
│   │   │   ├── trades.ts
│   │   │   └── stats.ts
│   │   └── types.ts
│   ├── context/
│   │   ├── AuthContext.tsx
│   │   └── BotContext.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useBot.ts
│   │   └── useTrades.ts
│   ├── components/
│   │   ├── ui/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   └── Loading.tsx
│   │   └── bot/
│   │       ├── BotStatus.tsx
│   │       ├── TradeCard.tsx
│   │       └── StatsWidget.tsx
│   ├── utils/
│   │   ├── storage.ts
│   │   ├── formatters.ts
│   │   └── validators.ts
│   ├── types/
│   │   ├── index.ts
│   │   └── api.ts
│   └── constants/
│       ├── config.ts
│       ├── colors.ts
│       └── api.ts
├── assets/
├── package.json
├── tsconfig.json
└── app.json
```

---

## Step 5: Create Type Definitions (1-2 hours)

### `src/types/index.ts`

```typescript
// Auth types
export interface User {
  id: string;
  username: string;
  role: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// Bot types
export interface BotStatus {
  running: boolean;
  mode: string;
  symbol: string;
  trades_today: number;
  total_trades: number;
  uptime_seconds: number;
  last_trade_timestamp?: string;
  last_update: string;
}

export interface BotControlResponse {
  status: "started" | "stopped";
  message: string;
  timestamp: string;
}

// Trade types
export type TradeSide = "BUY" | "SELL";
export type TradeStatus = "completed" | "pending" | "failed";

export interface Trade {
  id: string;
  symbol: string;
  side: TradeSide;
  quantity: number;
  price: number;
  executed_at: string;
  status: TradeStatus;
  pnl: number;
  notes?: string;
}

export interface TradeDetail extends Trade {
  entry_price: number;
  exit_price?: number;
  closed_at?: string;
  roi_pct?: number;
  decision_notes?: string;
  chart_image_url?: string;
}

export interface TradesResponse {
  trades: Trade[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

// Stats types
export interface Stats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_profit: number;
  total_loss: number;
  net_pnl: number;
  avg_profit_per_trade: number;
  best_trade: number;
  worst_trade: number;
  sharpe_ratio?: number;
}

// Error types
export interface ApiError {
  error: string;
  message: string;
  status_code: number;
  timestamp: string;
  detail?: any;
}

// Config types
export interface AppConfig {
  apiVersion: string;
  minAppVersion: string;
  maintenanceMode: boolean;
  maintenanceMessage?: string;
  features: {
    live_trading: boolean;
    advanced_orders: boolean;
    ai_signals: boolean;
    paper_trading: boolean;
  };
  limits: {
    max_positions: number;
    max_trades_per_day: number;
    min_account_value: number;
  };
  environment: "production" | "staging" | "development";
}
```

---

## Step 6: Create API Client & Services (2-3 hours)

### `src/constants/api.ts`

```typescript
export const API_CONFIG = {
  BASE_URL: process.env.EXPO_PUBLIC_API_URL || "http://localhost:8004/api/v1",
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
};
```

### `src/utils/storage.ts`

```typescript
import * as SecureStore from "expo-secure-store";

const TOKEN_KEY = "change-me";
const USER_KEY = "user_data";

export async function getToken(): Promise<string | null> {
  try {
    return await SecureStore.getItemAsync(TOKEN_KEY);
  } catch (error) {
    console.error("Failed to get token:"change-me"Failed to set token:"change-me"Failed to remove token:"change-me"Failed to get user data:", error);
    return null;
  }
}

export async function setUserData(userData: any): Promise<void> {
  try {
    await SecureStore.setItemAsync(USER_KEY, JSON.stringify(userData));
  } catch (error) {
    console.error("Failed to set user data:", error);
    throw error;
  }
}

export async function clearAll(): Promise<void> {
  try {
    await removeToken();
    await SecureStore.deleteItemAsync(USER_KEY);
  } catch (error) {
    console.error("Failed to clear storage:", error);
  }
}
```

### `src/api/client.ts`

```typescript
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from "axios";
import { getToken, setToken, removeToken } from "@/utils/storage";
import { ApiError } from "@/types";
import { API_CONFIG } from "@/constants/api";

const client: AxiosInstance = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: Add auth token
client.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const token = await getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle 401 and token refresh
client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as any;

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const errorData = error.response.data;
      
      // If token expired, try to refresh
      if (errorData?.error === "token_expired") {
        try {
          const response = await axios.post(
            `${API_CONFIG.BASE_URL}/auth/refresh`,
            {},
            {
              headers: {
                Authorization: `Bearer ${await getToken()}`,
              },
            }
          );

          const newToken = response.data.access_token;
          await setToken(newToken);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return client(originalRequest);
        } catch (refreshError) {
          // Refresh failed; clear token and reject
          await removeToken();
          return Promise.reject(refreshError);
        }
      } else {
        // Invalid token or other auth issue
        await removeToken();
      }
    }

    return Promise.reject(error);
  }
);

export default client;
```

### `src/api/services/auth.ts`

```typescript
import client from "../client";
import { LoginRequest, LoginResponse, RefreshResponse } from "@/types";

export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  const response = await client.post<LoginResponse>("/auth/login", credentials);
  return response.data;
}

export async function refresh(): Promise<RefreshResponse> {
  const response = await client.post<RefreshResponse>("/auth/refresh");
  return response.data;
}

export async function logout(): Promise<void> {
  // Optional: Call server logout endpoint if exists
  // await client.post("/auth/logout");
}
```

### `src/api/services/bot.ts`

```typescript
import client from "../client";
import { BotStatus, BotControlResponse } from "@/types";

export async function getBotStatus(): Promise<BotStatus> {
  const response = await client.get<BotStatus>("/bot/status");
  return response.data;
}

export async function startBot(): Promise<BotControlResponse> {
  const response = await client.post<BotControlResponse>("/bot/start");
  return response.data;
}

export async function stopBot(): Promise<BotControlResponse> {
  const response = await client.post<BotControlResponse>("/bot/stop");
  return response.data;
}
```

### `src/api/services/trades.ts`

```typescript
import client from "../client";
import { TradesResponse, Trade, TradeDetail } from "@/types";

export interface GetTradesParams {
  limit?: number;
  offset?: number;
  symbol?: string;
  status?: string;
}

export async function getTrades(params: GetTradesParams = {}): Promise<TradesResponse> {
  const { limit = 50, offset = 0, symbol, status } = params;
  
  const queryParams = new URLSearchParams();
  queryParams.append("limit", limit.toString());
  queryParams.append("offset", offset.toString());
  if (symbol) queryParams.append("symbol", symbol);
  if (status) queryParams.append("status", status);

  const response = await client.get<TradesResponse>(`/trades?${queryParams}`);
  return response.data;
}

export async function getTrade(id: string): Promise<TradeDetail> {
  const response = await client.get<TradeDetail>(`/trades/${id}`);
  return response.data;
}
```

---

## Step 7: Create Auth Context (2 hours)

### `src/context/AuthContext.tsx`

```typescript
import React, { createContext, useReducer, useCallback, useEffect } from "react";
import * as authService from "@/api/services/auth";
import * as storage from "@/utils/storage";
import { LoginRequest, User } from "@/types";

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}

interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  clearError: () => void;
}

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
  loading: true,
  error: null,
};

type AuthAction =
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "LOGIN_SUCCESS"; payload: { token: string; user: User } }
  | { type: "LOGIN_ERROR"; payload: string }
  | { type: "LOGOUT" }
  | { type: "REFRESH_TOKEN"; payload: string }
  | { type: "CLEAR_ERROR" };

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case "SET_LOADING":
      return { ...state, loading: action.payload };
    case "LOGIN_SUCCESS":
      return {
        ...state,
        isAuthenticated: true,
        token: action.payload.token,
        user: action.payload.user,
        error: null,
        loading: false,
      };
    case "LOGIN_ERROR":
      return {
        ...state,
        isAuthenticated: false,
        token: null,
        user: null,
        error: action.payload,
        loading: false,
      };
    case "LOGOUT":
      return {
        ...state,
        isAuthenticated: false,
        token: null,
        user: null,
        error: null,
      };
    case "REFRESH_TOKEN":
      return {
        ...state,
        token: action.payload,
      };
    case "CLEAR_ERROR":
      return { ...state, error: null };
    default:
      return state;
  }
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Check stored auth on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = await storage.getToken();
        const userData = await storage.getUserData();

        if (token && userData) {
          dispatch({
            type: "LOGIN_SUCCESS",
            payload: { token, user: userData },
          });
        } else {
          dispatch({ type: "SET_LOADING", payload: false });
        }
      } catch (error) {
        console.error("Auth check failed:", error);
        dispatch({ type: "SET_LOADING", payload: false });
      }
    };

    checkAuth();
  }, []);

  const login = useCallback(async (credentials: LoginRequest) => {
    dispatch({ type: "SET_LOADING", payload: true });
    try {
      const response = await authService.login(credentials);
      
      await storage.setToken(response.access_token);
      await storage.setUserData(response.user);
      
      dispatch({
        type: "LOGIN_SUCCESS",
        payload: { token: response.access_token, user: response.user },
      });
    } catch (error: any) {
      const message = error.response?.data?.message || "Login failed";
      dispatch({ type: "LOGIN_ERROR", payload: message });
      throw error;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error("Logout API call failed:", error);
    } finally {
      await storage.clearAll();
      dispatch({ type: "LOGOUT" });
    }
  }, []);

  const refreshToken = useCallback(async () => {
    try {
      const response = await authService.refresh();
      await storage.setToken(response.access_token);
      dispatch({ type: "REFRESH_TOKEN", payload: response.access_token });
    } catch (error) {
      console.error("Token refresh failed:", error);
      await logout();
    }
  }, [logout]);

  const clearError = useCallback(() => {
    dispatch({ type: "CLEAR_ERROR" });
  }, []);

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    refreshToken,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = React.useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
```

---

## Step 8: Environment Configuration (30 min)

### `.env.example`

```
EXPO_PUBLIC_API_URL=http://localhost:8004/api/v1
EXPO_PUBLIC_APP_VERSION=1.0.0
EXPO_PUBLIC_ENVIRONMENT=development
```

### `.env.local` (git-ignored)

```
EXPO_PUBLIC_API_URL=http://192.0.2.21:8004/api/v1
EXPO_PUBLIC_APP_VERSION=1.0.0
EXPO_PUBLIC_ENVIRONMENT=development
```

### `.gitignore`

```
# Expo
.expo/
dist/
web-build/

# Environment
.env
.env.local
.env.production

# Dependencies
node_modules/

# IDE
.vscode/
.idea/

# OS
.DS_Store
*.swp
```

---

## Step 9: Testing & Verification (2-3 hours)

### Manual Testing Checklist

```bash
# Start development server
cd mobile
npm start

# Run on simulator/device
# iOS: Press 'i'
# Android: Press 'a'
# Web: Press 'w'
```

### Checklist

- [ ] App starts without errors
- [ ] TypeScript compiles (`npm run type-check`)
- [ ] Linting passes (`npm run lint`)
- [ ] Can navigate between screens (once navigation implemented)
- [ ] API client configured correctly
- [ ] Auth context initializes
- [ ] Token storage/retrieval works (test in DevTools)
- [ ] Environment variables load correctly

### Next Steps

After Phase 3-A:
1. **Phase 3-B:** Build auth screens (login UI)
2. **Phase 3-C:** Build main app screens (dashboard, trades, stats, settings)
3. **Phase 3-D:** Polish (loading, errors, accessibility)
4. **Phase 3-E:** Build & release

---

## Time Estimate

| Task | Time |
|------|------|
| Initialize project | 1-2 hours |
| Install dependencies | 1-2 hours |
| Configure TypeScript | 1 hour |
| Create directory structure | 1 hour |
| Type definitions | 1-2 hours |
| API client & services | 2-3 hours |
| Auth context | 2 hours |
| Environment & testing | 2-3 hours |
| **Total** | **11-16 hours** |

**Recommendation:** 1 mobile engineer, 2-3 days full-time work.
