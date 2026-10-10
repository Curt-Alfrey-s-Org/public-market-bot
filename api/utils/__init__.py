"""
API Utilities Package

Provides retry logic, caching, bot instance management, and other utilities for API operations.
"""

import time
from datetime import datetime

from api.utils.retries import (
    with_retry,
    retry_sync,
    retry_on_exception,
    RetryConfig,
)

from api.utils.cache import (
    TTLCache,
    CacheEntry,
    get_cache,
    cache_get,
    cache_set,
    cache_delete,
    cache_clear,
    cache_stats,
)

# ============================================================================
# Bot Instance Management (moved from api/utils.py module)
# ============================================================================

# Global bot instance (will be set when bot starts)
_bot_instance = None

# Startup timing tracking
_startup_timings = {}


def set_bot_instance(bot):
    """Set the global bot instance. Pass None to clear (e.g. on shutdown). Always replace so Restart uses the new bot and Decision Report shows live data."""
    global _bot_instance
    _bot_instance = bot
    return _bot_instance


def get_bot_instance():
    """Get the global bot instance"""
    return _bot_instance


def record_startup_timing(phase: str, duration: float):
    """Record timing for a startup phase"""
    _startup_timings[phase] = {
        'duration_s': duration,
        'duration_ms': duration * 1000,
        'timestamp': datetime.now().isoformat()
    }


def get_startup_timings():
    """Get all recorded startup timings"""
    return _startup_timings.copy()


__all__ = [
    # Retry utilities
    'with_retry',
    'retry_sync',
    'retry_on_exception',
    'RetryConfig',
    # Cache utilities
    'TTLCache',
    'CacheEntry',
    'get_cache',
    'cache_get',
    'cache_set',
    'cache_delete',
    'cache_clear',
    'cache_stats',
    # Bot instance management
    'get_bot_instance',
    'set_bot_instance',
    'record_startup_timing',
    'get_startup_timings',
]
