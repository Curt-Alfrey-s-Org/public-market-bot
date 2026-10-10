"""
Prometheus metrics endpoint for Market Pie5 Bot API.
"""

import logging
import os

from fastapi import APIRouter
from fastapi.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["metrics"])

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Histogram,
        REGISTRY,
        generate_latest,
    )
    from prometheus_client.multiprocess import MultiProcessCollector

    prometheus_multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")

    if prometheus_multiproc_dir:
        registry = CollectorRegistry()
        MultiProcessCollector(registry)
    else:
        registry = REGISTRY

    http_requests_total = Counter(
        "http_requests_total",
        "Total number of HTTP requests",
        ["method", "endpoint", "status"],
    )

    http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "endpoint"],
        buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    )

    http_request_size_bytes = Histogram(
        "http_request_size_bytes",
        "HTTP request size in bytes",
        ["method", "endpoint"],
        buckets=[100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000],
    )

    http_response_size_bytes = Histogram(
        "http_response_size_bytes",
        "HTTP response size in bytes",
        ["method", "endpoint"],
        buckets=[100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000],
    )

    PROMETHEUS_AVAILABLE = True

except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not installed. Install with: pip install prometheus-client")
    http_requests_total = None
    http_request_duration_seconds = None
    http_request_size_bytes = None
    http_response_size_bytes = None
    registry = None


@router.get("/metrics")
async def metrics():
    """Prometheus scrape endpoint (text format)."""
    if not PROMETHEUS_AVAILABLE or registry is None:
        return Response(
            content="Prometheus client not available. Install with: pip install prometheus-client",
            status_code=503,
            media_type="text/plain",
        )

    try:
        output = generate_latest(registry)
        return Response(content=output, media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error("Error generating Prometheus metrics: %s", e)
        return Response(
            content=f"Error generating metrics: {str(e)}",
            status_code=500,
            media_type="text/plain",
        )
