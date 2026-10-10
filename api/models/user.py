"""
SQLAlchemy ORM model for user authentication system.

This module defines the core data model for user account management,
including user accounts with authentication and profile information.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, CheckConstraint, Index
from datetime import datetime
from database import Base
from api.utils.timeutils import utcnow as _naive_utcnow


class User(Base):
    """
    User account model for storing user authentication and profile information.
    
    Attributes:
        id: Primary key, auto-incremented integer
        username: Unique username for login (max 50 chars)
        email: Unique email address (max 120 chars)
        password_hash: Hashed password using argon2 (legacy bcrypt hashes re-hashed on login; max 255 chars)
        role: User role (default: "user", can be "admin", "director")
        email_verified: Boolean flag for email verification status
        totp_secret: Optional TOTP secret for 2FA (max 32 chars)
        totp_enabled: Boolean flag for 2FA enablement
        created_at: Account creation timestamp
        last_login: Last successful login timestamp
        failed_login_attempts: Counter for failed login attempts
        account_locked_until: Timestamp for account lockout period
        is_active: Boolean flag for account activation status
    """
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    email_verified = Column(Boolean, default=False)
    totp_secret = Column(String(32), nullable=True)
    totp_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    __table_args__ = (
        CheckConstraint("failed_login_attempts >= 0", name="check_failed_login_non_negative"),
        CheckConstraint("role IN ('user', 'admin', 'director')", name="check_role_values"),
        Index("idx_username_active", "username", "is_active"),
        Index("idx_email_verified", "email", "email_verified"),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email}, is_active={self.is_active})>"
