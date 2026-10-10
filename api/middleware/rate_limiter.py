"""
Rate Limiting Middleware for API V1 Endpoints
Prevents API abuse and ensures fair usage across all clients
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple
from collections import defaultdict
import hashlib
from fastapi import Request, status
from fastapi.responses import JSONResponse
from api.utils.timeutils import utcnow as _naive_utcnow

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Configuration for rate limiting rules"""
    
    # General endpoints: 60 requests per minute
    GENERAL_LIMIT = 60
    GENERAL_WINDOW = 60  # seconds
    
    # Auth endpoints: 10 requests per minute per IP (prevent brute force)
    AUTH_LIMIT = 10
    AUTH_WINDOW = 60  # seconds
    
    # Bot control (start/stop): 30 requests per hour (prevent accidental spam)
    BOT_CONTROL_LIMIT = 30
    BOT_CONTROL_WINDOW = 3600  # seconds
    
    # Webhook/admin: 100 requests per minute
    WEBHOOK_LIMIT = 100
    WEBHOOK_WINDOW = 60  # seconds


class RateLimiter:
    """
    Simple in-memory rate limiter for FastAPI.
    Tracks requests per IP address and path.
    """
    
    def __init__(self):
        # Store request counts: {bucket_key: [(timestamp, count), ...]}
        self.request_history: Dict[str, list] = defaultdict(list)  
    
    def _get_bucket_key(self, ip_address: str, path: str) -> str:
        """Create a unique key for tracking a specific IP and endpoint"""
        # Hash path to make it shorter but still unique
        path_hash = hashlib.md5(path.encode(), usedforsecurity=False).hexdigest()[:8]
        return f"{ip_address}:{path_hash}"
    
    def _get_rate_limit(self, path: str) -> Tuple[int, int]:
        """Get rate limit and window for a specific path"""
        if path.startswith("/api/v1/auth"):
            return RateLimitConfig.AUTH_LIMIT, RateLimitConfig.AUTH_WINDOW
        elif path.startswith("/api/v1/bot") and any(x in path for x in ["/start", "/stop"]):
            return RateLimitConfig.BOT_CONTROL_LIMIT, RateLimitConfig.BOT_CONTROL_WINDOW
        else:
            return RateLimitConfig.GENERAL_LIMIT, RateLimitConfig.GENERAL_WINDOW
    
    def is_rate_limited(self, ip_address: str, path: str) -> Tuple[bool, int]:
        """
        Check if a request from IP_address to path is rate limited.
        
        Returns:
            (is_limited, retry_after_seconds)
        """
        limit, window = self._get_rate_limit(path)
        bucket_key = self._get_bucket_key(ip_address, path)
        
        now = _naive_utcnow()
        cutoff_time = now - timedelta(seconds=window)
        
        # Remove old entries outside the window
        self.request_history[bucket_key] = [
            timestamp for timestamp in self.request_history[bucket_key]
            if timestamp > cutoff_time
        ]
        
        # Count requests in current window
        request_count = len(self.request_history[bucket_key])
        
        # Check if limit exceeded
        if request_count >= limit:
            # Calculate when next request is allowed
            oldest_request = self.request_history[bucket_key][0]
            next_allowed = oldest_request + timedelta(seconds=window)
            retry_after = int((next_allowed - now).total_seconds()) + 1
            return True, retry_after
        
        # Record this request
        self.request_history[bucket_key].append(now)
        return False, 0
    
    def cleanup(self):
        """Cleanup old entries from memory (call periodically)"""
        # This is a simple implementation. In production, use Redis
        now = _naive_utcnow()
        cutoff_time = now - timedelta(hours=1)
        
        for bucket_key in list(self.request_history.keys()):
            self.request_history[bucket_key] = [
                timestamp for timestamp in self.request_history[bucket_key]
                if timestamp > cutoff_time
            ]
            
            # Delete empty buckets
            if not self.request_history[bucket_key]:
                del self.request_history[bucket_key]


# Global instance
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware to rate limit API endpoints.
    
    Usage:
        app.add_middleware(RateLimitMiddleware)
    """
    # Skip rate limiting for non-API paths
    if not request.url.path.startswith("/api/v1/"):
        return await call_next(request)
    
    # Get client IP (handle proxies)
    ip_address = request.client.host if request.client else "unknown"
    if "x-forwarded-for" in request.headers:
        ip_address = request.headers["x-forwarded-for"].split(",")[0].strip()
    
    # Check rate limit
    is_limited, retry_after = rate_limiter.is_rate_limited(ip_address, request.url.path)
    
    if is_limited:
        logger.warning(
            f"Rate limit exceeded for IP {ip_address} on {request.url.path}. "
            f"Retry after {retry_after}s"
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "rate_limited",
                "message": "Too many requests. Please wait before retrying.",
                "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
                "timestamp": _naive_utcnow().isoformat() + "Z",
                "detail": f"Rate limit exceeded. Retry after {retry_after} seconds."
            },
            headers={"Retry-After": str(retry_after)}
        )
    
    # Continue processing
    return await call_next(request)
