"""
Automatic error monitoring with ALFa AI triage.

Flow:
1. The global exception handlers (api/middleware/error_handler.py) call
   `record_error(...)` for unhandled 5xx errors. Errors are deduplicated by
   fingerprint into the `error_events` table (count + last_seen bumped).
2. A background task (started in the API lifespan) periodically batches
   `pending` errors, redacts secrets, and asks the ALFa AI brain (LiteLLM,
   `internal` trust zone, model `code`) for a root-cause summary, which is
   written back to `error_events.triage_summary`.
3. The admin AI Monitor page reads `error_events` to show recent errors and
   their triage results.

Everything is best-effort and degrades gracefully: capture never raises and
never affects the HTTP response; triage marks rows `pending` (not `error`) when
the brain is unreachable so they are retried on the next batch.
"""

import hashlib
import logging
import os
import re
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def is_error_monitor_enabled() -> bool:
    return os.getenv("ERROR_MONITOR_ENABLED", "true").strip().lower() in ("true", "1", "yes")


def triage_interval_seconds() -> int:
    try:
        return max(30, int(os.getenv("ERROR_MONITOR_INTERVAL_SECONDS", "300")))
    except ValueError:
        return 300


def triage_batch_size() -> int:
    try:
        return max(1, int(os.getenv("ERROR_MONITOR_BATCH_SIZE", "10")))
    except ValueError:
        return 10


# ---------------------------------------------------------------------------
# Secret redaction (defense-in-depth before anything is persisted or sent)
# ---------------------------------------------------------------------------

_REDACTION_PATTERNS = [
    (re.compile(r"(SCHWAB_[A-Z_]*\s*[=:]\s*)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(HUGGINGFACE_[A-Z_]*\s*[=:]\s*)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(BOT_API_KEY\s*[=:]\s*)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(LITELLM_API_KEY[A-Z_]*\s*[=:]\s*)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(ALFA_AI_API_TOKEN\s*[=:]\s*)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(authorization:\s*bearer\s+)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{6,}\b"), "[REDACTED_KEY]"),
    (re.compile(r"\bhf_[A-Za-z0-9]{6,}\b"), "[REDACTED_KEY]"),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"), "[REDACTED_JWT]"),
    # Account-number-ish long digit runs and dollar balances
    (re.compile(r"\b\d{8,}\b"), "[REDACTED_NUM]"),
]


def redact(value: Optional[str]) -> str:
    if not value:
        return ""
    out = value
    for pattern, repl in _REDACTION_PATTERNS:
        out = pattern.sub(repl, out)
    return out


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------

def _fingerprint(error_type: str, method: str, path: str, message: str) -> str:
    basis = f"{error_type}|{method}|{path}|{(message or '')[:200]}"
    return hashlib.sha1(basis.encode("utf-8", errors="ignore"), usedforsecurity=False).hexdigest()


def _engine():
    try:
        from database import engine
        return engine
    except Exception:
        return None


def record_error(
    error_type: str,
    error_message: str,
    path: str = "",
    method: str = "",
    request_id: str = "",
    traceback_text: str = "",
) -> None:
    """Best-effort capture of a runtime error into error_events. Never raises."""
    if not is_error_monitor_enabled():
        return
    engine = _engine()
    if engine is None:
        return
    try:
        msg = redact(error_message)[:2000]
        tb = redact(traceback_text)[:8000]
        fp = _fingerprint(error_type, method, path, msg)
        now = datetime.now(timezone.utc)
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, count FROM error_events WHERE fingerprint = :fp"),
                {"fp": fp},
            ).fetchone()
            if row:
                conn.execute(
                    text(
                        """
                        UPDATE error_events
                        SET count = count + 1,
                            last_seen = :now,
                            error_message = :msg,
                            traceback = :tb,
                            request_id = :rid,
                            triage_status = CASE
                                WHEN triage_status = 'triaged' THEN 'pending'
                                ELSE triage_status END
                        WHERE id = :id
                        """
                    ),
                    {"now": now, "msg": msg, "tb": tb, "rid": (request_id or "")[:64], "id": row[0]},
                )
            else:
                conn.execute(
                    text(
                        """
                        INSERT INTO error_events
                            (fingerprint, error_type, error_message, path, method,
                             request_id, traceback, count, first_seen, last_seen, triage_status)
                        VALUES
                            (:fp, :etype, :msg, :path, :method,
                             :rid, :tb, 1, :now, :now, 'pending')
                        """
                    ),
                    {
                        "fp": fp,
                        "etype": (error_type or "Exception")[:200],
                        "msg": msg,
                        "path": (path or "")[:500],
                        "method": (method or "")[:16],
                        "rid": (request_id or "")[:64],
                        "tb": tb,
                        "now": now,
                    },
                )
            conn.commit()
    except Exception as e:
        logger.debug("error_monitor.record_error failed: %s", e)


