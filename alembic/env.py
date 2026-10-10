"""
Alembic environment configuration.

This module initializes Alembic for database migrations with SQLAlchemy.
Updated for PostgreSQL migration - reads DATABASE_URL from environment.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add project root to path so we can import from database and models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the database configuration and engine
from database import engine, DATABASE_URL, Base

# Import all models to ensure they're registered with Base.metadata
from api.models.user import Base as UserBase  # Auth models
from log_manager import TradeLog, SystemLog, BacktestResult, PerformanceMetric  # Trading models

# This is the Alembic Config object
config = context.config

# Override sqlalchemy.url with DATABASE_URL from environment or database.py
config.set_main_option('sqlalchemy.url', DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add metadata object for 'autogenerate' support
# This includes both auth and trading models
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.
    """
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
