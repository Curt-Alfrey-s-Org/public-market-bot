"""
Auth: JWT-based admin, director, and user accounts.
- Admin: full access (refresh, settings). Credentials from env ADMIN_USERNAME, ADMIN_PASSWORD.
- Director: data input (e.g. batch actions). Credentials from env DIRECTOR_USERNAME, DIRECTOR_PASSWORD.
- User: view-only access. Credentials from env USER_USERNAME, USER_PASSWORD.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Literal, Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlalchemy.orm import Session
from api.utils.timeutils import utcnow as _naive_utcnow
from api.security_config import get_jwt_secret

logger = logging.getLogger(__name__)

# Required in production (JWT_SECRET); no public fallback. See api/security_config.py.
SECRET_KEY = get_jwt_secret()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# Password hashing (pwdlib, per FastAPI security tutorial:
# https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#password-hashing).
# Argon2 (first hasher) is the current scheme for new hashes; bcrypt is kept only
# to verify legacy hashes created under passlib. verify_and_update() returns an
# argon2 re-hash for any valid bcrypt hash so logins transparently migrate
# (https://frankie567.github.io/
password_hash = PasswordHash((Argon2Hasher(), BcryptHasher()))

security = HTTPBearer(auto_error=False)
optional_bearer = HTTPBearer(auto_error=False)

Role = Literal["admin", "director", "user"]


def _verify_password(plain: str, hashed: str) -> bool:
    """Verify plaintext against a stored hash (argon2 or legacy bcrypt)."""
    if not (plain and hashed):
        return False
    try:
        return password_hash.verify(plain, hashed)
    except (UnknownHashError, ValueError) as e:
        logger.warning("Password verification failed on malformed hash: %s", type(e).__name__)
        return False


def verify_and_update_password(plain: str, hashed: str) -> tuple[bool, str | None]:
    """Verify plaintext against a stored hash; return (valid, updated_hash).

    pwdlib verify_and_update semantics: updated_hash is a new argon2 hash when the
    stored hash uses a deprecated scheme (legacy bcrypt) and should be persisted,
    or None when no re-hash is needed. Callers with a DB session must save the
    updated hash so logins transparently migrate off bcrypt.
    """
    if not (plain and hashed):
        return False, None
    try:
        return password_hash.verify_and_update(plain, hashed)
    except (UnknownHashError, ValueError) as e:
        logger.warning("Password verification failed on malformed hash: %s", type(e).__name__)
        return False, None


def create_access_token(role: Role, subject: str = "") -> str:
    """Create a JWT with role and optional subject."""
    expire = _naive_utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": subject or role,
        "role": role,
        "exp": expire,
        "iat": _naive_utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate JWT; raise HTTPException if invalid."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Dependency: require valid Bearer token; return payload with role."""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    role = payload.get("role")
    if role not in ("admin", "director", "user"):
        raise HTTPException(status_code=401, detail="Invalid role")
    return payload


def authenticate_bearer_token(token: str) -> dict | None:
    """Validate a Bearer token for the API auth gate; return its payload or None.

    Accepts access tokens signed with SECRET_KEY that carry a known role
    (web login) or are v1 access tokens (mobile login). Refresh tokens and
    tokens with an unknown role (e.g. "guest") are rejected. The role always
    comes from the signed token, never from a client-sent header.
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    if payload.get("type") == "refresh":
        return None
    if payload.get("role") in ("admin", "director", "user"):
        return payload
    return None


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
) -> dict | None:
    """Dependency: optional auth; return payload or None."""
    if not credentials:
        return None
    try:
        return decode_token(credentials.credentials)
    except HTTPException:
        return None


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dependency: require admin role."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user


def require_director_or_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dependency: require director or admin role."""
    if user.get("role") not in ("admin", "director"):
        raise HTTPException(status_code=403, detail="Director or Admin only")
    return user


def verify_db_user_password(db: Session, user, password: str) -> bool:
    """Verify a DB-backed user's password; transparently re-hash legacy bcrypt hashes.

    On a successful verify against a deprecated hash, the new argon2 hash is
    persisted immediately so the migration happens on first login.
    """
    valid, updated_hash = verify_and_update_password(password, user.password_hash)
    if valid and updated_hash:
        try:
            user.password_hash = updated_hash
            db.commit()
            logger.info("Re-hashed legacy password hash to argon2 for user '%s'", user.username)
        except Exception as e:
            # Login still succeeds; re-hash will be retried on next login.
            logger.warning("Failed to persist re-hashed password for user '%s': %s", user.username, e)
            db.rollback()
    return valid


