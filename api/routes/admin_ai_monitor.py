"""
Admin AI Monitor API.

Admin-only endpoints that surface:
- ALFa AI / LiteLLM call telemetry (ollama_activity_log)
- Captured runtime errors and their alfa-ai triage results (error_events)
- On-demand triage trigger

All routes require the `admin` role (api.auth.require_admin).
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from api.auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter()


def _engine():
    try:
        from database import engine
        return engine
    except Exception:
        return None


@router.get("/summary")
def ai_monitor_summary(_: dict = Depends(require_admin)) -> Dict[str, Any]:
    """Counts for the AI Monitor dashboard header."""
    from api.services.error_monitor import error_summary

    engine = _engine()
    activity: Dict[str, Any] = {"total_calls": 0, "errors": 0}
    if engine is not None:
        try:
            with engine.connect() as conn:
                total = conn.execute(text("SELECT COUNT(*) FROM ollama_activity_log")).fetchone()
                errs = conn.execute(
                    text("SELECT COUNT(*) FROM ollama_activity_log WHERE status = 'error'")
                ).fetchone()
            activity = {
                "total_calls": int(total[0]) if total else 0,
                "errors": int(errs[0]) if errs else 0,
            }
        except Exception as e:
            logger.debug("ai_monitor_summary activity query failed: %s", e)

    return {"llm_activity": activity, "errors": error_summary()}


@router.get("/activity")
def ai_monitor_activity(limit: int = 50, _: dict = Depends(require_admin)) -> List[Dict[str, Any]]:
    """Recent LiteLLM/Ollama calls (most recent first)."""
    engine = _engine()
    if engine is None:
        return []
    limit = max(1, min(limit, 500))
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT id, created_at, feature, model, prompt_summary,
                           duration_seconds, eval_tokens, prompt_tokens, status, error_message
                    FROM ollama_activity_log
                    ORDER BY created_at DESC
                    LIMIT :lim
                    """
                ),
                {"lim": limit},
            ).fetchall()
        return [
            {
                "id": r[0],
                "created_at": str(r[1]) if r[1] else None,
                "feature": r[2],
                "model": r[3],
                "prompt_summary": r[4],
                "duration_seconds": r[5],
                "eval_tokens": r[6],
                "prompt_tokens": r[7],
                "status": r[8],
                "error_message": r[9],
            }
            for r in rows
        ]
    except Exception as e:
        logger.debug("ai_monitor_activity failed: %s", e)
        return []


@router.get("/errors")
def ai_monitor_errors(limit: int = 50, _: dict = Depends(require_admin)) -> List[Dict[str, Any]]:
    """Recent captured runtime errors with triage results (most recent first)."""
    from api.services.error_monitor import recent_errors

    return recent_errors(limit=limit)


@router.post("/errors/triage")
def ai_monitor_trigger_triage(limit: int = 10, _: dict = Depends(require_admin)) -> Dict[str, Any]:
    """On-demand: triage pending errors now via the ALFa AI brain."""
    from api.services.error_monitor import run_triage_batch

    try:
        count = run_triage_batch(limit=max(1, min(limit, 50)))
        return {"status": "ok", "triaged": count}
    except Exception as e:
        logger.warning("On-demand triage failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Triage failed: {str(e)[:200]}")
