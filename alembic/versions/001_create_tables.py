"""
Initial database migration: Create user authentication tables.

Revision ID: 001
Create Date: 2026-02-06

This migration creates the initial schema for the user authentication system:
- users table: Stores user account information
- email_verification_tokens table: Stores email verification tokens
- audit_log table: Stores authentication and security events
"""

from alembic import op

# Revision identifiers used by Alembic. Without them the chain 001 -> 002 -> ...
# could not be resolved and every `alembic` command failed (review 2026-09-25).
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Upgrade database schema to version 001.
    
    Creates three tables:
    1. users - Main user account table
    2. email_verification_tokens - Email verification tokens
    3. audit_log - Audit logging for security events
    """
    # Create all tables using the Base metadata, on Alembic's connection
    # (idempotent: create_all skips tables that already exist).
    from api.models.user import Base
    Base.metadata.create_all(bind=op.get_bind())


def downgrade():
    """
    Downgrade database schema from version 001.
    
    Drops all tables created in the upgrade() function.
    """
    from api.models.user import Base
    
    Base.metadata.drop_all(bind=op.get_bind())
