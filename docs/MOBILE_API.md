# Market Bot Mobile API (V1)

**Base URL:** `https://market-bot.example.com/api/v1`  
**API Version:** v1  
**Last Updated:** February 12, 2026  
**Status:** Stable & Ready for Production

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Authentication](#auth-endpoints)
  - [Bot Control](#bot-control-endpoints)
  - [Trades](#trades-endpoints)
  - [Statistics](#statistics-endpoints)
  - [Settings](#settings-endpoints)
  - [Configuration](#configuration-endpoints)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Timestamps](#timestamps)

---

## Overview

The Market Bot Mobile API provides a stable, versioned REST API for native iOS/Android applications and web clients to interact with the trading bot.

**Key Features:**
- ✓ Token-based authentication (JWT)
- ✓ Consistent error responses
- ✓ Token refresh mechanism (24-hour expiry with 7-day grace period)
- ✓ Paginated list endpoints
- ✓ Feature flags via config endpoint
- ✓ Minimal response overhead for mobile networks
- ✓ No breaking changes within v1 (backward compatible)

---

## Authentication

### Overview

All endpoints (except `/auth/login` and `/auth/refresh`) require Bearer token authentication:

```
Authorization: Bearer <access_token>
```

### Token Lifespan

- **Token Expiry:** 24 hours (86,400 seconds)
- **Refresh Grace Period:** 7 days after expiry
- **Recommendation:** Call `/api/v1/auth/refresh` every 20 hours to avoid expiry

### Authentication Flow (Mobile App)

1. **First Launch / Login:**
   ```
   POST /api/v1/auth/login
   {
     "username": "operator@example.com",
     "password": "change-me"
   }
   ```
   → Returns: `access_token`, `expires_in` (seconds), user info

2. **Store Token Securely:**
   - iOS: Keychain
   - Android: Android Keystore
   - Web: Secure HttpOnly cookie (backend) or encrypted localStorage

3. **Make Authenticated Requests:**
   ```
   GET /api/v1/bot/status
   Authorization: Bearer <access_token>
   ```

4. **Token Expiry / Refresh:**
   ```
   POST /api/v1/auth/refresh
   Authorization: Bearer <current_token>
   ```
   → Returns: new `access_token` with fresh expiry

---

## Endpoints

### Authentication

#### POST /auth/login

**Login with username and password.**

**Request:**
```json
{
  "username": "operator@example.com",
  "password": "change-me"
}
```

**Response (200 OK):**
```json
{
  "access_token": "change-me",
  "token_type": "change-me",
  "expires_in": 86400,
  "user": {
    "id": "user-123",
    "username": "operator@example.com",
    "role": "trader"
  }
}
```

**Error Responses:**
- `400`: Missing username or password
- `401`: Invalid credentials
- `401`: Email not verified (registration pending)

**cURL Example:**
```bash
curl -X POST "https://market-bot.example.com/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "<ADMIN_USERNAME>",
    "password": "change-me"
  }'
```

---

#### POST /auth/refresh

**Refresh access token before expiry.**

**Headers:**
```
Authorization: Bearer <current_token>
```

**Request Body:** Empty (token in header)

**Response (200 OK):**
```json
{
  "access_token": "change-me",
  "token_type": "change-me",
  "expires_in": 86400
}
```

**Error Responses:**
- `401`: Token missing or invalid
- `401`: Token expired (not in grace period)
- `401`: Token too old (> 7 days since expiry)

**cURL Example:**
```bash
curl -X POST "https://market-bot.example.com/api/v1/auth/refresh" \
  -H "Authorization: Bearer <current_token>"
```

---

### Bot Control

#### GET /bot/status

**Get current bot status and running statistics.**

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "running": true,
  "mode": "yfinance",
  "symbol": "AAPL",
  "trades_today": 3,
  "total_trades": 152,
  "uptime_seconds": 3600,
  "last_trade_timestamp": "2026-02-12T10:15:30Z",
  "last_update": "2026-02-12T10:30:45Z"
}
```

**Field Descriptions:**
- `running` (bool): Is bot actively trading?
- `mode` (string): 'yfinance' | 'sandbox' | 'live' | 'dryrun-live'
- `symbol` (string | null): Current trading symbol
- `trades_today` (int): Trades executed today (UTC)
- `total_trades` (int): Cumulative trade count
- `uptime_seconds` (int): Bot runtime in seconds
- `last_trade_timestamp` (string | null): ISO 8601 or null
- `last_update` (string): ISO 8601 timestamp of response

**Error Responses:**
- `401`: Unauthorized
- `500`: Internal server error

**cURL Example:**
```bash
curl -X GET "https://market-bot.example.com/api/v1/bot/status" \
  -H "Authorization: Bearer <access_token>"
```

---

#### POST /bot/start

**Start the trading bot.**

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:** Empty

**Response (200 OK):**
```json
{
  "status": "started",
  "message": "Bot started successfully",
  "timestamp": "2026-02-12T10:30:45Z"
}
```

**Error Responses:**
- `400`: Bot already running
- `401`: Unauthorized
- `500`: Failed to start bot

---

#### POST /bot/stop

**Stop the trading bot.**

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:** Empty

**Response (200 OK):**
```json
{
  "status": "stopped",
  "message": "Bot stopped successfully",
  "timestamp": "2026-02-12T10:30:45Z"
}
```

**Error Responses:**
- `400`: Bot not running
- `401`: Unauthorized
- `500`: Failed to stop bot

---

### Trades

#### GET /trades

**Get list of trades with pagination.**

**Query Parameters:**
- `limit` (int): Items per page (1-1000, default 50)
- `offset` (int): Starting position (0-indexed, default 0)
- `symbol` (string | optional): Filter by stock symbol (e.g., 'AAPL')
- `status` (string | optional): Filter by status ('completed' | 'pending' | 'failed')

**Response (200 OK):**
```json
{
  "trades": [
    {
      "id": "trade-123",
      "symbol": "AAPL",
      "side": "BUY",
      "quantity": 10,
      "price": 150.50,
      "executed_at": "2026-02-12T10:15:30Z",
      "status": "completed",
      "pnl": 50.25,
      "notes": "Signal quality 85%"
    }
  ],
  "total": 152,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

**Field Descriptions:**
- `trades[]` (array): Trade summaries
  - `id`: Unique trade identifier
  - `symbol`: Stock symbol
  - `side`: 'BUY' or 'SELL'
  - `quantity`: Shares traded
  - `price`: Execution price per share
  - `executed_at`: ISO 8601 timestamp
  - `status`: 'completed', 'pending', 'failed'
  - `pnl`: Profit/loss in dollars (or null)
  - `notes`: Optional signal strength or notes
- `total`: Total count of trades matching filters
- `limit`: Items per page
- `offset`: Starting position
- `has_more`: Boolean indicating more pages exist

**Error Responses:**
- `400`: Invalid parameters
- `401`: Unauthorized

**cURL Example:**
```bash
curl -X GET "https://market-bot.example.com/api/v1/trades?limit=20&offset=0" \
  -H "Authorization: Bearer <access_token>"
```

---

#### GET /trades/{id}

**Get detailed information about a specific trade.**

**Path Parameters:**
- `id` (string): Trade ID

**Response (200 OK):**
```json
{
  "id": "trade-123",
  "symbol": "AAPL",
  "side": "BUY",
  "quantity": 10,
  "entry_price": 150.50,
  "exit_price": 152.00,
  "executed_at": "2026-02-12T10:15:30Z",
  "closed_at": "2026-02-12T14:30:00Z",
  "status": "completed",
  "pnl": 15.00,
  "roi_pct": 0.99,
  "decision_notes": "Signal quality 85%, momentum positive",
  "chart_image_url": "https://..."
}
```

**Error Responses:**
- `401`: Unauthorized
- `404`: Trade not found

---

### Statistics

#### GET /stats/overall

**Get overall trading statistics.**

**Response (200 OK):**
```json
{
  "win_rate": 65.5,
  "total_trades": 152,
  "winning_trades": 100,
  "losing_trades": 52,
  "profit_loss": 1250.50,
  "roi": 12.5,
  "avg_win": 25.50,
  "avg_loss": -10.25,
  "best_trade": 150.00,
  "worst_trade": -75.00,
  "max_drawdown": 5.2,
  "average_holding_time_hours": 4.5
}
```

**Error Responses:**
- `401`: Unauthorized
- `500`: Internal error

---

#### GET /stats/today

**Get today's trading statistics (UTC day).**

---

#### GET /stats/week

**Get this week's trading statistics.**

---

#### GET /stats/month

**Get this month's trading statistics.**

---

### Settings

#### GET /settings

**Get current bot configuration.**

**Response (200 OK):**
```json
{
  "mode": "yfinance",
  "max_positions": 5,
  "paper_trading_mode": true,
  "symbols": ["AAPL", "SPY", "QQQ"],
  "risk_per_trade": 0.02,
  "take_profit_pct": 2.5,
  "stop_loss_pct": 1.5,
  "last_updated": "2026-02-12T10:00:00Z"
}
```

---

#### POST /settings

**Update bot configuration (admin only).**

**Request (partial update allowed):**
```json
{
  "max_positions": 10,
  "risk_per_trade": 0.03
}
```

**Response (200 OK):**
```json
{
  "mode": "yfinance",
  "max_positions": 10,
  "paper_trading_mode": true,
  "symbols": ["AAPL", "SPY", "QQQ"],
  "risk_per_trade": 0.03,
  "take_profit_pct": 2.5,
  "stop_loss_pct": 1.5,
  "last_updated": "2026-02-12T10:05:00Z"
}
```

**Error Responses:**
- `401`: Unauthorized
- `403`: Admin permissions required
- `500`: Failed to update

---

### Configuration

#### GET /config

**Get app configuration and feature flags.**

**Response (200 OK):**
```json
{
  "minAppVersion": "1.0.0",
  "maintenanceMode": false,
  "features": {
    "live_trading": false,
    "advanced_orders": false,
    "ai_signals": true
  },
  "apiVersion": "v1"
}
```

**Field Descriptions:**
- `minAppVersion`: Minimum app version required (e.g., "1.0.0")
- `maintenanceMode`: If true, API under maintenance
- `features`: Feature flags to enable/disable UI features
- `apiVersion`: Current API version ("v1")

**Mobile App Usage Example:**
```javascript
// On app launch
const config = await fetch('/api/v1/config').then(r => r.json());

if (config.maintenanceMode) {
  showAlert("The API is under maintenance. Please try again later.");
  return;
}

if (config.minAppVersion > appVersion) {
  showAlert("Please update the app to continue.");
  openAppStore();
  return;
}

// Show/hide features based on flags
if (config.features.ai_signals) {
  showAISignalsUI();
}
```

---

## Error Handling

### Standard Error Response

All errors follow this format:

```json
{
  "error": "error_code",
  "message": "Human-readable message",
  "status_code": 401,
  "timestamp": "2026-02-12T10:30:45Z",
  "detail": null
}
```

### Error Codes

| HTTP Status | Error Code | Meaning | Example |
|-------------|-----------|---------|---------|
| 400 | `validation_error` | Invalid request body or parameters | Missing required field |
| 401 | `unauthorized` | Missing or invalid authentication token | Invalid credentials |
| 403 | `forbidden` | User lacks required permissions | Non-admin updating settings |
| 404 | `not_found` | Resource not found | Trade ID doesn't exist |
| 429 | `rate_limited` | Too many requests | Exceeded 60 req/minute |
| 500 | `server_error` | Unexpected server error | Database connection failed |

### Mobile App Error Handling Example

```javascript
async function getStatus() {
  try {
    const response = await fetch('/api/v1/bot/status', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (!response.ok) {
      const error = await response.json();
      
      if (error.status_code === 401) {
        // Token expired or invalid
        // Try refresh:
        await refreshToken();
        // Retry request
        return getStatus();
      }
      
      if (error.status_code === 403) {
        // User doesn't have permission
        showAlert("Access denied: " + error.message);
        return;
      }
      
      // Other errors
      throw new Error(error.message || 'Unknown error');
    }
    
    return await response.json();
  } catch (err) {
    console.error('Error:', err);
    showAlert('Failed: ' + err.message);
  }
}
```

---

## Rate Limiting

### Limits

- **General Endpoints:** 60 requests per minute
- **Auth Endpoints:** 10 requests per minute per IP

### Rate Limit Headers

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1613056245
```

### Exceeding Limit

Returns `HTTP 429`:
```json
{
  "error": "rate_limited",
  "message": "Too many requests. Please wait before retrying.",
  "status_code": 429,
  "timestamp": "2026-02-12T10:30:45Z",
  "detail": {
    "retry_after_seconds": 60
  }
}
```

---

## Pagination

### Query Parameters

- `limit` (int): Items per page (default 50, max 1000)
- `offset` (int): Starting position (0-indexed, default 0)

### Response Format

```json
{
  "trades": [...],
  "total": 152,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

### Pagination Example

**Page 1 (first 50):**
```
GET /api/v1/trades?limit=50&offset=0
```

**Page 2 (next 50):**
```
GET /api/v1/trades?limit=50&offset=50
```

**All Pages:**
```javascript
let offset = 0;
let allTrades = [];

while (true) {
  const response = await fetch(
    `/api/v1/trades?limit=100&offset=${offset}`
  ).then(r => r.json());
  
  allTrades = allTrades.concat(response.trades);
  
  if (!response.has_more) break;
  offset += response.limit;
}
```

---

## Timestamps

### Format

All timestamps are **ISO 8601** in **UTC**:

```
2026-02-12T10:30:45Z
```

### Parsing in Different Languages

**JavaScript:**
```javascript
const date = new Date('2026-02-12T10:30:45Z');
```

**Python:**
```python
from datetime import datetime
dt = datetime.fromisoformat('2026-02-12T10:30:45Z'.replace('Z', '+00:00'))
```

**Swift (iOS):**
```swift
let formatter = ISO8601DateFormatter()
let date = formatter.date(from: "2026-02-12T10:30:45Z")
```

**Java (Android):**
```java
Instant instant = Instant.parse("2026-02-12T10:30:45Z");
```

---

## Getting Started (Mobile App)

### 1. Initialize

```javascript
const API_BASE = "https://market-bot.example.com/api/v1";
let token = null;
```

### 2. Login

```javascript
async function login(username, password) {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message);
  }
  
  const data = await response.json();
  token = data.access_token;
  localStorage.setItem('token', token);
  localStorage.setItem('expires_at', Date.now() + data.expires_in * 1000);
  
  return data.user;
}
```

### 3. Make Authenticated Request

```javascript
async function getBotStatus() {
  const response = await fetch(`${API_BASE}/bot/status`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  if (!response.ok) throw new Error(await response.text());
  return await response.json();
}
```

### 4. Handle Token Refresh

```javascript
async function ensureValidToken() {
  const expiresAt = localStorage.getItem('expires_at');
  if (Date.now() > expiresAt - 3600000) { // Refresh 1 hour before expiry
    await refreshToken();
  }
}

async function refreshToken() {
  const response = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  if (!response.ok) {
    // Token refresh failed, require re-login
    localStorage.removeItem('token');
    location.hash = '#login';
    return;
  }
  
  const data = await response.json();
  token = data.access_token;
  localStorage.setItem('token', token);
  localStorage.setItem('expires_at', Date.now() + data.expires_in * 1000);
}
```

### 5. Auto-Refresh Pattern

```javascript
// Call before each request
async function apiCall(endpoint, options = {}) {
  await ensureValidToken();
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) throw new Error(await response.text());
  return await response.json();
}
```

---

## Changelog

### v1.0.0 (February 12, 2026)
- ✓ Initial release
- ✓ Authentication with JWT + refresh token
- ✓ Bot control endpoints (status, start, stop)
- ✓ Trades list and detail endpoints
- ✓ Statistics endpoints (overall, today, week, month)
- ✓ Settings management
- ✓ Feature flags via config endpoint
- ✓ Comprehensive error handling
- ✓ Rate limiting
- ✓ Pagination support

---

## Support

For issues or questions:
1. Check error message and timestamp
2. Review endpoint documentation
3. Verify token is valid and not expired
4. Check rate limit headers
5. Contact development team

---

**API Version:** v1 | **Status:** Production | **Last Updated:** Feb 12, 2026
