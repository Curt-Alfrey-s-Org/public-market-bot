"""
RAG retriever over market *domain* knowledge.

Embeddings are produced by the ALFa AI brain (LiteLLM `/v1/embeddings`, model
`embed`) and stored in `market_rag_chunks`. Retrieval embeds the query and
ranks chunks by cosine similarity in Python (no pgvector dependency, so this
works on both Postgres and the SQLite dev fallback).

Trust boundary: only domain documentation/strategy/factor text is ever indexed
(see scripts/rag/index_market_corpus.py). Schwab tokens, balances, and account
data are never embedded or stored here.
"""

import json
import logging
import math
from typing import Any, Dict, List, Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)


def _engine():
    try:
        from database import engine
        return engine
    except Exception:
        return None


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def chunk_count() -> int:
    engine = _engine()
    if engine is None:
        return 0
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT COUNT(*) FROM market_rag_chunks")).fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0


def retrieve(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Return the top_k most similar domain chunks for a query.

    Best-effort: returns [] if RAG is empty, embeddings fail, or the brain is
    unreachable.
    """
    engine = _engine()
    if engine is None or not query:
        return []

    try:
        from api.services.litellm_client import litellm_embeddings_sync, is_litellm_enabled
    except Exception:
        return []
    if not is_litellm_enabled():
        return []

    emb = litellm_embeddings_sync([query], trust_zone="app_authenticated")
    if emb.get("error") or not emb.get("vectors"):
        logger.debug("market_rag: query embedding failed: %s", emb.get("error"))
        return []
    qvec = emb["vectors"][0]

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT id, source, chunk_index, chunk_text, embedding FROM market_rag_chunks")
            ).fetchall()
    except Exception as e:
        logger.debug("market_rag: could not load chunks: %s", e)
        return []

    scored: List[Dict[str, Any]] = []
    for r in rows:
        try:
            vec = json.loads(r[4]) if r[4] else []
        except Exception:
            continue
        score = _cosine(qvec, vec)
        scored.append(
            {"id": r[0], "source": r[1], "chunk_index": r[2], "chunk_text": r[3], "score": score}
        )
    scored.sort(key=lambda d: d["score"], reverse=True)
    return scored[: max(1, min(top_k, 20))]


def build_rag_context(query: str, top_k: int = 5, max_chars: int = 4000) -> Optional[str]:
    """Return a formatted context block of the top chunks, or None if empty."""
    hits = retrieve(query, top_k=top_k)
    if not hits:
        return None
    parts: List[str] = []
    used = 0
    for h in hits:
        block = f"[source: {h['source']}#{h['chunk_index']} score={h['score']:.2f}]\n{h['chunk_text']}"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n\n".join(parts) if parts else None
