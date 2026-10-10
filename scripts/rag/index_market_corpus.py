#!/usr/bin/env python3
"""
Index market *domain* knowledge into market_rag_chunks for RAG.

What is indexed:
- Markdown docs under docs/ and selected top-level guides (strategy, ML, AI,
  decision factors). These describe how the bot works -- safe domain knowledge.

What is NEVER indexed (trust boundary):
- .env / secrets, Schwab tokens/balances, account data, the auth DB, logs.

Embeddings are produced by the ALFa AI brain (LiteLLM `/v1/embeddings`, model
`embed`). Requires LITELLM_ENABLED=true and a reachable brain.

Usage (from ):
    cd /home/operator/market-pie5-bot
    python3 scripts/rag/index_market_corpus.py            # index defaults
    python3 scripts/rag/index_market_corpus.py --reset    # wipe + reindex
    python3 scripts/rag/index_market_corpus.py --paths docs README.md
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text  # noqa: E402

# Domain doc sources (relative to repo root). Add more as needed.
DEFAULT_SOURCES = [
    "docs",
    "README.md",
    "ML_GUIDE.md",
    "AI_IMPROVEMENTS_GUIDE.md",
    "SHORT_SELLING_GUIDE.md",
    "MISSION.md",
]

# Never index these (defense-in-depth on top of source allow-list).
EXCLUDE_NAME_SUBSTRINGS = [
    ".env",
    "secret",
    "token",
    "credential",
    "password",
    "bot_auth",
    ".key",
]

CHUNK_CHARS = 1200
CHUNK_OVERLAP = 150


def _excluded(path: Path) -> bool:
    low = str(path).lower()
    return any(sub in low for sub in EXCLUDE_NAME_SUBSTRINGS)


def iter_markdown_files(sources: Iterable[str]) -> List[Path]:
    files: List[Path] = []
    for src in sources:
        p = (PROJECT_ROOT / src).resolve()
        if not str(p).startswith(str(PROJECT_ROOT)):
            continue  # path traversal guard
        if p.is_dir():
            for f in sorted(p.rglob("*.md")):
                if not _excluded(f):
                    files.append(f)
        elif p.is_file() and p.suffix.lower() == ".md" and not _excluded(p):
            files.append(p)
    return files


def chunk_text(content: str) -> List[str]:
    content = content.strip()
    if not content:
        return []
    chunks: List[str] = []
    start = 0
    n = len(content)
    while start < n:
        end = min(start + CHUNK_CHARS, n)
        chunks.append(content[start:end])
        if end >= n:
            break
        start = end - CHUNK_OVERLAP
    return chunks


def main() -> int:
    parser = argparse.ArgumentParser(description="Index market domain docs for RAG")
    parser.add_argument("--paths", nargs="*", default=None, help="Override source paths")
    parser.add_argument("--reset", action="store_true", help="Delete existing chunks first")
    parser.add_argument("--batch", type=int, default=16, help="Embedding batch size")
    args = parser.parse_args()

    if os.getenv("LITELLM_ENABLED", "false").strip().lower() not in ("true", "1", "yes"):
        print("ERROR: LITELLM_ENABLED is not true. Enable the ALFa AI brain first.")
        return 2

    from database import engine
    from api.services.ai_tables import ensure_ai_tables
    from api.services.litellm_client import litellm_embeddings_sync

    ensure_ai_tables(engine)

    sources = args.paths if args.paths else DEFAULT_SOURCES
    files = iter_markdown_files(sources)
    if not files:
        print("No markdown files found to index.")
        return 1
    print(f"Found {len(files)} markdown file(s) to index.")

    if args.reset:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM market_rag_chunks"))
            conn.commit()
        print("Cleared existing market_rag_chunks.")

    total_chunks = 0
    for f in files:
        rel = str(f.relative_to(PROJECT_ROOT))
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"  skip {rel}: {e}")
            continue
        chunks = chunk_text(content)
        if not chunks:
            continue

        # Remove prior chunks for this source (idempotent re-index)
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM market_rag_chunks WHERE source = :s"), {"s": rel})
            conn.commit()

        # Embed in batches
        for i in range(0, len(chunks), args.batch):
            batch = chunks[i : i + args.batch]
            emb = litellm_embeddings_sync(batch, trust_zone="app_authenticated")
            if emb.get("error") or not emb.get("vectors"):
                print(f"  embedding failed for {rel} batch {i}: {emb.get('error')}")
                return 3
            vectors = emb["vectors"]
            model = emb.get("model", "embed")
            now = datetime.now(timezone.utc)
            with engine.connect() as conn:
                for j, (chunk, vec) in enumerate(zip(batch, vectors)):
                    conn.execute(
                        text(
                            """
                            INSERT INTO market_rag_chunks
                                (created_at, source, chunk_index, chunk_text, embedding, embed_model, dim)
                            VALUES (:created_at, :source, :idx, :chunk, :emb, :model, :dim)
                            """
                        ),
                        {
                            "created_at": now,
                            "source": rel,
                            "idx": i + j,
                            "chunk": chunk,
                            "emb": json.dumps(vec),
                            "model": model,
                            "dim": len(vec),
                        },
                    )
                conn.commit()
            total_chunks += len(batch)
        print(f"  indexed {rel}: {len(chunks)} chunk(s)")

    print(f"Done. Indexed {total_chunks} chunk(s) from {len(files)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
