"""Health check API routes."""

import logging
from pathlib import Path

from fastapi import APIRouter

from api.services.health_check import get_basic_health, run_health_checks
from api.startup import get_startup_status

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SERVICE_NAME = "Market Pie5 Bot API"
VERSION = "1.0.0"


def _get_engine():
    try:
        from database import engine
        return engine
    except ImportError:
        return None


async def _check_litellm() -> dict:
    """Probe the ALFa AI LiteLLM brain so monitoring catches an unreachable brain.

    Returns a dict with status (healthy/degraded/unreachable/disabled) and the
    base_url. Never raises; the trading bot must keep serving when AI is down.
    """
    try:
        from api.services.litellm_client import (
            get_litellm_base_url,
            is_litellm_enabled,
            litellm_model_for_trust_zone,
            LiteLLMClient,
        )

        if not is_litellm_enabled():
            return {
                "status": "disabled",
                "base_url": get_litellm_base_url(),
                "enabled": False,
            }
        client = LiteLLMClient()
        result = await client.health()
        await client.close()
        result["enabled"] = True
        result["model_chat"] = litellm_model_for_trust_zone("app_authenticated")
        return result
    except Exception as e:
        logger.warning("LiteLLM health probe failed: %s", e)
        return {"status": "unreachable", "error": str(e)[:200], "enabled": True}


@router.get("/health")
async def health_basic():
    """Basic probe for load balancers; avoid 5xx on transient failures."""
    try:
        health_data = get_basic_health(SERVICE_NAME, VERSION)
        health_data["startup_status"] = get_startup_status()
        return health_data
    except Exception as e:
        logger.warning("Health basic failed, returning degraded: %s", e)
        try:
            startup_status = get_startup_status()
        except Exception:
            startup_status = None
        return {
            "status": "degraded",
            "service": SERVICE_NAME,
            "version": VERSION,
            "uptime_seconds": None,
            "startup_status": startup_status,
            "error": str(e)[:200],
        }


@router.get("/health/detailed")
async def health_detailed():
    try:
        engine = _get_engine()
        health_data = run_health_checks(
            service_name=SERVICE_NAME,
            version=VERSION,
            engine=engine,
            session_factory=None,
            log_path=PROJECT_ROOT / "trading_bot.log",
        )
        health_data["startup_status"] = get_startup_status()
        health_data["litellm"] = await _check_litellm()
        return health_data
    except Exception as e:
        logger.warning("Health detailed failed: %s", e)
        try:
            startup_status = get_startup_status()
        except Exception:
            startup_status = None
        return {
            "status": "unhealthy",
            "service": SERVICE_NAME,
            "version": VERSION,
            "startup_status": startup_status,
            "error": str(e)[:200],
        }