# ---------------------------------------------------------------------------
# Triage (runs OFF the event loop via asyncio.to_thread)
# ---------------------------------------------------------------------------

_TRIAGE_SYSTEM_PROMPT = (
    "You are an SRE assistant for the market-pie5-bot trading application "
    "(FastAPI backend on host ). You are given one recurring runtime error "
    "(type, endpoint, count, and a redacted traceback). Respond with a concise "
    "root-cause hypothesis and 1-3 concrete next steps for an engineer. Be "
    "specific and brief (<= 150 words). Do not include any secrets. This is an "
    "internal ops aid, not user-facing."
)


def _build_triage_prompt(ev: Dict[str, Any]) -> str:
    return (
        f"Error type: {ev.get('error_type')}\n"
        f"Endpoint: {ev.get('method')} {ev.get('path')}\n"
        f"Occurrences: {ev.get('count')}\n"
        f"Message: {ev.get('error_message')}\n\n"
        f"Redacted traceback:\n{ev.get('traceback') or '(none)'}"
    )


def run_triage_batch(limit: Optional[int] = None) -> int:
    """Triage up to `limit` pending errors via LiteLLM (internal zone, model code).

    Synchronous; intended to be invoked via asyncio.to_thread from the
    background loop, or directly from an admin on-demand endpoint. Returns the
    number of errors successfully triaged.
    """
    if not is_error_monitor_enabled():
        return 0
    engine = _engine()
    if engine is None:
        return 0

    try:
        from api.services.litellm_client import (
            is_litellm_enabled,
            litellm_chat_completion_sync,
            litellm_model_for_trust_zone,
            TRUST_ZONE_INTERNAL,
        )
    except Exception as e:
        logger.debug("error_monitor: litellm client unavailable: %s", e)
        return 0

    if not is_litellm_enabled():
        return 0

    batch = limit or triage_batch_size()
    model = litellm_model_for_trust_zone(TRUST_ZONE_INTERNAL)

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT id, error_type, error_message, path, method, traceback, count
                    FROM error_events
                    WHERE triage_status = 'pending'
                    ORDER BY last_seen DESC
                    LIMIT :lim
                    """
                ),
                {"lim": batch},
            ).fetchall()
    except Exception as e:
        logger.debug("error_monitor: could not select pending errors: %s", e)
        return 0

    triaged = 0
    for r in rows:
        ev = {
            "id": r[0], "error_type": r[1], "error_message": r[2],
            "path": r[3], "method": r[4], "traceback": r[5], "count": r[6],
        }
        result = litellm_chat_completion_sync(
            [
                {"role": "system", "content": _TRIAGE_SYSTEM_PROMPT},
                {"role": "user", "content": _build_triage_prompt(ev)},
            ],
            model=model,
            temperature=0.1,
            max_tokens=400,
            feature="error_triage",
            trust_zone="internal",
        )
        if result.get("error") or not result.get("content"):
            # Leave as pending so the next batch retries when the brain is back.
            logger.debug("error_monitor: triage deferred for id=%s (%s)", ev["id"], result.get("error"))
            continue
        summary = result["content"][:5000]
        now = datetime.now(timezone.utc)
        try:
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                        UPDATE error_events
                        SET triage_status = 'triaged',
                            triage_summary = :summary,
                            triage_model = :model,
                            triaged_at = :now
                        WHERE id = :id
                        """
                    ),
                    {"summary": summary, "model": f"litellm/{model}", "now": now, "id": ev["id"]},
                )
                conn.commit()
            triaged += 1
        except Exception as e:
            logger.debug("error_monitor: could not write triage for id=%s: %s", ev["id"], e)

    if triaged:
        logger.info("error_monitor: triaged %d error(s) via %s", triaged, model)
    return triaged


