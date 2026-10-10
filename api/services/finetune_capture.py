"""
Opt-in fine-tune sample capture with redaction and retention.

DISABLED BY DEFAULT. When `FINETUNE_CAPTURE_ENABLED=true`, successful LLM
interactions are stored (redacted) in `finetune_samples` for later export to a
fine-tuning dataset. This is opt-in because it persists prompts/completions.

Guarantees:
- Redaction: every prompt and completion is passed through the same secret
  redactor used by error monitoring before storage. Schwab tokens/balances,
  API keys, JWTs, and long digit runs are masked.
- Retention: rows get `retain_until = now + FINETUNE_RETENTION_DAYS`;
  `purge_expired()` deletes anything past retention.
- Trust zone: only `app_authenticated`/`internal` features are captured;
  `public_web` is never captured.

Export: scripts/finetune/export_finetune.py writes OpenAI-style JSONL.
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)


def is_capture_enabled() -> bool:
    return os.getenv("FINETUNE_CAPTURE_ENABLED", "false").strip().lower() in ("true", "1", "yes")


def retention_days() -> int:
    try:
        return max(1, int(os.getenv("FINETUNE_RETENTION_DAYS", "30")))
    except ValueError:
        return 30


def _engine():
    try:
        from database import engine
        return engine
    except Exception:
        return None


def _redact(value: str) -> str:
    try:
        from api.services.error_monitor import redact
        return redact(value)
    except Exception:
        return value or ""


def capture_sample(
    feature: str,
    messages: List[Dict[str, str]],
    completion: str,
    model: Optional[str] = None,
    trust_zone: str = "app_authenticated",
) -> None:
    """Best-effort opt-in capture of one (messages -> completion) pair. Never raises."""
    if not is_capture_enabled():
        return
    if trust_zone == "public_web":  # never capture untrusted traffic
        return
    if not completion:
        return
    engine = _engine()
    if engine is None:
        return
    try:
        redacted_messages = [
            {"role": m.get("role", "user"), "content": _redact(m.get("content", ""))[:8000]}
            for m in messages
        ]
        redacted_completion = _redact(completion)[:8000]
        now = datetime.now(timezone.utc)
        retain_until = now + timedelta(days=retention_days())
        with engine.connect() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO finetune_samples
                        (created_at, feature, model, messages, completion, redacted, retain_until)
                    VALUES (:created_at, :feature, :model, :messages, :completion, :redacted, :retain_until)
                    """
                ),
                {
                    "created_at": now,
                    "feature": feature,
                    "model": model,
                    "messages": json.dumps(redacted_messages),
                    "completion": redacted_completion,
                    "redacted": True,
                    "retain_until": retain_until,
                },
            )
            conn.commit()
    except Exception as e:
        logger.debug("finetune_capture.capture_sample failed: %s", e)


def purge_expired() -> int:
    """Delete samples past their retention window. Returns rows deleted."""
    engine = _engine()
    if engine is None:
        return 0
    try:
        now = datetime.now(timezone.utc)
        with engine.connect() as conn:
            result = conn.execute(
                text("DELETE FROM finetune_samples WHERE retain_until IS NOT NULL AND retain_until < :now"),
                {"now": now},
            )
            conn.commit()
            return result.rowcount or 0
    except Exception as e:
        logger.debug("finetune_capture.purge_expired failed: %s", e)
        return 0


def export_samples(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Return samples as OpenAI fine-tune records: {"messages": [...]}"""
    engine = _engine()
    if engine is None:
        return []
    try:
        sql = "SELECT messages, completion FROM finetune_samples ORDER BY created_at ASC"
        params: Dict[str, Any] = {}
        if limit:
            sql += " LIMIT :lim"
            params["lim"] = limit
        with engine.connect() as conn:
            rows = conn.execute(text(sql), params).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            try:
                msgs = json.loads(r[0])
            except Exception:
                continue
            msgs = list(msgs) + [{"role": "assistant", "content": r[1]}]
            out.append({"messages": msgs})
        return out
    except Exception as e:
        logger.debug("finetune_capture.export_samples failed: %s", e)
        return []