# Admin credentials from env

def get_admin_username() -> str:
    return os.getenv("ADMIN_USERNAME", "admin")


def get_admin_password_hash() -> str | None:
    return os.getenv("ADMIN_PASSWORD_HASH")


def check_admin_password(username: str, password: str, db: Optional[Session] = None) -> bool:
    """Check admin password against database or env vars (fallback)."""
    # Try database first if available
    if db:
        try:
            from api.models.user import User
            user = db.query(User).filter_by(username=username).first()
            if user and user.role == "admin" and verify_db_user_password(db, user, password):
                return True
            # If user exists but password wrong, fall through to env
        except Exception as e:
            logger.warning(f"Database lookup failed for admin: {e}, falling back to env vars")
    
    # Fallback to env vars for backward compatibility
    expected_user = get_admin_username()
    if username != expected_user:
        return False
    stored_hash = get_admin_password_hash()
    if stored_hash:
        return _verify_password(password, stored_hash)
    plain = os.getenv("ADMIN_PASSWORD")
    if not plain:
        logger.warning("ADMIN_PASSWORD and ADMIN_PASSWORD_HASH not set; admin login disabled")
        return False
    return password == plain


# Director credentials from env

def get_director_username() -> str:
    return os.getenv("DIRECTOR_USERNAME", "director")


def get_director_password_hash() -> str | None:
    return os.getenv("DIRECTOR_PASSWORD_HASH")


def check_director_password(username: str, password: str, db: Optional[Session] = None) -> bool:
    """Check director password against database or env vars (fallback)."""
    # Try database first if available (director may not exist in new User model, but support for backward compat)
    if db:
        try:
            from api.models.user import User
            user = db.query(User).filter_by(username=username).first()
            if user and user.role in ("admin", "moderator") and verify_db_user_password(db, user, password):
                return True
            # If user exists but password wrong, fall through to env
        except Exception as e:
            logger.warning(f"Database lookup failed for director: {e}, falling back to env vars")
    
    # Fallback to env vars for backward compatibility
    expected_user = get_director_username()
    if username != expected_user:
        return False
    stored_hash = get_director_password_hash()
    if stored_hash:
        return _verify_password(password, stored_hash)
    plain = os.getenv("DIRECTOR_PASSWORD")
    if not plain:
        logger.warning("DIRECTOR_PASSWORD and DIRECTOR_PASSWORD_HASH not set; director login disabled")
        return False
    return password == plain


# User credentials from env

def get_user_username() -> str:
    return os.getenv("USER_USERNAME", "user")


def get_user_password_hash() -> str | None:
    return os.getenv("USER_PASSWORD_HASH")


def check_user_password(username: str, password: str, db: Optional[Session] = None) -> bool:
    """Check user password against database or env vars (fallback)."""
    # Try database first if available
    if db:
        try:
            from api.models.user import User
            user = db.query(User).filter_by(username=username).first()
            if user and user.role == "user" and verify_db_user_password(db, user, password):
                return True
            # If user exists but password wrong, fall through to env
        except Exception as e:
            logger.warning(f"Database lookup failed for user: {e}, falling back to env vars")
    
    # Fallback to env vars for backward compatibility
    expected_user = get_user_username()
    if username != expected_user:
        return False
    stored_hash = get_user_password_hash()
    if stored_hash:
        return _verify_password(password, stored_hash)
    plain = os.getenv("USER_PASSWORD")
    if not plain:
        logger.warning("USER_PASSWORD and USER_PASSWORD_HASH not set; user login disabled")
        return False
    return password == plain


def require_admin_user(user: dict = Depends(get_current_user)) -> dict:
    """Dependency: require admin role from authenticated user."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_authenticated_user(user: dict = Depends(get_current_user)) -> dict:
    """Dependency: require any authenticated user."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def hash_password(password: str) -> str:
    """Hash a plaintext password using argon2 (current scheme)."""
    return password_hash.hash(password)
