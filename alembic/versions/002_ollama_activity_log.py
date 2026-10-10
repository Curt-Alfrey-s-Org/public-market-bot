"""ollama_activity_log table for the AI Monitor dashboard.

Revision ID: 002
Revises: 001
Create Date: 2026-06-02

Stores every LiteLLM/Ollama API call: prompt, response, model, duration,
feature area, errors. Enables the admin AI Monitor page to show what the
ALFa AI brain is doing for market-pie5-bot.

Note: at runtime the app also creates this table idempotently at startup via
api.services.ai_tables.ensure_ai_tables (the app uses Base.metadata.create_all,
not `alembic upgrade`). This migration is provided for operators who run
migrations explicitly.
"""

from alembic import op
from sqlalchemy import text

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS ollama_activity_log (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            feature TEXT NOT NULL,
            model TEXT NOT NULL,
            prompt_summary TEXT,
            request_text TEXT,
            response_text TEXT,
            duration_seconds FLOAT,
            eval_tokens INTEGER DEFAULT 0,
            prompt_tokens INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'success',
            error_message TEXT,
            metadata JSONB DEFAULT '{}'
        )
    """))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_ollama_activity_created ON ollama_activity_log (created_at DESC)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_ollama_activity_feature ON ollama_activity_log (feature)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_ollama_activity_status ON ollama_activity_log (status)"
    ))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS ollama_activity_log"))
