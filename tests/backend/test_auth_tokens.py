"""
Phase 2-C Tests: Token Refresh Lifecycle
=========================================
Verify token expiry, refresh mechanism, and auth middleware.
"""

import pytest
from fastapi.testclient import TestClient
import jwt
import os
import time
from datetime import datetime, timedelta, timezone
import json

# Get settings before importing app
from api.main import app, BOT_API_KEY
from api.utils.jwt import SECRET_KEY  # v1 tokens are signed by api/utils/jwt.py
from api.auth import create_access_token

# All /api/* routes except health and /api/auth require X-API-Key (RequireApiKeyMiddleware)
client = TestClient(app, headers={"X-API-Key": BOT_API_KEY})

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24


def _utcnow() -> datetime:
    """Naive UTC now (datetime.utcnow() is deprecated since Python 3.12)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TestTokenExpiry:
    """Verify token expiry claims and behavior."""
    
    def test_login_returns_token_with_correct_expiry(self):
        """Test login returns token with 24-hour expiry."""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "change-me"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify token structure
        assert "access_token" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
        
        # Verify expires_in is 86400 seconds (24 hours)
        assert data["expires_in"] == 86400
    
    def test_token_has_valid_exp_claim(self):
        """Test token contains valid exp claim for 24 hours."""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "change-me"
        })
        
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Decode token (skip verification to just check claims)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check exp claim exists
        assert "exp" in payload
        
        # Check exp is approximately 24 hours in future (decode exp as UTC,
        # not local time, to match the naive-UTC `now` below)
        exp_datetime = datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(tzinfo=None)
        now = _utcnow()
        time_diff = (exp_datetime - now).total_seconds()
        
        # Should be around 86400 seconds (24 hours)
        # Allow 1 minute variance for test execution time
        assert 86400 - 60 < time_diff < 86400 + 60, f"Expiry is {time_diff} seconds, expected ~86400"
    
    def test_token_contains_required_claims(self):
        """Test token contains required claims (sub, role)."""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "change-me"
        })
        
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Required claims (v1 tokens: sub = user id, username = display name)
        assert "sub" in payload
        assert "username" in payload
        assert "role" in payload
        assert payload["username"] == "admin"
        assert payload["role"] == "admin"


class TestTokenRefresh:
    """Verify token refresh mechanism."""
    
    def test_refresh_returns_new_token(self):
        """Test refresh endpoint returns new valid token."""
        # Get initial token
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "change-me"
        })
        assert login_response.status_code == 200
        initial_token = login_response.json()["access_token"]
        
        # Refresh token (sleep so iat/exp differ — tokens issued in the same
        # second are byte-identical)
        time.sleep(1)
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {initial_token}"}
        )
        
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        
        # Verify structure
        assert "access_token" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 86400
        
        # Verify new token is different
        new_token = data["access_token"]
        assert new_token != initial_token
    
    def test_refresh_new_token_has_valid_exp(self):
        """Test refreshed token has valid exp claim."""
        # Get and refresh token
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "change-me"
        })
        initial_token = login_response.json()["access_token"]
        
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {initial_token}"}
        )
        
        new_token = refresh_response.json()["access_token"]
        
        # Decode new token
        payload = jwt.decode(new_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check exp is fresh (24 hours from now; decode exp as UTC)
        exp_datetime = datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(tzinfo=None)
        now = _utcnow()
        time_diff = (exp_datetime - now).total_seconds()
        
        # Should be around 86400 seconds (24 hours)
        assert 86400 - 60 < time_diff < 86400 + 60
    
    def test_refresh_without_bearer_header_fails(self):
        """Test refresh fails without Bearer token."""
        response = client.post("/api/v1/auth/refresh")
        
        # HTTPBearer dependency will return 401 or 403
        assert response.status_code in (401, 403)
        data = response.json()
        
        # Should have error field
        assert "error" in data or "detail" in data
    
    def test_refresh_with_invalid_token_fails(self):
        """Test refresh with invalid token fails."""
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401
        data = response.json()
        
        # Should return invalid_token error
        assert data.get("error") == "invalid_token"


class TestTokenGracePeriod:
    """Verify 7-day grace period for expired token refresh."""
    
    def test_refresh_with_expired_token_within_grace_period(self):
        """Test refresh works with token expired < 7 days."""
        # Create an expired token manually (expired 1 day ago).
        # Refresh requires sub + username claims (api/routes/v1/auth.py).
        payload = {
            "sub": "admin",
            "username": "admin",
            "role": "admin",
            "exp": _utcnow() - timedelta(days=1)
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        # Refresh should succeed (within 7-day grace period)
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        # Should return new token
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        
        assert "access_token" in data
        new_token = data["access_token"]
        
        # New token should be valid
        payload = jwt.decode(new_token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload
    
    def test_refresh_with_very_old_token_fails(self):
        """Test refresh fails if token > 7 days old."""
        # Create token expired 8 days ago (beyond grace period)
        payload = {
            "sub": "admin",
            "username": "admin",
            "role": "admin",
            "exp": _utcnow() - timedelta(days=8)
        }
        old_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        # Refresh should fail
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {old_token}"}
        )
        
        assert refresh_response.status_code == 401
        data = refresh_response.json()
        
        # Should return token_expired error
        assert data.get("error") == "token_expired"
        assert "grace period" in data.get("message", "").lower()


class TestProtectedEndpointAuth:
    """Verify protected endpoints validate token properly."""
    
    def test_get_bot_status_with_valid_token(self, db_admin_token):
        """Test protected endpoint works with valid token.

        Protected v1 endpoints resolve the token sub to a users-table row,
        so the DB-backed test account (conftest) is required.
        """
        assert db_admin_token is not None
        
        # Access protected endpoint
        status_response = client.get(
            "/api/v1/bot/status",
            headers={"Authorization": f"Bearer {db_admin_token}"}
        )
        
        # Should succeed (assuming bot initialization is ok)
        # Could be 200 if bot is running, or error if bot not initialized yet
        assert status_response.status_code in (200, 500, 503)
    
    def test_get_bot_status_with_expired_token_fails(self):
        """Test protected endpoint fails with expired token."""
        # Create expired token
        payload = {
            "sub": "admin",
            "role": "admin",
            "exp": _utcnow() - timedelta(days=1)
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        # Try to access protected endpoint
        status_response = client.get(
            "/api/v1/bot/status",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        # Should return 401 with token_expired error
        assert status_response.status_code == 401
        data = status_response.json()
        
        assert data.get("error") == "token_expired"
    
    def test_get_bot_status_with_invalid_token_fails(self):
        """Test protected endpoint fails with invalid token."""
        status_response = client.get(
            "/api/v1/bot/status",
            headers={"Authorization": "Bearer not.a.valid.token"}
        )
        
        assert status_response.status_code == 401
        data = status_response.json()
        
        assert data.get("error") == "invalid_token"


class TestTokenClaims:
    """Verify token claims contain correct user information."""
    
    def test_admin_token_has_admin_role(self):
        """Test admin token has admin role claim."""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "change-me"
        })
        
        token = response.json()["access_token"]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert payload["role"] == "admin"
        assert payload["username"] == "admin"
    
    def test_user_token_has_user_role(self):
        """Test user token has user role claim."""
        response = client.post("/api/v1/auth/login", json={
            "username": "user",
            "password": "user123"
        })
        
        # May fail if user not in env, but if it works, verify role
        if response.status_code == 200:
            token = response.json()["access_token"]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            assert payload["role"] == "user"
            assert payload["username"] == "user"


class TestConcurrentRefreshes:
    """Verify concurrent token refreshes don't cause issues."""
    
    def test_multiple_sequential_refreshes(self):
        """Test multiple sequential refresh operations."""
        # Get initial token
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "change-me"
        })
        token = login_response.json()["access_token"]
        
        # Refresh multiple times sequentially (sleep so iat/exp differ —
        # tokens issued in the same second are byte-identical)
        tokens = [token]
        for i in range(3):
            time.sleep(1)
            refresh_response = client.post(
                "/api/v1/auth/refresh",
                headers={"Authorization": f"Bearer {tokens[-1]}"}
            )
            
            assert refresh_response.status_code == 200
            new_token = refresh_response.json()["access_token"]
            tokens.append(new_token)
            
            # Verify all tokens are different
            assert len(set(tokens)) == len(tokens)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
