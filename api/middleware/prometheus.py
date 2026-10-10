"""
Prometheus HTTP metrics middleware for FastAPI.
"""

import logging
import re
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

try:
    from api.routes.metrics import (
        PROMETHEUS_AVAILABLE,
        http_request_duration_seconds,
        http_request_size_bytes,
        http_requests_total,
        http_response_size_bytes,
    )
except ImportError:
    PROMETHEUS_AVAILABLE = False
    http_requests_total = None
    http_request_duration_seconds = None
    http_request_size_bytes = None
    http_response_size_bytes = None


def _normalize_path(path: str) -> str:
    if "?" in path:
        path = path.split("?")[0]
    path = re.sub(
        r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "/{id}",
        path,
        flags=re.IGNORECASE,
    )
    path = re.sub(r"/\d+", "/{id}", path)
    if len(path) > 100:
        path = path[:100]
    return path


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Record request counts and latency for Prometheus."""

    async def dispatch(self, request: Request, call_next):
        if not PROMETHEUS_AVAILABLE:
            return await call_next(request)

        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        path = _normalize_path(request.url.path)

        request_size = 0
        try:
            content_length = request.headers.get("content-length")
            if content_length:
                request_size = int(content_length)
        except (TypeError, ValueError):
            request_size = 0

        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            response_size = 0
            if hasattr(response, "body"):
                try:
                    response_size = len(response.body)
                except Exception:
                    pass

            status_code = getattr(response, "status_code", 200)
            status_class = f"{status_code // 100}xx"

            try:
                http_requests_total.labels(method=method, endpoint=path, status=status_class).inc()
                http_request_duration_seconds.labels(method=method, endpoint=path).observe(duration)
                if request_size > 0:
                    http_request_size_bytes.labels(method=method, endpoint=path).observe(request_size)
                if response_size > 0:
                    http_response_size_bytes.labels(method=method, endpoint=path).observe(response_size)
            except Exception as e:
                logger.warning("Error recording Prometheus metrics: %s", e)

            return response

        except Exception:
            duration = time.time() - start_time
            status_class = "5xx"
            try:
                http_requests_total.labels(method=method, endpoint=path, status=status_class).inc()
                http_request_duration_seconds.labels(method=method, endpoint=path).observe(duration)
            except Exception:
                pass
            raise
