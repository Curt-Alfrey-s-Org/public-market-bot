# Phase 2-B through 2-E: Mobile API Finalization Guide

**Status:** Ready for implementation  
**Estimated Time:** 9-13 hours  
**Dependencies:** Phase 2-A complete ✅

---

## Overview

Phase 2-A established the `/api/v1/` route structure. This phase completes the mobile API by adding:
- **2-B:** Global error handling with consistent schema
- **2-C:** Token lifecycle (JWT with 24h expiry + refresh)
- **2-D:** Rate limiting middleware
- **2-E:** Integration tests and validation

---

## Phase 2-B: Error Response Integration (2-3 hours)

### Goal
All API endpoints return consistent error responses with standardized schema.

### Error Response Schema

```python
# api/models/error.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ErrorResponse(BaseModel):
    error: str  # Error code: "unauthorized", "not_found", "validation_error", etc.
    message: str  # Human-readable message
    status_code: int  # HTTP status code
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    detail: Optional[dict] = None  # Optional context (field errors, etc.)
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "unauthorized",
                "message": "Missing authorization token",
                "status_code": 401,
                "timestamp": "2026-02-12T10:30:00Z"
            }
        }
```

### Standard Error Codes

| HTTP Status | Error Code | When to Use |
|-------------|-----------|-------------|
| 400 | `validation_error` | Invalid request body, bad parameters |
| 401 | `unauthorized` | Missing/invalid/expired token |
| 403 | `forbidden` | User lacks permission |
| 404 | `not_found` | Resource doesn't exist |
| 429 | `rate_limited` | Too many requests |
| 500 | `server_error` | Unexpected server exception |
| 503 | `service_unavailable` | Bot initializing or maintenance |

### Implementation Steps

**Step 1: Create Error Middleware**

```python
# api/middleware/error_handler.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from api.models.error import ErrorResponse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException with consistent error format"""
    error_code = "unknown_error"
    
    # Map status codes to error codes
    if exc.status_code == 400:
        error_code = "validation_error"
    elif exc.status_code == 401:
        error_code = "unauthorized"
    elif exc.status_code == 403:
        error_code = "forbidden"
    elif exc.status_code == 404:
        error_code = "not_found"
    elif exc.status_code == 429:
        error_code = "rate_limited"
    elif exc.status_code >= 500:
        error_code = "server_error"
    
    # If detail is a dict with error code, use it
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        error_code = exc.detail["error"]
        message = exc.detail.get("message", str(exc.detail))
    else:
        message = str(exc.detail)
    
    error_response = ErrorResponse(
        error=error_code,
        message=message,
        status_code=exc.status_code,
        timestamp=datetime.utcnow()
    )
    
    logger.warning(f"HTTP {exc.status_code}: {error_code} - {message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors from Pydantic"""
    error_response = ErrorResponse(
        error="validation_error",
        message="Request validation failed",
        status_code=422,
        timestamp=datetime.utcnow(),
        detail={"errors": exc.errors()}
    )
    
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content=error_response.dict()
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all for unexpected exceptions"""
    logger.error(f"Unexpected error: {type(exc).__name__}: {str(exc)}", exc_info=True)
    
    error_response = ErrorResponse(
        error="server_error",
        message="An unexpected error occurred",
        status_code=500,
        timestamp=datetime.utcnow()
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )
```

**Step 2: Register Middleware in `api/main.py`**

```python
# api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from api.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)

app = FastAPI()

# Register exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# ... rest of app setup ...
```

**Step 3: Update Routes to Use Consistent Errors**

Example in `api/routes/v1/auth.py`:

```python
from fastapi import HTTPException

@router.post("/login")
async def login(credentials: LoginRequest):
    user = await authenticate_user(credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_credentials",
                "message": "Username or password is incorrect"
            }
        )
    
    # ... generate token ...
    return response
```

**Step 4: Testing**

