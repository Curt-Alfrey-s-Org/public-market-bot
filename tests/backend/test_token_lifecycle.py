"""
PHASE 2-C: Token Lifecycle Tests
Tests JWT token generation, expiry, and refresh mechanisms
"""

import pytest
import json
import os
import time
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import jwt
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.main import app, BOT_API_KEY
# v1 tokens are signed/verified by api/utils/jwt.py (not api/auth.py)
from api.utils.jwt import SECRET_KEY, ALGORITHM

# All /api/* routes except health and /api/auth require X-API-Key (RequireApiKeyMiddleware)
client = TestClient(app, headers={"X-API-Key": BOT_API_KEY})


def _utcnow() -> datetime:
    """Naive UTC now (_utcnow() is deprecated since Python 3.12)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TestTokenGeneration:
    """Test JWT token generation and claims"""
    
    def test_successful_login(self):
        """Test login endpoint returns valid token"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "change-me"  # Default env credentials
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data
        
        # Verify token_type
        assert data["token_type"].lower() == "bearer"
        
        # Verify expires_in (24 hours = 86400 seconds)
        assert data["expires_in"] == 86400
        
        # Verify user structure
        assert "username" in data["user"]
        assert "role" in data["user"]
    
    def test_token_is_valid_jwt(self):
        """Test that returned token is valid JWT"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username":"admin",
                "password": "change-me"
            }
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Decode without verification (just check structure)
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        # Verify JWT claims
        assert "sub" in decoded  # subject (username)
        assert "exp" in decoded  # expiration timestamp
        assert "iat" in decoded  # issued at
        assert "role" in decoded  # role claim
    
    def test_token_has_24h_expiry(self):
        """Test token has 24-hour expiry"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "change-me"
            }
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Decode token
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        # Check expiry is ~24 hours from now
        exp_timestamp = decoded["exp"]
        iat_timestamp = decoded["iat"]
        expiry_duration = exp_timestamp - iat_timestamp
        
        # Should be approximately 24 hours (86400 seconds)
        # Allow 60 second tolerance for test execution time
        assert 86340 <= expiry_duration <= 86460
    
    def test_invalid_credentials_return_401(self):
        """Test login with invalid credentials returns 401"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "change-me"
            }
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "invalid_credentials"
    
    def test_missing_credentials_return_400(self):
        """Test login missing username/password is rejected.

        Pydantic request validation returns 422 Unprocessable Content
        (FastAPI default for RequestValidationError).
        """
        # Missing password
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin"}
        )
        assert response.status_code in (400, 422)
        
        # Missing username
        response = client.post(
            "/api/v1/auth/login",
            json={"password": "change-me"}
        )
        assert response.status_code in (400, 422)


class TestTokenValidation:
    """Test token validation on protected endpoints"""
    
    @pytest.fixture
    def valid_token(self):
        """Get a valid token for testing"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "change-me"
            }
        )
        return response.json()["access_token"]
    
    def test_protected_endpoint_requires_token(self):
        """Test protected endpoint rejects request without token"""
        response = client.get("/api/v1/bot/status")
        assert response.status_code == 401
        assert response.json()["error"] == "unauthorized"
    
    def test_protected_endpoint_with_valid_token(self, db_admin_token):
        """Test protected endpoint accepts valid token.

        Protected v1 endpoints resolve the token sub to a users-table row,
        so the DB-backed test account (conftest) is required.
        """
        response = client.get(
            "/api/v1/bot/status",
            headers={"Authorization": f"Bearer {db_admin_token}"}
        )
        assert response.status_code == 200
    
    def test_invalid_token_rejected(self):
        """Test protected endpoint rejects invalid token"""
        response = client.get(
            "/api/v1/bot/status",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    def test_malformed_auth_header_rejected(self, valid_token):
        """Test malformed Authorization header rejected"""
        # Missing 'Bearer' prefix
        response = client.get(
            "/api/v1/bot/status",
            headers={"Authorization": valid_token}
        )
        assert response.status_code == 401
    
    def test_expired_token_rejected(self):
        """Test expired token is rejected"""
        # Create expired token manually
        expired_payload = {
            "sub": "admin",
            "role": "admin",
            "exp":_utcnow() - timedelta(hours=1),  # 1 hour ago
            "iat": _utcnow() - timedelta(hours=25)
        }
        expired_token = jwt.encode(
            expired_payload,
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        response = client.get(
            "/api/v1/bot/status",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
        assert "expired" in response.json()["message"].lower()


class TestTokenRefresh:
    """Test token refresh functionality"""
    
    @pytest.fixture
    def valid_token(self):
        """Get a valid token"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "change-me"
            }
        )
        return response.json()["access_token"]
    
    def test_refresh_valid_token(self, valid_token):
        """Test refreshing a valid token"""
        # Sleep so iat/exp differ — tokens issued in the same second are
        # byte-identical (HS256 over identical claims)
        time.sleep(1)
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["expires_in"] == 86400
        
        # New token should be different
        assert data["access_token"] != valid_token
    
    def test_refresh_returns_new_token(self, valid_token):
        """Test refresh returns new token with fresh expiry"""
        # Sleep so the refreshed exp is strictly later (1s claim resolution)
        time.sleep(1)
        # Refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response.status_code == 200
        new_token = response.json()["access_token"]
        
        # Decode both tokens
        old_decoded = jwt.decode(
            valid_token,
            options={"verify_signature": False}
        )
        new_decoded = jwt.decode(
            new_token,
            options={"verify_signature": False}
        )
        
        # New token should have later expiry
        assert new_decoded["exp"] > old_decoded["exp"]
    
    def test_refresh_expired_token_within_grace_period(self):
        """Test refreshing expired token within 7-day grace period"""
        # Create expired token (within 7-day grace period).
        # Refresh requires sub + username claims (api/routes/v1/auth.py).
        expired_payload = {
            "sub": "admin",
            "username": "admin",
            "role": "admin",
            "exp": _utcnow() - timedelta(hours=1),  # 1 hour ago
            "iat": _utcnow() - timedelta(hours=25)
        }
        expired_token = jwt.encode(
            expired_payload,
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        # Should succeed (within grace period)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    def test_refresh_token_beyond_grace_period_fails(self):
        """Test refresh fails for tokens beyond 7-day grace period"""
        # Create very old expired token (beyond 7-day grace)
        old_payload = {
            "sub": "admin",
            "username": "admin",
            "role": "admin",
            "exp": _utcnow() - timedelta(days=10),  # 10 days ago
            "iat": _utcnow() - timedelta(days=11)
        }
        old_token = jwt.encode(
            old_payload,
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {old_token}"}
        )
        
        # Should fail
        assert response.status_code == 401
        assert "beyond refresh grace period" in response.json()["message"].lower() or \
               "too old" in response.json()["message"].lower()
    
    def test_refresh_without_token_fails(self):
        """Test refresh without Authorization header fails"""
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 401
    
    def test_can_use_new_token_after_refresh(self, db_admin_token):
        """Test that new token from refresh can access protected endpoints.

        Uses the DB-backed test account — protected endpoints resolve the
        token sub to a users-table row.
        """
        # Refresh token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {db_admin_token}"}
        )
        assert refresh_response.status_code == 200
        new_token = refresh_response.json()["access_token"]
        
        # Use new token to access protected endpoint
        status_response = client.get(
            "/api/v1/bot/status",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        assert status_response.status_code == 200


class TestTokenLifecycleFlow:
    """Test complete token lifecycle: login -> use -> refresh -> use"""
    
    def test_full_auth_flow(self):
        """Test complete authentication flow.

        Uses the DB-backed test account (conftest) — protected endpoints
        resolve the token sub to a users-table row.
        """
        from tests.backend.conftest import (
            TEST_DB_ADMIN_PASSWORD,
            TEST_DB_ADMIN_USERNAME,
        )

        # 1. Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": TEST_DB_ADMIN_USERNAME,
                "password": TEST_DB_ADMIN_PASSWORD
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # 2. Use token to access protected endpoint
        status_response = client.get(
            "/api/v1/bot/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert status_response.status_code == 200
        
        # 3. Refresh token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert refresh_response.status_code == 200
        new_token = refresh_response.json()["access_token"]
        
        # 4. Use new token
        status_response2 = client.get(
            "/api/v1/bot/status",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        assert status_response2.status_code == 200
    
    def test_concurrent_refresh_requests(self):
        """Test multiple concurrent refresh requests"""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "change-me"
            }
        )
        token = login_response.json()["access_token"]
        
        # Multiple refresh requests should all succeed (sleep so iat/exp
        # differ — tokens issued in the same second are byte-identical)
        tokens = []
        for i in range(5):
            time.sleep(1)
            response = client.post(
                "/api/v1/auth/refresh",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            tokens.append(response.json()["access_token"])
        
        # All should be different tokens
        assert len(set(tokens)) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
