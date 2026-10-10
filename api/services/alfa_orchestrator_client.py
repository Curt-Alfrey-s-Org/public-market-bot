"""
Client for the ALFa AI orchestrator (agentic jobs) on the brain (:8420).

Contract (see alfa-ai/src/api/app.py):
    POST /api/runs            {goal: str}        -> {run_id: str}
    GET  /api/runs/{run_id}                      -> {ok, run, tasks, artifacts}
    GET  /health                                 -> {status: "ok", ...}

Auth: Bearer ALFA_AI_API_TOKEN (required when the brain enforces API auth).

Used for factual, multi-step jobs (end-of-day summary, anomaly digest,
sector-rotation report). Trust zone: app_authenticated. Graceful degrade: all
methods return an object with `error` set rather than raising.

Environment:
    ALFA_AI_API_URL    orchestrator base URL (default http://192.0.2.30)
    ALFA_AI_API_TOKEN  bearer token (optional; sent if present)
    ALFA_AI_TIMEOUT    request timeout seconds (default 30)
"""

import logging
import os
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_ORCHESTRATOR_URL = "http://192.0.2.30"


def _get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def get_orchestrator_url() -> str:
    return _get_env("ALFA_AI_API_URL", DEFAULT_ORCHESTRATOR_URL)


def is_orchestrator_enabled() -> bool:
    """Enabled when LiteLLM is on (same brain) unless explicitly disabled."""
    explicit = _get_env("ALFA_ORCHESTRATOR_ENABLED", "").lower()
    if explicit in ("true", "1", "yes"):
        return True
    if explicit in ("false", "0", "no"):
        return False
    return _get_env("LITELLM_ENABLED", "false").lower() in ("true", "1", "yes")


def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    token = _get_env("ALFA_AI_API_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _timeout() -> float:
    try:
        return float(_get_env("ALFA_AI_TIMEOUT", "30"))
    except ValueError:
        return 30.0


async def health() -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{get_orchestrator_url()}/health")
        return {
            "status": "healthy" if resp.status_code == 200 else "degraded",
            "url": get_orchestrator_url(),
        }
    except Exception as e:
        return {"status": "unreachable", "url": get_orchestrator_url(), "error": str(e)[:200]}


async def create_run(goal: str) -> Dict[str, Any]:
    """Submit an agentic job. Returns {run_id} or {error}."""
    if not is_orchestrator_enabled():
        return {"error": "orchestrator_disabled"}
    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            resp = await client.post(
                f"{get_orchestrator_url()}/api/runs",
                headers=_headers(),
                json={"goal": goal},
            )
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}: {resp.text[:300]}"}
        data = resp.json()
        return {"run_id": data.get("run_id")}
    except Exception as e:  # noqa: BLE001
        logger.debug("orchestrator create_run failed: %s", e)
        return {"error": f"{type(e).__name__}: {e}"}


async def get_run(run_id: str) -> Dict[str, Any]:
    """Fetch a run's status, tasks, and artifacts. Returns {error} on failure."""
    if not is_orchestrator_enabled():
        return {"error": "orchestrator_disabled"}
    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            resp = await client.get(
                f"{get_orchestrator_url()}/api/runs/{run_id}",
                headers=_headers(),
            )
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}: {resp.text[:300]}"}
        return resp.json()
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}