```bash
# Test missing auth
curl http://localhost:8004/api/v1/bot/status
# Expected: 401 {"error": "unauthorized", "message": "...", "status_code": 401, "timestamp": "..."}

# Test invalid trade ID
curl -H "Authorization: Bearer <token>" http://localhost:8004/api/v1/trades/invalid-id
# Expected: 404 {"error": "not_found", "message": "Trade not found", ...}

# Test invalid JSON
curl -X POST http://localhost:8004/api/v1/auth/login \
  -H "Content-Type: application/json" -d '{invalid json}'
# Expected: 422 {"error": "validation_error", ...}
```

### Checklist

- [ ] Error models created in `api/models/error.py`
- [ ] Error middleware created in `api/middleware/error_handler.py`
- [ ] Middleware registered in `api/main.py`
- [ ] All routes return consistent error format
- [ ] 401 used for missing/invalid auth (not 403)
- [ ] 404 for missing resources
- [ ] 500 errors don't leak internal details
- [ ] Manual tests pass

---

## Phase 2-C: Token Lifecycle Management (2-3 hours)

### Goal
Full JWT-based authentication with 24-hour expiry and refresh capability.

### JWT Structure

```json
{
  "sub": "user_id_123",
  "exp": 1739462400,
  "iat": 1739376000,
  "token_type": "change-me"
}
```

### Implementation Steps

**Step 1: Install Dependencies**

```bash
pip install pyjwt[crypto] python-dotenv
```

**Step 2: Create Token Utilities**

```python
# api/utils/jwt.py
from datetime import datetime, timedelta
from typing import Optional
import jwt
from api.config import settings

TOKEN_ALGORITHM = "change-me"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_GRACE_PERIOD_DAYS = 7

def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "token_type": "change-me"
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=TOKEN_ALGORITHM)
    return token

def decode_token(token: str, verify_exp: bool = True) -> dict:
    """Decode and validate JWT token"""
    options = {"verify_exp": verify_exp}
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[TOKEN_ALGORITHM],
            options=options
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

def is_token_refreshable(token: str) -> bool:
    """Check if expired token is still within refresh grace period"""
    try:
        payload = decode_token(token, verify_exp=False)
        exp_timestamp = payload.get("exp")
        if not exp_timestamp:
            return False
        
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        grace_cutoff = datetime.utcnow() - timedelta(days=REFRESH_GRACE_PERIOD_DAYS)
        
        return exp_datetime > grace_cutoff
    except Exception:
        return False
```

**Step 3: Update Auth Routes**

```python
# api/routes/v1/auth.py
from fastapi import APIRouter, HTTPException, Header
from api.utils.jwt import create_access_token, decode_token, is_token_refreshable
from api.models.auth import LoginRequest, LoginResponse, RefreshResponse
from datetime import timedelta

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """Authenticate user and return access token"""
    # Validate credentials (check database)
    user = await authenticate_user(credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_credentials",
                "message": "Username or password is incorrect"
            }
        )
    
    # Generate token
    access_token = create_access_token(user["id"])
    
    return LoginResponse(
        access_token=access_token,
        token_type="change-me",
        expires_in=86400,  # 24 hours in seconds
        user={
            "id": user["id"],
            "username": user["username"],
            "role": user.get("role", "user")
        }
    )

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(authorization: str = Header(...)):
    """Refresh access token"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "unauthorized",
                "message": "Invalid authorization header format"
            }
        )
    
    token = authorization.split(" ")[1]
    
    # Try to decode token (allow expired)
    try:
        payload = decode_token(token, verify_exp=False)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_token",
                "message": "Token is invalid"
            }
        )
    
    # Check if token is within refresh grace period
    if not is_token_refreshable(token):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "token_expired",
                "message": "Token is too old to refresh. Please log in again."
            }
        )
    
    # Generate new token
    user_id = payload.get("sub")
    new_token = create_access_token(user_id)
    
    return RefreshResponse(
        access_token=new_token,
        token_type="change-me",
        expires_in=86400
    )
```

