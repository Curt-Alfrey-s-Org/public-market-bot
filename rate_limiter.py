#!/usr/bin/env python3
"""
Rate Limiter Utility Module for market-pie5-bot

Provides thread-safe rate limiting for API calls to prevent quota exhaustion
and 429 (Rate Limited) errors.
"""

import time
import threading
import logging
from collections import deque

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter to track and enforce API call limits with thread-safety
    
    Uses a sliding window algorithm to track API calls and enforce rate limits.
    Thread-safe for concurrent operations.
    """
    
    def __init__(self, max_calls: int, time_window: int, name: str = "API"):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum number of calls allowed in the time window
            time_window: Time window in seconds
            name: Name of the API for logging purposes
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.name = name
        self.call_times = deque()
        self._lock = threading.Lock()  # Thread safety for concurrent operations
        logger.info(f"Rate limiter for {name}: {max_calls} calls per {time_window}s")
    
    def _clean_old_calls(self):
        """Remove call timestamps outside the time window"""
        current_time = time.time()
        cutoff_time = current_time - self.time_window
        
        while self.call_times and self.call_times[0] < cutoff_time:
            self.call_times.popleft()
    
    def can_make_call(self) -> bool:
        """
        Check if a call can be made without exceeding rate limits
        
        Returns:
            True if call can be made, False otherwise
        """
        with self._lock:
            self._clean_old_calls()
            return len(self.call_times) < self.max_calls
    
    def record_call(self):
        """Record that a call was made"""
        with self._lock:
            self.call_times.append(time.time())
            self._clean_old_calls()
    
    def get_wait_time(self) -> float:
        """
        Get the time to wait before next call is allowed
        
        Returns:
            Seconds to wait, or 0 if call can be made now
        """
        with self._lock:
            self._clean_old_calls()
            
            if len(self.call_times) < self.max_calls:
                return 0.0
            
            # If max_calls is 0, no calls should ever be allowed
            if self.max_calls == 0:
                return float(self.time_window)
            
            # Calculate when the oldest call will expire
            oldest_call = self.call_times[0]
            current_time = time.time()
            wait_time = (oldest_call + self.time_window) - current_time
            
            return max(0.0, wait_time)
    
    def get_remaining_calls(self) -> int:
        """
        Get the number of remaining calls in the current time window
        
        Returns:
            Number of calls that can still be made
        """
        with self._lock:
            self._clean_old_calls()
            return max(0, self.max_calls - len(self.call_times))
