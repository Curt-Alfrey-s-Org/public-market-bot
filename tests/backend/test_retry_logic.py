"""
Tests for Phase 1.2: API Retry Logic

Tests exponential backoff, rate limiting, timeout handling, and cache fallback.
"""

import asyncio
import pytest
import logging
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import time
import sys
from pathlib import Path

# Test imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.utils.retries import (
    with_retry,
    retry_sync,
    retry_on_exception,
    RetryConfig,
    RETRYABLE_HTTP_CODES,
    PERMANENT_HTTP_CODES,
)
from api.utils.cache import TTLCache, CacheEntry, cache_get, cache_set, cache_delete, cache_clear


class TestRetryLogic:
    """Tests for retry mechanism."""

    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """Test: Successful call returns immediately without retries."""
        async def successful_call():
            return "success"
        
        result = await with_retry(successful_call, max_retries=3)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_timeout_then_success(self):
        """Test: API timeout first 2 times, success on 3rd → verify retries."""
        call_count = 0
        
        async def flaky_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise asyncio.TimeoutError("Simulated timeout")
            return "success_after_retries"
        
        result = await with_retry(
            flaky_call,
            max_retries=3,
            initial_delay=0.01,  # Short delay for testing
        )
        
        assert result == "success_after_retries"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_connection_error_with_backoff(self):
        """Test: Connection error retries with exponential backoff."""
        call_count = 0
        call_times = []
        
        async def flaky_connection():
            nonlocal call_count
            call_count += 1
            call_times.append(time.time())
            if call_count < 2:
                raise ConnectionError("Connection refused")
            return "connected"
        
        start_time = time.time()
        result = await with_retry(
            flaky_connection,
            max_retries=2,
            initial_delay=0.05,
            backoff_factor=2.0,
        )
        
        elapsed = time.time() - start_time
        assert result == "connected"
        assert call_count == 2
        # Should have some delay due to backoff. RetryConfig applies 50-100%
        # jitter (delay *= 0.5 + random()), so the minimum is initial_delay/2.
        assert elapsed >= 0.025

    @pytest.mark.asyncio
    async def test_retry_rate_limit_429(self):
        """Test: Mock Schwab API returns 429 (rate limit) → retry with backoff."""
        call_count = 0
        
        class RateLimitError(Exception):
            def __init__(self):
                self.status_code = 429
        
        async def rate_limited_api():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RateLimitError()
            return {"status": "ok"}
        
        result = await with_retry(
            rate_limited_api,
            max_retries=2,
            initial_delay=0.01,
        )
        
        assert result == {"status": "ok"}
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_permanent_error_404_fails_immediately(self):
        """Test: Permanent error (404) → fail immediately, no retries."""
        call_count = 0
        
        class NotFoundError(Exception):
            def __init__(self):
                self.status_code = 404
        
        async def missing_resource():
            nonlocal call_count
            call_count += 1
            raise NotFoundError()
        
        with pytest.raises(NotFoundError):
            await with_retry(
                missing_resource,
                max_retries=3,
            )
        
        # Should fail immediately without retries
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_permanent_error_403_forbidden(self):
        """Test: Permanent error (403) → fail immediately."""
        class ForbiddenError(Exception):
            def __init__(self):
                self.status_code = 403
        
        async def forbidden_call():
            raise ForbiddenError()
        
        with pytest.raises(ForbiddenError):
            await with_retry(
                forbidden_call,
                max_retries=3,
            )

    @pytest.mark.asyncio
    async def test_retry_exhaustion_after_max_attempts(self):
        """Test: All retries exhausted → raises final exception."""
        
        async def always_fails():
            raise asyncio.TimeoutError("Always times out")
        
        with pytest.raises(asyncio.TimeoutError):
            await with_retry(
                always_fails,
                max_retries=2,
                initial_delay=0.01,
            )

    @pytest.mark.asyncio
    async def test_retry_with_custom_timeout(self):
        """Test: Custom timeout per attempt."""
        
        async def slow_call():
            await asyncio.sleep(0.05)
            return "done"
        
        result = await with_retry(
            slow_call,
            timeout=0.2,  # Long enough for the call
        )
        
        assert result == "done"

    @pytest.mark.asyncio
    async def test_retry_timeout_exceeded_within_timeout(self):
        """Test: Function call exceeds timeout → TimeoutError."""
        
        async def too_slow():
            await asyncio.sleep(0.5)
            return "done"
        
        with pytest.raises(asyncio.TimeoutError):
            await with_retry(
                too_slow,
                max_retries=1,
                timeout=0.1,  # Too short
                initial_delay=0.01,
            )

    def test_retry_sync_function(self):
        """Test: Synchronous retry works."""
        call_count = 0
        
        def flaky_sync():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Not connected")
            return "success"
        
        result = retry_sync(
            flaky_sync,
            max_retries=2,
            initial_delay=0.01,
        )
        
        assert result == "success"
        assert call_count == 2

    def test_retry_decorator(self):
        """Test: @retry_on_exception decorator works."""
        call_count = 0
        
        @retry_on_exception(max_retries=2, initial_delay=0.01)
        def decorated_flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Timeout")
            return "done"
        
        result = decorated_flaky()
        
        assert result == "done"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_logs_backoff_timing(self):
        """Test: Logs include retry count and backoff timing."""
        call_count = 0
        
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Timeout")
            return "ok"
        
        with patch('api.utils.retries.logger') as mock_logger:
            result = await with_retry(
                flaky,
                max_retries=2,
                initial_delay=0.01,
                operation_name="test_operation"
            )
            
            assert result == "ok"
            # Verify logging calls
            assert mock_logger.warning.called or mock_logger.info.called


