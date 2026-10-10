"""
Idempotent creation of ALFa AI support tables.

market-pie5-bot creates its schema at startup via `Base.metadata.create_all`
(see api/main.py lifespan), not via `alembic upgrade`. These tables are not
SQLAlchemy ORM models, so this helper creates them with CREATE TABLE IF NOT
EXISTS during the same startup step. Alembic migrations are also provided
(alembic/versions/002_*, 003_*) for operators who run migrations explicitly.

Tables:
- ollama_activity_log : telemetry for every LiteLLM/Ollama call (AI Monitor)
- error_events        : captured runtime errors + alfa-ai triage results

Supports PostgreSQL (production) and SQLite (local dev fallback).
"""

import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


_PG_OLLAMA = """
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
"""

_SQLITE_OLLAMA = """
CREATE TABLE IF NOT EXISTS ollama_activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    feature TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_summary TEXT,
    request_text TEXT,
    response_text TEXT,
    duration_seconds REAL,
    eval_tokens INTEGER DEFAULT 0,
    prompt_tokens INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'success',
    error_message TEXT,
    metadata TEXT DEFAULT '{}'
)
"""

_PG_ERROR_EVENTS = """
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
"""

_SQLITE_ERROR_EVENTS = """
CREATE TABLE IF NOT EXISTS error_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fingerprint TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT,
    path TEXT,
    method TEXT,
    request_id TEXT,
    traceback TEXT,
    count INTEGER NOT NULL DEFAULT 1,
    first_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    triage_status TEXT NOT NULL DEFAULT 'pending',
    triage_summary TEXT,
    triage_model TEXT,
    triaged_at TIMESTAMP
)
"""

_PG_RAG_CHUNKS = """
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
"""

_SQLITE_RAG_CHUNKS = """
CREATE TABLE IF NOT EXISTS market_rag_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source TEXT NOT NULL,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    chunk_text TEXT NOT NULL,
    embedding TEXT NOT NULL,
    embed_model TEXT,
    dim INTEGER DEFAULT 0
)
"""

_PG_FINETUNE = """
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
"""

_SQLITE_FINETUNE = """
CREATE TABLE IF NOT EXISTS finetune_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    feature TEXT NOT NULL,
    model TEXT,
    messages TEXT NOT NULL,
    completion TEXT NOT NULL,
    redacted INTEGER NOT NULL DEFAULT 1,
    retain_until TIMESTAMP
)
"""

_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_ollama_activity_created ON ollama_activity_log (created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_ollama_activity_feature ON ollama_activity_log (feature)",
    "CREATE INDEX IF NOT EXISTS idx_ollama_activity_status ON ollama_activity_log (status)",
    "CREATE INDEX IF NOT EXISTS idx_error_events_fingerprint ON error_events (fingerprint)",
    "CREATE INDEX IF NOT EXISTS idx_error_events_triage_status ON error_events (triage_status)",
    "CREATE INDEX IF NOT EXISTS idx_error_events_last_seen ON error_events (last_seen DESC)",
    "CREATE INDEX IF NOT EXISTS idx_market_rag_source ON market_rag_chunks (source)",
    "CREATE INDEX IF NOT EXISTS idx_finetune_retain_until ON finetune_samples (retain_until)",
]


def ensure_ai_tables(engine) -> None:
    """Create the ollama_activity_log and error_events tables if missing.

    Best-effort: logs and returns on failure so startup is never blocked.
    """
    if engine is None:
        return
    try:
        is_sqlite = engine.dialect.name == "sqlite"
        ollama_ddl = _SQLITE_OLLAMA if is_sqlite else _PG_OLLAMA
        error_ddl = _SQLITE_ERROR_EVENTS if is_sqlite else _PG_ERROR_EVENTS
        rag_ddl = _SQLITE_RAG_CHUNKS if is_sqlite else _PG_RAG_CHUNKS
        finetune_ddl = _SQLITE_FINETUNE if is_sqlite else _PG_FINETUNE
        with engine.connect() as conn:
            conn.execute(text(ollama_ddl))
            conn.execute(text(error_ddl))
            conn.execute(text(rag_ddl))
            conn.execute(text(finetune_ddl))
            for idx in _INDEXES:
                conn.execute(text(idx))
            conn.commit()
        logger.info(
            "[STARTUP] ALFa AI tables ensured "
            "(ollama_activity_log, error_events, market_rag_chunks, finetune_samples)"
        )
    except Exception as e:
        logger.warning("Could not ensure ALFa AI tables: %s", e)
