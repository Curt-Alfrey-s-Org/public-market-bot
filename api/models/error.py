"""
Error Response Models
Standard error response format for all API endpoints
"""

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Dict, Any
from api.utils.timeutils import utcnow as _naive_utcnow


class ErrorResponse(BaseModel):
    """
    Standard error response format.
    
    All errors from the API should follow this format for consistent
    parsing by mobile apps and other clients.
    """
    error: str = Field(
        ...,
        description="Error code (machine-readable): e.g., 'invalid_credentials', 'not_found', 'server_error'"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    status_code: int = Field(
        ...,
        description="HTTP status code (400, 401, 403, 404, 500, etc.)"
    )
    timestamp: str = Field(
        default_factory=lambda: _naive_utcnow().isoformat() + "Z",
        description="ISO 8601 timestamp when error occurred"
    )
    detail: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional detailed error context (e.g., validation errors)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "invalid_credentials",
                "message": "Username or password incorrect",
                "status_code": 401,
                "timestamp": "2026-02-12T10:30:00Z",
                "detail": None
            }
        }
    )


class ValidationError(ErrorResponse):
    """Validation error response (400) with field-level details."""
    error: str = "validation_error"
    detail: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Field-level validation errors: {'field_name': 'error message'}"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "validation_error",
                "message": "Request validation failed",
                "status_code": 400,
                "timestamp": "2026-02-12T10:30:00Z",
                "detail": {
                    "username": "Username is required",
                    "password": "change-me"
                }
            }
        }
    )


class UnauthorizedError(ErrorResponse):
    """Unauthorized error response (401)."""
    error: str = "unauthorized"
    message: str = "Authentication required or invalid credentials"
    status_code: int = 401
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "unauthorized",
                "message": "Invalid token",
                "status_code": 401,
                "timestamp": "2026-02-12T10:30:00Z"
            }
        }
    )


class ForbiddenError(ErrorResponse):
    """Forbidden error response (403)."""
    error: str = "forbidden"
    message: str = "User lacks required permissions"
    status_code: int = 403


class NotFoundError(ErrorResponse):
    """Not found error response (404)."""
    error: str = "not_found"
    message: str = "Requested resource not found"
    status_code: int = 404


class RateLimitError(ErrorResponse):
    """Rate limit error response (429)."""
    error: str = "rate_limited"
    message: str = "Too many requests. Please wait before retry."
    status_code: int = 429
    detail: Optional[Dict[str, Any]] = Field(
        default=None,
        description="{'retry_after_seconds': 60}"
    )


class ServerError(ErrorResponse):
    """Server error response (500)."""
    error: str = "server_error"
    message: str = "Internal server error"
    status_code: int = 500
