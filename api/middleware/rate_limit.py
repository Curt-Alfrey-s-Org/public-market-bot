"""
Rate Limiting Configuration for API V1
======================================
Uses slowapi to protect endpoints from abuse.

Rate Limits:
- Auth endpoints (/api/v1/auth/*): 10 requests/minute per IP
- Bot control (/api/v1/bot/start, /stop): 30 requests/hour per IP
- General endpoints: 60 requests/minute per IP
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
from api.utils.timeutils import utcnow as _naive_utcnow

logger = logging.getLogger(__name__)

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],  # Default rate limit for all routes
    storage_uri="memory://",  # In-memory storage (use Redis for production multi-instance)
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.
    
    Returns consistent ErrorResponse format with 429 status.
    Includes Retry-After header telling client when they can retry.
    """
    # Extract rate limit info from exception
    retry_after = getattr(exc, "retry_after", 60)  # Default 60 seconds
    
    logger.warning(
        f"Rate limit exceeded for {request.client.host if request.client else 'unknown'} "
        f"on {request.url.path} (retry after {retry_after}s)"
    )
    
    return JSONResponse(
        status_code=429,
        headers={"Retry-After": str(retry_after)},
        content={
            "error": "rate_limited",
            "message": f"Too many requests. Please wait {retry_after} seconds before retrying.",
            "status_code": 429,
            "timestamp": _naive_utcnow().isoformat() + "Z",
            "detail": {
                "retry_after_seconds": retry_after,
                "rate_limit": str(exc)
            }
        }
    )


# Rate limit decorators for different endpoint categories
AUTH_RATE_LIMIT = "10/minute"  # Login, refresh endpoints
BOT_CONTROL_RATE_LIMIT = "30/hour"  # Start/stop bot
GENERAL_RATE_LIMIT = "60/minute"  # All other endpoints
