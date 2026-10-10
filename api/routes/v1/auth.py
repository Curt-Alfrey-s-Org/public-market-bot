"""
API V1 Authentication Routes
Compatible with mobile apps (iOS/Android)
Endpoints: /api/v1/auth/login, /api/v1/auth/refresh
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import hmac
import logging
import os
import json
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from api.utils.jwt import (
    SECRET_KEY as JWT_SIGNING_KEY,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
    ACCESS_TOKEN_EXPIRE_HOURS,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from api.auth import hash_password, verify_db_user_password
from api.dependencies.auth import get_current_user
from api.models.user import User
from api.models.audit import AuditLog
from database import get_db
from api.middleware.rate_limit import limiter, AUTH_RATE_LIMIT
from api.utils.timeutils import utcnow as _naive_utcnow, utcfromtimestamp as _naive_utcfromtimestamp

logger = logging.getLogger(__name__)
router = APIRouter()

TOKEN_EXPIRE_HOURS = ACCESS_TOKEN_EXPIRE_HOURS


# ============================================================================
# REQUEST/RESPONSE MODELS (V1 Mobile-Friendly)
# ============================================================================

class AuthLoginRequest(BaseModel):
    """Login request: username and password."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class AuthLoginResponse(BaseModel):
    """Login response with token and user info."""
    access_token: str = Field(..., description="JWT access token for API calls")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Token expiry in seconds (86400 = 24 hours)")
    user: dict = Field(..., description="User info: id, username, role")


class AuthRefreshRequest(BaseModel):
    """Refresh token request (send current token in Authorization header instead)."""
    pass


class AuthRefreshResponse(BaseModel):
    """Refresh token response with new access token."""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Token expiry in seconds (86400 = 24 hours)")


# ============================================================================
# ENVIRONMENT-BASED CREDENTIALS LOADER
# ============================================================================

_ENV_USERS = {}


def _load_env_users():
    """Load environment-based credentials from env variables (no built-in default accounts)."""
    global _ENV_USERS
    
    _ENV_USERS = {}
    
    # Load from environment variables
    admin_user = os.getenv("ADMIN_USERNAME", "").strip()
    admin_pass = os.getenv("ADMIN_PASSWORD", "").strip()
    if admin_user and admin_pass:
        _ENV_USERS[admin_user] = ("admin", admin_pass)
    
    user_user = os.getenv("USER_USERNAME", "").strip()
    user_pass = os.getenv("USER_PASSWORD", "").strip()
    if user_user and user_pass:
        _ENV_USERS[user_user] = ("user", user_pass)
    
    logger.debug(f"Auth system loaded {len(_ENV_USERS)} environment-based users")


def _check_env_password(username: str, password: str) -> tuple[bool, str]:
    """
    Check credentials against environment-based users.
    Returns (success, role).
    """
    if not _ENV_USERS:
        _load_env_users()
    
    if username not in _ENV_USERS:
        return False, ""
    
    expected_role, expected_pass = _ENV_USERS[username]
    if expected_pass and hmac.compare_digest(expected_pass.encode("utf-8"), (password or "").encode("utf-8")):
        return True, expected_role
    
    return False, ""


# ============================================================================
# LOGIN ENDPOINT: /api/v1/auth/login
# ============================================================================

