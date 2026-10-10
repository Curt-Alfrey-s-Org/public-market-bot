"""
Health check service: Database, Redis, API probes.
"""

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_startup_time: Optional[float] = None


def set_startup_time(t: float) -> None:
    global _startup_time
    _startup_time = t


def get_uptime_seconds() -> Optional[float]:
    if _startup_time is None:
        return None
    return time.time() - _startup_time


def check_database(engine=None, session_factory=None) -> Dict[str, Any]:
    result: Dict[str, Any] = {"status": "unknown", "latency_ms": None, "error": None}
    try:
        from sqlalchemy import text

        start = time.perf_counter()
        if engine is not None:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        elif session_factory is not None:
            session = session_factory()
            try:
                session.execute(text("SELECT 1"))
            finally:
                session.close()
        else:
            result["error"] = "No database configured"
            result["status"] = "skipped"
            return result
        elapsed_ms = (time.perf_counter() - start) * 1000
        result["latency_ms"] = round(elapsed_ms, 2)
        result["status"] = "healthy" if elapsed_ms < 5000 else "degraded"
    except Exception as e:
        result["status"] = "unhealthy"
        result["error"] = str(e)[:200]
        logger.warning("Database health check failed: %s", e)
    return result


def check_redis() -> Dict[str, Any]:
    import os

    redis_url = os.getenv("REDIS_URL", "").strip()
    result: Dict[str, Any] = {"configured": bool(redis_url), "status": "unknown", "latency_ms": None, "error": None}
    if not redis_url:
        result["status"] = "not_configured"
        return result
    try:
        import redis

        r = redis.from_url(redis_url)
        start = time.perf_counter()
        r.ping()
        elapsed_ms = (time.perf_counter() - start) * 1000
        result["latency_ms"] = round(elapsed_ms, 2)
        result["status"] = "healthy"
    except ImportError:
        result["status"] = "not_available"
        result["error"] = "redis package not installed"
    except Exception as e:
        result["status"] = "unhealthy"
        result["error"] = str(e)[:200]
        logger.warning("Redis health check failed: %s", e)
    return result


def get_error_log_tail(log_path: Optional[Path], lines: int = 20) -> list:
    if not log_path or not log_path.exists():
        return []
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
        error_lines = [ln.strip() for ln in all_lines if "ERROR" in ln.upper() or "CRITICAL" in ln.upper()]
        return error_lines[-lines:]
    except Exception as e:
        logger.warning("Could not read log file %s: %s", log_path, e)
        return []


def run_health_checks(
    service_name: str,
    version: str = "1.0.0",
    engine=None,
    session_factory=None,
    log_path: Optional[Path] = None,
) -> Dict[str, Any]:
    db_result = check_database(engine=engine, session_factory=session_factory)
    redis_result = check_redis()
    uptime = get_uptime_seconds()
    overall = "healthy"
    if db_result.get("status") == "unhealthy" or redis_result.get("status") == "unhealthy":
        overall = "unhealthy"
    elif db_result.get("status") == "degraded" or redis_result.get("status") == "degraded":
        overall = "degraded"
    return {
        "status": overall,
        "service": service_name,
        "version": version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(uptime, 1) if uptime is not None else None,
        "database": db_result,
        "redis": redis_result,
        "error_logs": get_error_log_tail(log_path) if log_path else [],
    }


def get_basic_health(service_name: str, version: str = "1.0.0") -> Dict[str, Any]:
    uptime = get_uptime_seconds()
    return {
        "status": "healthy",
        "service": service_name,
        "version": version,
        "uptime_seconds": round(uptime, 1) if uptime is not None else None,
    }
