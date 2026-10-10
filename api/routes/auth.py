"""
Auth routes: Environment-based + database-backed authentication
================================================================
Pattern inspired by rankings-bot: simple, stateless auth with role-based access.

Supports two authentication modes:
1. Environment-based credentials (ADMIN_USERNAME/ADMIN_PASSWORD, etc.)
2. Database-backed user registration with email verification

(The optional /home/operator/auth-service client import was removed: it was never
used by any route and that path does not exist in the container.)

Role hierarchy: admin > director > user
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import hmac
import secrets
import re
import os
import sys
import json
import logging
import httpx

from api.auth import (
    create_access_token,
    get_current_user,
    hash_password,
)
from api.models.user import User
from api.models.auth_token import EmailVerificationToken, PasswordResetToken
from api.models.audit import AuditLog
from database import get_db
from api.utils.timeutils import utcnow as _naive_utcnow
from api.middleware.rate_limit import limiter, AUTH_RATE_LIMIT

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


# ============================================================================
# ENVIRONMENT-BASED USER CREDENTIALS (inspired by rankings-bot)
# ============================================================================

# No built-in default accounts: an env user exists only when both its
# *_USERNAME and *_PASSWORD variables are set (security review 2026-09-25).
_ENV_USERS = {}

def _load_env_users():
    """
    Load environment-based credentials from env variables.
    Format: ADMIN_USERNAME/ADMIN_PASSWORD, DIRECTOR_USERNAME/DIRECTOR_PASSWORD, USER_USERNAME/USER_PASSWORD
    A role without both variables set has no env login (there are no fallback passwords).
    """
    global _ENV_USERS
    _ENV_USERS = {}
    
    # Admin credentials
    admin_user = os.getenv("ADMIN_USERNAME", "").strip()
    admin_pass = os.getenv("ADMIN_PASSWORD", "").strip()
    if admin_user and admin_pass:
        _ENV_USERS[admin_user] = ("admin", admin_pass)
        logger.info(f"Loaded admin user from env: {admin_user}")
    
    # Director credentials
    director_user = os.getenv("DIRECTOR_USERNAME", "").strip()
    director_pass = os.getenv("DIRECTOR_PASSWORD", "").strip()
    if director_user and director_pass:
        _ENV_USERS[director_user] = ("director", director_pass)
        logger.info(f"Loaded director user from env: {director_user}")
    
    # User credentials
    user_user = os.getenv("USER_USERNAME", "").strip()
    user_pass = os.getenv("USER_PASSWORD", "").strip()
    if user_user and user_pass:
        _ENV_USERS[user_user] = ("user", user_pass)
        logger.info(f"Loaded user from env: {user_user}")
    
    logger.info(f"Auth system initialized with {len(_ENV_USERS)} environment-based users")


def _check_env_password(username: str, password: str) -> tuple[bool, str]:
    """Check credentials against environment-based users. Returns (success, role)."""
    if not _ENV_USERS:
        _load_env_users()
    
    if username not in _ENV_USERS:
        return False, ""
    
    expected_role, expected_pass = _ENV_USERS[username]
    if expected_pass and hmac.compare_digest(expected_pass.encode("utf-8"), (password or "").encode("utf-8")):
        return True, expected_role
    
    return False, ""


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    """Standard login response with success flag and optional token."""
    success: bool
    token: str | None = None
    user: str | None = None
    role: str | None = None
    message: str | None = None


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    role: str
    user: str


class MeResponse(BaseModel):
    """Current user response."""
    role: str
    sub: str


class RegistrationRequest(BaseModel):
    username: str
    email: str
    password: str
    captcha_token: str


class RegistrationResponse(BaseModel):
    message: str
    username: str


class VerificationResponse(BaseModel):
    message: str


class VerificationRequest(BaseModel):
    token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ============================================================================
# LOGIN ENDPOINT (Refactored: Environment-based + DB-backed)
# ============================================================================

# Rate limited like /api/v1/auth/login (review 2026-09-26): this is the login the
# web GUI uses and it had no brute-force limit at all.
@router.post("/login", response_model=LoginResponse)
@limiter.limit(AUTH_RATE_LIMIT)  # 10 requests/minute
async def login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint supporting:
    1. Environment-based credentials (admin, director, user)
    2. Database-backed registered users (email verified required for role='user')
    3. Audit logging for security
    
    Returns:
        - success=true with token, user, role on success
        - success=false with message on failure
    """
    username = (req.username or "").strip()
    password = req.password or ""
    
    # Validation: username required
    if not username:
        return LoginResponse(success=False, message="Username required")
    
    # Step 1: Check environment-based credentials (admin/director/user)
    env_ok, env_role = _check_env_password(username, password)
    if env_ok:
        token = create_access_token(env_role, subject=username)
        logger.info(f"User '{username}' logged in via environment-based credentials as {env_role}")
        return LoginResponse(
            success=True,
            token=token,
            user=username,
            role=env_role
        )
    
    # Step 2: Check database-backed registered users
    user = db.query(User).filter_by(username=username).first()
    if user:
        # Verify password hash (re-hashes legacy bcrypt to argon2 on success)
        from api.auth import verify_db_user_password
        if verify_db_user_password(db, user, password):
            
            # Check if email is verified for regular users
            if user.role == "user" and not user.email_verified:
                db.add(AuditLog(
                    user_id=user.id,
                    event_type='login_blocked_email_not_verified',
                    ip_address="",
                    user_agent="",
                    success=False,
                    details=json.dumps({"reason": "email_not_verified"})
                ))
                db.commit()
                return LoginResponse(
                    success=False,
                    message="Email not verified. Please check your email."
                )
            
            # Update last_login and log success
            user.last_login = _naive_utcnow()
            db.add(AuditLog(
                user_id=user.id,
                event_type='login',
                ip_address="",
                user_agent="",
                success=True
            ))
            db.commit()
            
            # Generate token
            token = create_access_token(user.role, subject=username)
            logger.info(f"User '{username}' logged in via database-backed credentials as {user.role}")
            return LoginResponse(
                success=True,
                token=token,
                user=username,
                role=user.role
            )
    
    # Step 3: Log failed attempt and return error
    db.add(AuditLog(
        user_id=None,
        event_type='login_failed',
        ip_address="",
        user_agent="",
        success=False,
        details=json.dumps({"username": username})
    ))
    db.commit()
    
    logger.warning(f"Failed login attempt for username: {username}")
    return LoginResponse(
        success=False,
        message="Invalid username or password"
    )


