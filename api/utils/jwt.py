"""
JWT Token Utilities
===================
Handles token creation, validation, and refresh logic for mobile API authentication.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import os
import logging
from api.utils.timeutils import utcnow as _naive_utcnow, utcfromtimestamp as _naive_utcfromtimestamp
from api.security_config import get_jwt_secret

logger = logging.getLogger(__name__)

# JWT Configuration: shared secret from JWT_SECRET (alias JWT_SECRET_KEY); required
# in production, no public fallback. See api/security_config.py.
SECRET_KEY = get_jwt_secret()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7   # 7 days grace period


def create_access_token(
    user_id: int,
    username: str,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a new JWT access token.
    
    Args:
        user_id: Database user ID
        username: Username for display
        additional_claims: Optional extra claims to include in token
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_access_token(user_id=123, username="trader")
        >>> # Token valid for 24 hours
    """
    now = _naive_utcnow()
    expire = now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "username": username,
        "iat": now,  # Issued at
        "exp": expire,  # Expiration
        "type": "access"
    }
    
    # Add any additional claims
    if additional_claims:
        payload.update(additional_claims)
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    logger.debug(f"Created access token for user {user_id} (expires {expire.isoformat()})")
    
    return token


def create_refresh_token(user_id: int, username: str) -> str:
    """
    Create a refresh token with longer expiration.
    
    Refresh tokens allow clients to get new access tokens without
    re-authenticating, within the 7-day grace period.
    
    Args:
        user_id: Database user ID
        username: Username
        
    Returns:
        Encoded JWT refresh token
    """
    now = _naive_utcnow()
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": expire,
        "type": "refresh"
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    logger.debug(f"Created refresh token for user {user_id} (expires {expire.isoformat()})")
    
    return token


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        ExpiredSignatureError: Token has expired
        InvalidTokenError: Token is invalid or malformed
        
    Example:
        >>> payload = decode_token(token)
        >>> user_id = int(payload["sub"])
        >>> username = payload["username"]
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        logger.warning("Token expired")
        raise
    except InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
    """
    Verify that a token payload has the expected type.
    
    Args:
        payload: Decoded token payload
        expected_type: Expected token type ("access" or "refresh")
        
    Returns:
        True if type matches, False otherwise
    """
    token_type = payload.get("type")
    if token_type != expected_type:
        logger.warning(f"Token type mismatch: expected {expected_type}, got {token_type}")
        return False
    return True


def get_token_expiration(token: str) -> Optional[datetime]:
    """
    Get the expiration datetime of a token without validating it.
    
    Args:
        token: JWT token string
        
    Returns:
        Expiration datetime or None if invalid
    """
    try:
        # Decode without verification to check expiration
        payload = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            return _naive_utcfromtimestamp(exp_timestamp)
    except Exception as e:
        logger.warning(f"Could not extract expiration from token: {e}")
    
    return None


def is_token_expired(token: str) -> bool:
    """
    Check if a token is expired without full validation.
    
    Args:
        token: JWT token string
        
    Returns:
        True if expired, False otherwise
    """
    exp = get_token_expiration(token)
    if exp:
        return _naive_utcnow() > exp
    return True  # If we can't determine, assume expired


def extract_user_id(token: str) -> Optional[int]:
    """
    Extract user ID from token without full validation.
    Useful for logging/debugging.
    
    Args:
        token: JWT token string
        
    Returns:
        User ID or None if extraction fails
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id_str = payload.get("sub")
        if user_id_str:
            return int(user_id_str)
    except Exception as e:
        logger.warning(f"Could not extract user ID from token: {e}")
    
    return None