@router.post("/login", response_model=AuthLoginResponse)
@limiter.limit(AUTH_RATE_LIMIT)  # 10 requests/minute
async def login(
    request: Request,
    request_body: AuthLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with username and password.
    
    Supports:
    1. Environment-based credentials (admin, user)
    2. Database-backed registered users
    
    Returns:
        - access_token: JWT token for Authorization: Bearer <token>
        - expires_in: 86400 seconds (24 hours)
        - user: {id, username, role}
    
    Errors:
        - 400: Invalid request
        - 401: Invalid username or password
        - 500: Internal server error
    """
    username = (request_body.username or "").strip()
    password = request_body.password or ""
    
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_request",
                "message": "Username and password required"
            }
        )
    
    # Step 1: Check environment-based credentials
    env_ok, env_role = _check_env_password(username, password)
    if env_ok:
        # For env users, use username as user_id
        token = create_access_token(
            user_id=hash(username),  # Use hash of username as fake ID
            username=username,
            additional_claims={"role": env_role}
        )
        logger.info(f"User logged in via env: {username} ({env_role})")
        
        # Log audit
        db.add(AuditLog(
            user_id=None,
            event_type='login',
            ip_address=request.client.host if request.client else "",
            user_agent=request.headers.get("user-agent", ""),
            success=True,
            details=json.dumps({"username": username, "method": "env"})
        ))
        db.commit()
        
        return AuthLoginResponse(
            access_token=token,
            token_type="change-me",
            expires_in=TOKEN_EXPIRE_HOURS * 3600,
            user={"id": username, "username": username, "role": env_role}
        )
    
    # Step 2: Check database-backed users (re-hashes legacy bcrypt to argon2 on success)
    user = db.query(User).filter_by(username=username).first()
    if user and verify_db_user_password(db, user, password):
        # Check if email verified for regular users
        if user.role == "user" and not user.email_verified:
            db.add(AuditLog(
                user_id=user.id,
                event_type='login_failed',
                ip_address=request.client.host if request.client else "",
                user_agent=request.headers.get("user-agent", ""),
                success=False,
                details=json.dumps({"reason": "email_not_verified"})
            ))
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "email_not_verified",
                    "message": "Email address not verified. Please check your email and verify before logging in.",
                },
            )

        # Update last login
        user.last_login = _naive_utcnow()
        token = create_access_token(
            user_id=user.id,
            username=username,
            additional_claims={"role": user.role},
        )
        refresh_token = create_refresh_token(user_id=user.id, username=username)
        logger.info(f"User logged in via db: {username} ({user.role})")
        
        # Log audit
        db.add(AuditLog(
            user_id=user.id,
            event_type='login',
            ip_address=request.client.host if request.client else "",
            user_agent=request.headers.get("user-agent", ""),
            success=True,
            details=json.dumps({"method": "database"})
        ))
        db.commit()
        
        return AuthLoginResponse(
            access_token=token,
            token_type="change-me",
            expires_in=TOKEN_EXPIRE_HOURS * 3600,
            user={"id": str(user.id), "username": username, "role": user.role}
        )
    
    # Failed login
    logger.warning(f"Failed login attempt: {username}")
    db.add(AuditLog(
        user_id=None,
        event_type='login_failed',
        ip_address=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", ""),
        success=False,
        details=json.dumps({"username": username})
    ))
    db.commit()
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": "invalid_credentials",
            "message": "Invalid username or password"
        }
    )


# ============================================================================
# REFRESH TOKEN ENDPOINT: /api/v1/auth/refresh
# ============================================================================

@router.post("/refresh", response_model=AuthRefreshResponse)
@limiter.limit(AUTH_RATE_LIMIT)  # 10 requests/minute
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh access token before expiry.
    
    Mobile app should call this endpoint before token expires (e.g., after 20 hours).
    Sends current token in Authorization: Bearer <token> header.
    
    Returns:
        - access_token: New JWT token with fresh expiry
        - expires_in: 86400 seconds (24 hours)
    
    Errors:
        - 401: Token missing or invalid
        - 401: Token expired beyond 7-day grace period
    """
    # Extract authorization header
    auth_header = request.headers.get("Authorization", "").strip()
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "unauthorized",
                "message": "Missing or invalid Authorization header"
            }
        )
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    try:
        # Decode token (allow expired within grace period)
        payload = jwt.decode(
            token,
            JWT_SIGNING_KEY,
            algorithms=["HS256"],
            options={"verify_exp": False}  # Allow expired token for refresh
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "message": "Invalid or malformed token"
            }
        )
    
    # Check if token is too old (> 7 day grace period)
    exp_timestamp = payload.get("exp")
    if exp_timestamp:
        exp_datetime = _naive_utcfromtimestamp(exp_timestamp)
        grace_cutoff = _naive_utcnow() - timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        if exp_datetime < grace_cutoff:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "token_expired",
                    "message": f"Token expired beyond refresh grace period ({REFRESH_TOKEN_EXPIRE_DAYS} days). Please login again."
                }
            )
    
    # Extract user info from token
    user_id_str = payload.get("sub")
    username = payload.get("username")
    role = payload.get("role")
    
    if not user_id_str or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "message": "Token missing required claims"
            }
        )
    
    # Generate new access token
    try:
        user_id = int(user_id_str)
    except ValueError:
        user_id = hash(username)  # Fallback for env users

    new_token = create_access_token(
        user_id=user_id,
        username=username,
        additional_claims={"role": role} if role else None,
    )
    logger.info(f"Token refreshed for user: {username}")
    
    return AuthRefreshResponse(
        access_token=new_token,
        token_type="change-me",
        expires_in=TOKEN_EXPIRE_HOURS * 3600
    )