@router.post("/logout")
async def logout():
    """Logout endpoint (stateless; tokens valid until expiry)."""
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=MeResponse)
async def me(user: dict = Depends(get_current_user)):
    """Get current authenticated user from JWT token. Returns role and subject."""
    return MeResponse(role=user["role"], sub=user.get("sub", user["role"]))

# ============================================================================
# PASSWORD VALIDATION UTILITY
# ============================================================================

def _validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain digit"
    if not any(c in "!@#$%^&*()-_+={}[]|:;<>?,./~`" for c in password):
        return False, "Password must contain special character"
    return True, ""


# ============================================================================
# REGISTRATION ENDPOINT
# ============================================================================

@router.post("/register", response_model=RegistrationResponse)
@limiter.limit(AUTH_RATE_LIMIT)  # 10 requests/minute (unauthenticated account creation)
async def register(request: Request, body: RegistrationRequest, db: Session = Depends(get_db)):
    """
    Register a new user account with email verification.
    
    Validates:
    - Username: 3-20 characters, not taken
    - Email: valid format, not taken
    - Password: 8+ chars with uppercase, lowercase, digit, special char
    - CAPTCHA: token provided
    """
    
    # Validate username
    username = (body.username or "").strip()
    if not username or len(username) < 3 or len(username) > 20:
        raise HTTPException(status_code=400, detail="Username must be 3-20 characters")
    
    if db.query(User).filter_by(username=username).first():
        raise HTTPException(status_code=409, detail="Username already taken")
    
    # Validate email
    email = (body.email or "").strip()
    if not email or not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    
    # Validate password
    password = body.password or ""
    is_valid, error_msg = _validate_password_strength(password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Validate CAPTCHA token
    if not body.captcha_token or len(body.captcha_token.strip()) == 0:
        raise HTTPException(status_code=400, detail="CAPTCHA token required")
    
    # Create user
    password_hash = hash_password(password)
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        role="user",
        email_verified=False
    )
    db.add(user)
    db.flush()  # Get user.id
    
    # Create email verification token (24 hour expiry)
    verification_token = secrets.token_urlsafe(32)
    verification = EmailVerificationToken(
        token=verification_token,
        user_id=user.id,
        expires_at=_naive_utcnow() + timedelta(hours=24),
        used=False
    )
    db.add(verification)
    
    # Log registration
    db.add(AuditLog(
        user_id=user.id,
        event_type='register',
        ip_address="",
        user_agent="",
        success=True,
        details=json.dumps({"email": email})
    ))
    db.commit()
    
    logger.info(f"New user registered: {username} ({email})")
    
    # TODO: Send verification email via Phase 4 service
    # await send_verification_email(email, username, verification_token)
    
    return RegistrationResponse(
        message="Registration successful. Check your email for verification link.",
        username=username
    )


# ============================================================================
# EMAIL VERIFICATION ENDPOINT
# ============================================================================

@router.get("/verify-email", response_model=VerificationResponse)
async def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Verify user email with token from registration email.
    
    Validates:
    - Token exists and unused
    - Token not expired
    - Associated user exists
    """
    
    # Find verification token
    verification = db.query(EmailVerificationToken).filter_by(
        token=token,
        used=False
    ).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Invalid or already used verification token")
    
    # Check expiration
    if verification.expires_at < _naive_utcnow():
        verification.used = True
        db.commit()
        raise HTTPException(status_code=410, detail="Verification token expired")
    
    # Get user and verify
    user = db.query(User).get(verification.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Mark email as verified and token as used
    user.email_verified = True
    verification.used = True
    
    # Log verification
    db.add(AuditLog(
        user_id=user.id,
        event_type='email_verified',
        ip_address="",
        user_agent="",
        success=True
    ))
    db.commit()
    
    logger.info(f"Email verified for user: {user.username}")
    
    return VerificationResponse(
        message="Email verified successfully. You can now log in."
    )