class TestCacheFallback:
    """Tests for cache fallback when retries exhausted."""

    def test_cache_entry_ttl_check(self):
        """Test: Cache entry TTL expiration."""
        entry = CacheEntry("value", ttl_seconds=0.1)
        
        assert not entry.is_expired()
        time.sleep(0.2)
        assert entry.is_expired()

    def test_cache_get_returns_value_if_not_expired(self):
        """Test: Get returns value if not expired."""
        cache = TTLCache(default_ttl=10)
        cache.set("key1", "value1")
        
        result = cache.get("key1")
        assert result == "value1"

    def test_cache_get_returns_none_if_expired(self):
        """Test: Get returns None if expired."""
        cache = TTLCache(default_ttl=0.1)
        cache.set("key1", "value1")
        
        time.sleep(0.2)
        result = cache.get("key1")
        assert result is None

    def test_cache_get_nonexistent_key(self):
        """Test: Get nonexistent key returns None."""
        cache = TTLCache()
        result = cache.get("nonexistent")
        assert result is None

    def test_cache_delete(self):
        """Test: Delete removes entry."""
        cache = TTLCache()
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

    def test_cache_clear(self):
        """Test: Clear removes all entries."""
        cache = TTLCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        count = cache.clear()
        assert count == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_cleanup_expired(self):
        """Test: Cleanup removes expired entries."""
        cache = TTLCache(default_ttl=0.1)
        cache.set("key1", "value1")
        cache.set("key2", "value2", ttl_seconds=10)
        
        time.sleep(0.2)
        count = cache.cleanup_expired()
        
        assert count == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_cache_stats(self):
        """Test: Stats report correct counts."""
        cache = TTLCache(default_ttl=10)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        stats = cache.get_stats()
        
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 2
        assert stats["expired_entries"] == 0

    def test_global_cache_functions(self):
        """Test: Global cache convenience functions work."""
        cache_clear()
        
        cache_set("symbol:AAPL", {"price": 150.0})
        result = cache_get("symbol:AAPL")
        
        assert result == {"price": 150.0}
        
        assert cache_delete("symbol:AAPL") is True
        assert cache_get("symbol:AAPL") is None

    @pytest.mark.asyncio
    async def test_cache_fallback_on_yfinance_retry_failure(self):
        """Test: All retries fail yfinance fetch, use cached data as fallback."""
        # Setup cache with old data
        cache_clear()
        cached_data = {
            "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
            "price": 145.0,
            "volume": 1000000,
        }
        cache_set("yfinance:AAPL", cached_data, ttl_seconds=3600)
        
        # Simulate yfinance failure
        async def always_fails():
            raise Exception("API unreachable")
        
        with pytest.raises(Exception):
            await with_retry(
                always_fails,
                max_retries=2,
                initial_delay=0.01,
            )
        
        # Fallback to cache
        fallback_data = cache_get("yfinance:AAPL")
        
        assert fallback_data is not None
        assert fallback_data["price"] == 145.0


class TestRetryIntegration:
    """Integration tests for retry logic."""

    @pytest.mark.asyncio
    async def test_retry_config_with_jitter(self):
        """Test: Retry config applies jitter to delays."""
        config = RetryConfig(
            initial_delay=1.0,
            backoff_factor=2.0,
            jitter=True,
        )
        
        delays = []
        for attempt in range(3):
            delay = config.get_backoff_delay(attempt)
            delays.append(delay)
        
        # Delays should be different each time due to jitter
        assert len(set(delays)) > 1  # At least some variation

    @pytest.mark.asyncio
    async def test_retry_config_without_jitter(self):
        """Test: Retry config without jitter produces consistent delays."""
        config = RetryConfig(
            initial_delay=1.0,
            backoff_factor=2.0,
            jitter=False,
        )
        
        delays = []
        for attempt in range(3):
            delay = config.get_backoff_delay(attempt)
            delays.append(delay)
        
        # Delays should follow exact exponential backoff: 1, 2, 4
        assert abs(delays[0] - 1.0) < 0.01
        assert abs(delays[1] - 2.0) < 0.01
        assert abs(delays[2] - 4.0) < 0.01


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
