"""
Database configuration and session management for SQLAlchemy ORM.

Performance Optimizations:
- Connection pooling with QueuePool for PostgreSQL (default)
- StaticPool fallback for SQLite in development
- WAL mode and SQLite pragmas for concurrent access (SQLite only)
- Query result caching via session identity map
- Connection recycling to prevent stale connections
"""

from typing import Generator
from sqlalchemy import create_engine, event as sa_event
# declarative_base moved to sqlalchemy.orm in SQLAlchemy 2.0 (https://sqlalche.me/e/b8d9)
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool, QueuePool
from contextlib import contextmanager
import os
import logging

logger = logging.getLogger(__name__)

# Database URL configuration from environment
# Falls back to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bot_auth.db")

# Detect database type
is_sqlite = DATABASE_URL.startswith("sqlite")
is_postgres = DATABASE_URL.startswith("postgresql")

# Configure engine parameters based on database type
if is_sqlite:
    # SQLite-specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite specific
        echo=False,  # Set to True for SQL debugging
        poolclass=StaticPool,  # Use StaticPool for SQLite thread safety
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_pre_ping=True,  # Test connections before using
    )
    logger.info("Database: SQLite configured with StaticPool")
    
elif is_postgres:
    # PostgreSQL-specific configuration with connection pooling
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL debugging
        poolclass=QueuePool,  # QueuePool is default for PostgreSQL
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
        pool_pre_ping=True,  # Test connections before using
        # PostgreSQL-specific connect_args for better performance
        connect_args={
            "connect_timeout": 10,
            "application_name": "market-pie5-bot",
        }
    )
    logger.info(f"Database: PostgreSQL configured with QueuePool (size={os.getenv('DB_POOL_SIZE', '10')})")
    
else:
    # Fallback for unsupported database types
    raise ValueError(f"Unsupported database type in DATABASE_URL: {DATABASE_URL}")


# Configure SQLite for better concurrent performance (SQLite only)
if is_sqlite:
    @sa_event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """
        Configure SQLite pragmas for optimization:
        - journal_mode=WAL: Write-Ahead Logging (better concurrency)
        - synchronous=NORMAL: Balance safety/performance
        - cache_size=-64000: 64MB query cache
        - temp_store=MEMORY: Use RAM for temp storage
        """
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create declarative base for ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency function that yields a database session.
    
    This function creates a new database session for each request
    and ensures it's properly closed after the request completes.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions outside of FastAPI routes.
    
    Usage:
        with get_db_context() as db:
            user = db.query(User).first()
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database by creating all tables defined in Base.metadata.
    
    This should be called at application startup to ensure all tables exist.
    """
    from api.models.user import Base
    Base.metadata.create_all(bind=engine)


# ============================================================================
# INDEX OPTIMIZATION GUIDE
# ============================================================================
# For further performance improvements, add these indexes to your models:
#
# User Model:
#   - Index on 'email' (authentication lookups)
#   - Index on 'username' (profile lookups)
#   - Index on 'created_at' (sorting operations)
#
# Trade History Model:
#   - Composite index on (user_id, created_at) for user trade lookups
#   - Index on 'trade_type' (filtering by buy/sell)
#   - Index on 'symbol' (cross-symbol analytics)
#
# Position Model:
#   - Composite index on (user_id, symbol) for quick position lookups
#   - Index on 'status' (filtering active positions)
#
# SQL to create indexes (run manually if needed):
#   CREATE INDEX IF NOT EXISTS idx_user_email ON user(email);
#   CREATE INDEX IF NOT EXISTS idx_user_username ON user(username);
#   CREATE INDEX IF NOT EXISTS idx_trade_user_date ON trade(user_id, created_at DESC);
#   CREATE INDEX IF NOT EXISTS idx_position_user_symbol ON position(user_id, symbol);