**Step 4: Create Auth Dependency for Protected Routes**

```python
# api/dependencies/auth.py
from fastapi import HTTPException, Header
from api.utils.jwt import decode_token

async def get_current_user(authorization: str = Header(...)) -> str:
    """Dependency to validate token and return current user ID"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "unauthorized",
                "message": "Missing authorization token"
            }
        )
    
    token = authorization.split(" ")[1]
    
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise ValueError("Token missing user ID")
        
        return user_id
    except ValueError as e:
        if "expired" in str(e).lower():
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "token_expired",
                    "message": "Token has expired. Use /api/v1/auth/refresh to get a new token."
                }
            )
        else:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "invalid_token",
                    "message": "Invalid authentication token"
                }
            )
```

**Step 5: Use Dependency in Protected Routes**

```python
# api/routes/v1/bot.py
from fastapi import APIRouter, Depends
from api.dependencies.auth import get_current_user

router = APIRouter()

@router.get("/status")
async def get_bot_status(current_user: str = Depends(get_current_user)):
    """Get bot status (requires authentication)"""
    # current_user contains user_id from token
    # ... fetch and return bot status ...
    return {"running": True, "mode": "yfinance", ...}
```

**Step 6: Testing**

```bash
# Login
TOKEN=$(curl -X POST http://localhost:8004/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo"}' | jq -r '.access_token')

# Use token
curl http://localhost:8004/api/v1/bot/status \
  -H "Authorization: Bearer $TOKEN"

# Refresh token (before expiry)
NEW_TOKEN=$(curl -X POST http://localhost:8004/api/v1/auth/refresh \
  -H "Authorization: Bearer $TOKEN" | jq -r '.access_token')

# Use new token
curl http://localhost:8004/api/v1/bot/status \
  -H "Authorization: Bearer $NEW_TOKEN"
```

### Checklist

- [ ] JWT utilities created (`create_access_token`, `decode_token`)
- [ ] Login endpoint returns token with `expires_in: 86400`
- [ ] Refresh endpoint validates token and issues new one
- [ ] 7-day grace period for refresh implemented
- [ ] Auth dependency created for protected routes
- [ ] All protected routes use `Depends(get_current_user)`
- [ ] Expired tokens return 401 with `error: "token_expired"`
- [ ] Manual token flow tested

---

## Phase 2-D: Rate Limiting Middleware (2-3 hours)

### Goal
Prevent API abuse with configurable rate limits.

### Rate Limit Configuration

| Endpoint Category | Limit | Window |
|------------------|-------|--------|
| General (bot, trades, stats) | 60 requests | 1 minute |
| Auth (login, refresh) | 10 requests | 1 minute |
| Bot Control (start, stop) | 30 requests | 1 hour |

### Implementation Steps

**Step 1: Install Dependencies**

```bash
pip install slowapi
```

**Step 2: Create Rate Limiter**

```python
# api/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Step 3: Apply Rate Limits to Routes**

```python
# api/routes/v1/auth.py
from slowapi import Limiter
from fastapi import Request

@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, credentials: LoginRequest):
    # ... login logic ...
    pass

@router.post("/refresh")
@limiter.limit("10/minute")
async def refresh_token(request: Request, authorization: str = Header(...)):
    # ... refresh logic ...
    pass
```

```python
# api/routes/v1/bot.py
@router.get("/status")
@limiter.limit("60/minute")
async def get_bot_status(request: Request, current_user: str = Depends(get_current_user)):
    # ... status logic ...
    pass

@router.post("/start")
@limiter.limit("30/hour")
async def start_bot(request: Request, current_user: str = Depends(get_current_user)):
    # ... start logic ...
    pass
```

**Step 4: Custom Rate Limit Error Handler**

```python
# api/middleware/error_handler.py
from slowapi.errors import RateLimitExceeded