# ---------------------------------------------------------------------------
# Background loop (started/stopped by the API lifespan)
# ---------------------------------------------------------------------------

_stop_event: Optional["threading.Event"] = None


async def background_triage_loop(stop_event: "threading.Event") -> None:
    """Async loop that periodically runs triage off the event loop."""
    import asyncio

    interval = triage_interval_seconds()
    logger.info(
        "error_monitor: background triage loop started (interval=%ss, batch=%s)",
        interval, triage_batch_size(),
    )
    # Small initial delay so startup isn't competing with the first batch.
    try:
        await asyncio.sleep(min(30, interval))
    except asyncio.CancelledError:
        return
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(run_triage_batch)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug("error_monitor: triage batch error: %s", e)
        # Sleep in short slices so cancellation/stop is responsive.
        slept = 0
        while slept < interval and not stop_event.is_set():
            try:
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                return
            slept += 5
    logger.info("error_monitor: background triage loop stopped")


# ---------------------------------------------------------------------------
# Read helpers for the admin AI Monitor
# ---------------------------------------------------------------------------

def recent_errors(limit: int = 50) -> List[Dict[str, Any]]:
    engine = _engine()
    if engine is None:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT id, created_at, error_type, error_message, path, method,
                           request_id, count, first_seen, last_seen,
                           triage_status, triage_summary, triage_model, triaged_at
                    FROM error_events
                    ORDER BY last_seen DESC
                    LIMIT :lim
                    """
                ),
                {"lim": max(1, min(limit, 500))},
            ).fetchall()
        return [
            {
                "id": r[0],
                "created_at": str(r[1]) if r[1] else None,
                "error_type": r[2],
                "error_message": r[3],
                "path": r[4],
                "method": r[5],
                "request_id": r[6],
                "count": r[7],
                "first_seen": str(r[8]) if r[8] else None,
                "last_seen": str(r[9]) if r[9] else None,
                "triage_status": r[10],
                "triage_summary": r[11],
                "triage_model": r[12],
                "triaged_at": str(r[13]) if r[13] else None,
            }
            for r in rows
        ]
    except Exception as e:
        logger.debug("error_monitor.recent_errors failed: %s", e)
        return []


def error_summary() -> Dict[str, Any]:
    engine = _engine()
    if engine is None:
        return {"total": 0, "pending": 0, "triaged": 0}
    try:
        with engine.connect() as conn:
            total = conn.execute(text("SELECT COALESCE(SUM(count),0), COUNT(*) FROM error_events")).fetchone()
            pending = conn.execute(
                text("SELECT COUNT(*) FROM error_events WHERE triage_status = 'pending'")
            ).fetchone()
            triaged = conn.execute(
                text("SELECT COUNT(*) FROM error_events WHERE triage_status = 'triaged'")
            ).fetchone()
        return {
            "total_occurrences": int(total[0]) if total else 0,
            "distinct_errors": int(total[1]) if total else 0,
            "pending": int(pending[0]) if pending else 0,
            "triaged": int(triaged[0]) if triaged else 0,
        }
    except Exception as e:
        logger.debug("error_monitor.error_summary failed: %s", e)
        return {"total_occurrences": 0, "distinct_errors": 0, "pending": 0, "triaged": 0}
