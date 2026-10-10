"""market_rag_chunks table for RAG over market domain knowledge.

Revision ID: 004
Revises: 003
Create Date: 2026-06-02

Stores embedded chunks of domain documentation (strategy/ML/AI guides). Vectors
are stored as JSON text; cosine similarity is computed in Python (no pgvector
dependency). Only domain docs are indexed -- never Schwab tokens/balances.

Note: at runtime the app also creates this table idempotently at startup via
api.services.ai_tables.ensure_ai_tables.
"""

from alembic import op
from sqlalchemy import text

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS market_rag_chunks (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            source TEXT NOT NULL,
            chunk_index INTEGER NOT NULL DEFAULT 0,
            chunk_text TEXT NOT NULL,
            embedding TEXT NOT NULL,
            embed_model TEXT,
            dim INTEGER DEFAULT 0
        )
    """))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_market_rag_source ON market_rag_chunks (source)"
    ))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS market_rag_chunks"))
