"""
Auth Middleware for C2 API V1
=============================
Validates JWT tokens and extracts user information.
"""

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import jwt
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Get JWT settings (shared secret; required in production, no public fallback)
from api.security_config import get_jwt_secret

SECRET_KEY = get_jwt_secret()
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24


async def get_current_user_v1(credentials: HTTPAuthCredentials = Depends(security)) -> dict:
    """
    Validates JWT token and returns user information.
    
    Returns: {"user_id": str, "username": str, "role": str}
    
    Raises:
        401 "unauthorized" - Missing or invalid token
        401 "token_expired" - Token has expired (but may be refreshable)
        401 "invalid_token" - Malformed token or wrong secret
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        role: str = payload.get("role", "user")
        
        if username is None:
            logger.warning("Token missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_token",
                    "message": "Token missing required claims"
                }
            )
        
        return {
            "user_id": user_id or username,
            "username": username,
            "role": role
        }
        
    except jwt.ExpiredSignatureError:
        logger.warning(f"Token expired for user")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "token_expired",
                "message": "Token has expired. Please refresh using POST /api/v1/auth/refresh"
            }
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)[:100]}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "message": "Invalid or malformed token"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in token validation: {str(e)[:100]}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "unauthorized",
                "message": "Authentication failed"
            }
        )
