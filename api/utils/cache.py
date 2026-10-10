"""
TTL-based Cache for API Data

Simple in-memory cache with time-to-live (TTL) support.
Used as a fallback when API calls fail after retries.
"""

import time
import logging
from typing import Optional, Dict, Any, Tuple
from threading import Lock

logger = logging.getLogger(__name__)


class CacheEntry:
    """Single cache entry with TTL support."""

    def __init__(self, value: Any, ttl_seconds: float = 300):
        """
        Args:
            value: Cached value
            ttl_seconds: Time-to-live in seconds (default: 300 = 5 minutes)
        """
        self.value = value
        self.timestamp = time.time()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        elapsed = time.time() - self.timestamp
        return elapsed > self.ttl_seconds

    def age_seconds(self) -> float:
        """Get age of this entry in seconds."""
        return time.time() - self.timestamp


class TTLCache:
    """Thread-safe TTL cache for storing API responses."""

    def __init__(self, default_ttl: float = 300):
        """
        Args:
            default_ttl: Default TTL for entries in seconds (default: 300 = 5 minutes)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if entry.is_expired():
                logger.debug(f"Cache miss for {key} (expired after {entry.age_seconds():.1f}s)")
                del self._cache[key]
                return None

            logger.debug(f"Cache hit for {key} (age: {entry.age_seconds():.1f}s)")
            return entry.value

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """
        Store value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL in seconds (uses default_ttl if not specified)
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl)
            logger.debug(f"Cached {key} with TTL={ttl}s")

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if entry was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Deleted cache entry for {key}")
                return True
            return False

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            if count > 0:
                logger.debug(f"Cleared {count} cache entries")
            return count

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            if expired_keys:
                logger.debug(f"Removed {len(expired_keys)} expired cache entries")
            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with entry count, expired count, etc.
        """
        with self._lock:
            expired_count = sum(1 for entry in self._cache.values() if entry.is_expired())
            return {
                "total_entries": len(self._cache),
                "expired_entries": expired_count,
                "active_entries": len(self._cache) - expired_count,
            }


# Global cache instance
_global_cache = TTLCache(default_ttl=300)  # 5 minutes default


def get_cache() -> TTLCache:
    """Get global cache instance."""
    return _global_cache


def cache_get(key: str) -> Optional[Any]:
    """Convenience function to get from global cache."""
    return _global_cache.get(key)


def cache_set(key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
    """Convenience function to set in global cache."""
    _global_cache.set(key, value, ttl_seconds)


def cache_delete(key: str) -> bool:
    """Convenience function to delete from global cache."""
    return _global_cache.delete(key)


def cache_clear() -> int:
    """Convenience function to clear global cache."""
    return _global_cache.clear()


def cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return _global_cache.get_stats()