async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded with consistent error format"""
    retry_after = exc.headers.get("Retry-After", "60")
    
    error_response = ErrorResponse(
        error="rate_limited",
        message=f"Too many requests. Please retry after {retry_after} seconds.",
        status_code=429,
        timestamp=datetime.utcnow(),
        detail={"retry_after": int(retry_after)}
    )
    
    return JSONResponse(
        status_code=429,
        content=error_response.dict(),
        headers={"Retry-After": str(retry_after)}
    )

# Register in api/main.py
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
```

**Step 5: Testing**

```bash
# Test rate limiting (login endpoint: 10/minute)
for i in {1..11}; do
  echo "Request $i"
  curl -X POST http://localhost:8004/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "test", "password": "test"}'
  echo "\n"
done

# 11th request should return 429 with Retry-After header
```

### Checklist

- [ ] slowapi installed
- [ ] Rate limiter configured in `api/main.py`
- [ ] Auth endpoints limited to 10/minute
- [ ] General endpoints limited to 60/minute
- [ ] Bot control limited to 30/hour
- [ ] 429 response includes `Retry-After` header
- [ ] Error format consistent with ErrorResponse schema
- [ ] Rate limit testing verified

---

## Phase 2-E: Integration Tests (3-4 hours)

### Goal
Comprehensive end-to-end testing of all v1 API flows.

### Test Structure

```
tests/backend/
├── test_api_v1_integration.py     # Full flow tests
├── test_token_lifecycle.py        # Token generation, expiry, refresh
├── test_error_responses.py        # Error format validation
└── test_rate_limiting.py          # Rate limit enforcement
```

### Implementation Steps

**Step 1: Create Integration Test Suite**

```python
# tests/backend/test_api_v1_integration.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

class TestAuthFlow:
    def test_full_auth_lifecycle(self):
        """Test login → use token → refresh → use new token"""
        # 1. Login
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "change-me"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["expires_in"] == 86400
        
        token = data["access_token"]
        
        # 2. Use token to access protected endpoint
        response = client.get(
            "/api/v1/bot/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # 3. Refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        new_token = response.json()["access_token"]
        assert new_token != token
        
        # 4. Use new token
        response = client.get(
            "/api/v1/bot/status",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        assert response.status_code == 200
    
    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post("/api/v1/auth/login", json={
            "username": "invalid",
            "password": "wrong"
        })
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "invalid_credentials"
        assert "status_code" in data
        assert "timestamp" in data
    
    def test_missing_auth(self):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/v1/bot/status")
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "unauthorized"
        assert "message" in data

class TestBotControl:
    def test_bot_status(self, auth_token):
        """Test getting bot status"""
        response = client.get(
            "/api/v1/bot/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert "mode" in data
        assert "trades_today" in data
    
    def test_bot_start_stop(self, auth_token):
        """Test starting and stopping bot"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Start bot
        response = client.post("/api/v1/bot/start", headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "started"
        
        # Stop bot
        response = client.post("/api/v1/bot/stop", headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "stopped"

class TestTradePagination:
    def test_get_trades_default(self, auth_token):
        """Test getting trades with default pagination"""
        response = client.get(
            "/api/v1/trades",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "trades" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data
    
    def test_get_trades_with_limit(self, auth_token):
        """Test getting trades with custom limit"""
        response = client.get(
            "/api/v1/trades?limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) <= 10
    
    def test_get_trade_by_id(self, auth_token):
        """Test getting single trade"""
        response = client.get(
            "/api/v1/trades/trade_123",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # May be 200 or 404 depending on data
        assert response.status_code in [200, 404]

@pytest.fixture
def auth_token():
    """Fixture to get auth token for tests"""
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "change-me"
    })
    return response.json()["access_token"]
```

**Step 2: Create Token Lifecycle Tests**

```python
# tests/backend/test_token_lifecycle.py
import pytest
from datetime import datetime, timedelta
from api.utils.jwt import create_access_token, decode_token, is_token_refreshable
import time

def test_token_creation():
    """Test JWT token creation"""
    user_id = "test_user_123"
    token = create_access_token(user_id)
    
    assert token is not None
    assert isinstance(token, str)
    
    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert "exp" in payload
    assert "iat" in payload

def test_token_expiry():
    """Test token expiry validation"""
    # Create token that expires in 1 second
    token = create_access_token("test_user", timedelta(seconds=1))
    
    # Token should be valid immediately
    payload = decode_token(token)
    assert payload["sub"] == "test_user"
    
    # Wait for expiry
    time.sleep(2)
    
    # Token should now be expired
    with pytest.raises(ValueError, match="expired"):
        decode_token(token)

def test_token_refresh_grace_period():
    """Test 7-day refresh grace period"""
    # Create token expired 3 days ago
    token = create_access_token("test_user", timedelta(days=-3))
    
    # Should still be refreshable (within 7-day grace)
    assert is_token_refreshable(token) == True
    
    # Create token expired 10 days ago
    token_old = create_access_token("test_user", timedelta(days=-10))
    
    # Should NOT be refreshable (beyond grace period)
    assert is_token_refreshable(token_old) == False
```

**Step 3: Run Tests**

```bash
# Run all Phase 2 tests
python -m pytest tests/backend/test_api_v1_integration.py -v
python -m pytest tests/backend/test_token_lifecycle.py -v
python -m pytest tests/backend/test_error_responses.py -v
python -m pytest tests/backend/test_rate_limiting.py -v

# Run with coverage
python -m pytest tests/backend/ --cov=api --cov-report=html
```

### Checklist

- [ ] Integration test suite created
- [ ] Full auth flow tested (login → use → refresh)
- [ ] Error responses validated
- [ ] Token lifecycle tested
- [ ] Rate limiting tested
- [ ] All tests pass
- [ ] Code coverage > 80%

---

## Verification & Handoff

### Manual Smoke Test

```bash
# 1. Login
curl -X POST http://localhost:8004/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo"}'

# 2. Get bot status
curl -H "Authorization: Bearer <token>" \
  http://localhost:8004/api/v1/bot/status

# 3. Get trades
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8004/api/v1/trades?limit=10"

# 4. Refresh token
curl -X POST http://localhost:8004/api/v1/auth/refresh \
  -H "Authorization: Bearer <token>"

# 5. Get config (no auth)
curl http://localhost:8004/api/v1/config
```

### Completion Criteria

- [ ] All error responses use ErrorResponse schema
- [ ] JWT tokens generated with 24h expiry
- [ ] Token refresh endpoint working
- [ ] Rate limiting active on all endpoints
- [ ] Integration tests pass (>30 tests)
- [ ] `docs/MOBILE_API.md` updated
- [ ] Mobile team can build app with confidence

### Next Steps

After Phase 2 completion:
1. **Phase 3-A:** Initialize Expo React Native project
2. **Phase 3-B:** Build auth screens (login, signup)
3. **Phase 3-C:** Build main app screens (dashboard, trades, stats, settings)
4. **Phase 3-D:** Polish (loading states, error handling, accessibility)
5. **Phase 3-E:** Build & release to TestFlight/Google Play

---

## Time Estimate Summary

| Phase | Task | Time | Total |
|-------|------|------|-------|
| 2-B | Error Response Integration | 2-3 hours | 2.5h |
| 2-C | Token Lifecycle | 2-3 hours | 2.5h |
| 2-D | Rate Limiting | 2-3 hours | 2.5h |
| 2-E | Integration Tests | 3-4 hours | 3.5h |
| **TOTAL** | | | **11 hours** |

**Recommended:** 1-2 backend engineers working in parallel can complete in 2-3 days.
