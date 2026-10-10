"""finetune_samples table for opt-in fine-tune capture.

Revision ID: 005
Revises: 004
Create Date: 2026-06-02

Stores redacted (messages -> completion) pairs for later export to a
fine-tuning dataset. Opt-in (FINETUNE_CAPTURE_ENABLED) with retention
(FINETUNE_RETENTION_DAYS). Never stores secrets (redacted before insert).

Note: at runtime the app also creates this table idempotently at startup via
api.services.ai_tables.ensure_ai_tables.
"""

from alembic import op
from sqlalchemy import text

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS finetune_samples (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            feature TEXT NOT NULL,
            model TEXT,
            messages TEXT NOT NULL,
            completion TEXT NOT NULL,
            redacted BOOLEAN NOT NULL DEFAULT true,
            retain_until TIMESTAMPTZ
        )
    """))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_finetune_retain_until ON finetune_samples (retain_until)"
    ))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS finetune_samples"))
