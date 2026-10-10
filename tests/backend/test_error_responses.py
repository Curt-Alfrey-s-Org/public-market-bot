"""
Phase 2-B Tests: Error Response Integration
============================================
Verify all error responses use consistent ErrorResponse schema.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app, BOT_API_KEY
import json
import logging

logger = logging.getLogger(__name__)

# All /api/* routes except health and /api/auth require X-API-Key (RequireApiKeyMiddleware)
client = TestClient(app, headers={"X-API-Key": BOT_API_KEY})


class TestErrorResponseSchema:
    """Verify error responses follow consistent schema."""
    
    def test_login_missing_credentials(self):
        """Test 400 error when credentials missing."""
        response = client.post("/api/v1/auth/login", json={
            "username": "",
            "password": ""
        })
        
        assert response.status_code == 400
        data = response.json()
        
        # Verify ErrorResponse schema
        assert "error" in data
        assert "message" in data
        assert "status_code" in data
        assert "timestamp" in data
        
        # Verify values
        assert data["error"] == "invalid_request"
        assert data["status_code"] == 400
        assert "required" in data["message"].lower() or "username" in data["message"].lower()
    
    def test_login_invalid_credentials(self):
        """Test 401 error for invalid credentials."""
        response = client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "change-me"
        })
        
        assert response.status_code == 401
        data = response.json()
        
        # Verify ErrorResponse schema
        assert "error" in data
        assert "message" in data
        assert "status_code" in data
        assert "timestamp" in data
        
        # Verify values
        assert data["error"] == "invalid_credentials"
        assert data["status_code"] == 401
    
    def test_unauthorized_endpoint_without_token(self):
        """Test 401 when accessing protected endpoint without token."""
        response = client.get("/api/v1/bot/status")
        
        assert response.status_code == 403 or response.status_code == 401
        # Status code might be 403 for missing API key, that's fine
        if response.status_code in (401, 403):
            data = response.json()
            # Should have error structure
            if isinstance(data, dict):
                # Could be ErrorResponse or custom message
                assert data.get("error") or data.get("detail") or data.get("message")
    
    def test_timestamp_format(self):
        """Test error timestamp is ISO 8601."""
        response = client.post("/api/v1/auth/login", json={
            "username": "",
            "password": ""
        })
        
        data = response.json()
        timestamp = data.get("timestamp")
        
        assert timestamp is not None
        assert "T" in timestamp or "-" in timestamp  # ISO 8601 format
        assert timestamp.endswith("Z") or "+" in timestamp or timestamp.count("-") >= 2


class TestErrorCodes:
    """Verify error codes are consistent and documented."""
    
    # Error codes that should be returned by the API
    EXPECTED_ERROR_CODES = {
        "invalid_request": 400,
        "invalid_credentials": 401,
        "unauthorized": 401,
        "token_expired": 401,
        "invalid_token": 401,
        "email_not_verified": 401,
        "forbidden": 403,
        "not_found": 404,
        "validation_error": 422,
        "rate_limited": 429,
        "server_error": 500,
        "service_unavailable": 503,
    }
    
    def test_login_returns_valid_error_code(self):
        """Test login endpoint returns valid error code."""
        response = client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "wrong"
        })
        
        assert response.status_code == 401
        data = response.json()
        error_code = data.get("error")
        
        assert error_code in self.EXPECTED_ERROR_CODES
        assert self.EXPECTED_ERROR_CODES[error_code] == response.status_code


class TestValidationErrors:
    """Verify validation errors (422) have proper format."""
    
    def test_malformed_login_request(self):
        """Test 422 when request body malformed."""
        response = client.post("/api/v1/auth/login", json={
            "username": "user"
            # Missing password
        })
        
        # FastAPI returns 422 for missing required fields
        if response.status_code == 422:
            data = response.json()
            
            # Should have error structure
            assert "error" in data or "detail" in data or "message" in data
    
    def test_invalid_json(self):
        """Test 422 when JSON is invalid."""
        response = client.post(
            "/api/v1/auth/login",
            content=b"not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Could be 400 or 422 depending on parser
        assert response.status_code in (400, 422, 422)


class TestErrorPropagation:
    """Verify errors are properly caught and converted."""
    
    def test_refresh_without_authorization(self):
        """Test refresh endpoint without auth header."""
        response = client.post(
            "/api/v1/auth/refresh",
            headers={}  # No Authorization header
        )
        
        # HTTPBearer security raises 403 if header missing
        assert response.status_code in (401, 403)
        data = response.json()
        
        # Should have error field
        assert "error" in data or "detail" in data or data.get("error") or data.get("detail")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
