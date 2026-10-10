"""
Authentication Dependencies for FastAPI Routes
==============================================
Provides reusable dependencies for protecting routes with JWT authentication.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import logging

from database import SessionLocal
from api.models.user import User
from api.utils.jwt import decode_token, verify_token_type
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

logger = logging.getLogger(__name__)

# HTTP Bearer scheme for Authorization header
security = HTTPBearer(
    scheme_name="JWT Bearer Token",
    description="Provide JWT access token in Authorization header"
)


def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to extract and validate JWT token from Authorization header.
    
    Returns the authenticated user or raises 401 if invalid/expired.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id, "username": user.username}
    
    Raises:
        HTTPException 401: If token is missing, invalid, expired, or user not found
    """
    token = credentials.credentials
    
    # Decode and validate token
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        logger.warning("Access token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "token_expired",
                "message": "Access token has expired. Please refresh your token."
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    except InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "message": "Invalid or malformed access token"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verify token type
    if not verify_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token_type",
                "message": "Token is not an access token"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract user ID
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "message": "Token missing user ID"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "message": "Invalid user ID in token"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Look up user in database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User {user_id} from token not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "user_not_found",
                "message": "User account not found"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Inactive user {user_id} attempted to access API")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "user_inactive",
                "message": "User account is inactive"
            }
        )
    
    logger.debug(f"Authenticated user {user.id} ({user.username})")
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication dependency.
    
    Returns the user if valid token provided, or None if no token.
    Raises 401 only if token is provided but invalid.
    
    Useful for endpoints that work differently with/without auth.
    
    Usage:
        @router.get("/public-or-private")
        async def flexible_route(user: Optional[User] = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user.username}"}
            return {"message": "Hello guest"}
    """
    if not credentials:
        return None
    
    # If credentials provided, validate them
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        # Re-raise authentication errors
        raise


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is an admin.
    
    Usage:
        @router.delete("/admin/users/{user_id}")
        async def delete_user(
            user_id: int,
            admin: User = Depends(get_admin_user)
        ):
            # Only admins can reach here
            pass
    
    Raises:
        HTTPException 403: If user is not an admin
    """
    # The User model has no is_superuser column; admin is role == "admin".
    if getattr(current_user, "role", None) != "admin" and not getattr(current_user, "is_superuser", False):
        logger.warning(f"User {current_user.id} attempted admin action without permission")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "insufficient_permissions",
                "message": "Admin permissions required for this action"
            }
        )
    
    return current_user
