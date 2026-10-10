"""error_events table for automatic error monitoring + alfa-ai triage.

Revision ID: 003
Revises: 002
Create Date: 2026-06-02

Captured runtime errors (from the global exception handlers) are deduplicated
by fingerprint and periodically triaged by the ALFa AI brain. The admin AI
Monitor page reads this table to show recent errors and their triage summaries.

Note: at runtime the app also creates this table idempotently at startup via
api.services.ai_tables.ensure_ai_tables.
"""

from alembic import op
from sqlalchemy import text

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS error_events (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            fingerprint TEXT NOT NULL,
            error_type TEXT NOT NULL,
            error_message TEXT,
            path TEXT,
            method TEXT,
            request_id TEXT,
            traceback TEXT,
            count INTEGER NOT NULL DEFAULT 1,
            first_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
            triage_status TEXT NOT NULL DEFAULT 'pending',
            triage_summary TEXT,
            triage_model TEXT,
            triaged_at TIMESTAMPTZ
        )
    """))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_error_events_fingerprint ON error_events (fingerprint)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_error_events_triage_status ON error_events (triage_status)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_error_events_last_seen ON error_events (last_seen DESC)"
    ))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS error_events"))
