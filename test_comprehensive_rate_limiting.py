#!/usr/bin/env python3
"""
Comprehensive Rate Limiting Test
Verifies rate limiting works for all APIs
"""

import unittest
import time
import os

# Set test environment variables before importing modules
os.environ['ALPHA_VANTAGE_MAX_CALLS_PER_MINUTE'] = '3'
os.environ['ALPHA_VANTAGE_TIME_WINDOW_SECONDS'] = '10'
os.environ['YFINANCE_MAX_CALLS_PER_MINUTE'] = '3'
os.environ['YFINANCE_TIME_WINDOW_SECONDS'] = '10'

# Try to import the shared rate_limiter module
try:
    from rate_limiter import RateLimiter
    RATE_LIMITER_AVAILABLE = True
except ImportError:
    RATE_LIMITER_AVAILABLE = False
    print("Warning: rate_limiter not available - skipping rate limiter tests")

# Try to import the modules for integration tests
try:
    from data_fetcher import DataFetcher
    DATA_FETCHER_AVAILABLE = True
except ImportError:
    DATA_FETCHER_AVAILABLE = False
    print("Warning: data_fetcher not available - skipping data_fetcher tests")


class TestRateLimiterCore(unittest.TestCase):
    """Test core RateLimiter functionality"""
    
    def test_rate_limiter_initialization(self):
        """Test RateLimiter can be initialized"""
        if not RATE_LIMITER_AVAILABLE:
            self.skipTest("rate_limiter not available")
        
        limiter = RateLimiter(max_calls=5, time_window=60, name="Test API")
        self.assertEqual(limiter.max_calls, 5)
        self.assertEqual(limiter.time_window, 60)
        self.assertEqual(limiter.name, "Test API")
    
    def test_can_make_call_when_under_limit(self):
        """Test that calls are allowed when under limit"""
        if not RATE_LIMITER_AVAILABLE:
            self.skipTest("rate_limiter not available")
        
        limiter = RateLimiter(max_calls=3, time_window=10, name="Test API")
        
        # Should be able to make 3 calls
        self.assertTrue(limiter.can_make_call())
        limiter.record_call()
        
        self.assertTrue(limiter.can_make_call())
        limiter.record_call()
        
        self.assertTrue(limiter.can_make_call())
        limiter.record_call()
    
    def test_cannot_make_call_when_at_limit(self):
        """Test that calls are blocked when at limit"""
        if not RATE_LIMITER_AVAILABLE:
            self.skipTest("rate_limiter not available")
        
        limiter = RateLimiter(max_calls=3, time_window=10, name="Test API")
        
        # Make 3 calls (at limit)
        for _ in range(3):
            self.assertTrue(limiter.can_make_call())
            limiter.record_call()
        
        # 4th call should be blocked
        self.assertFalse(limiter.can_make_call())
    
    def test_get_remaining_calls(self):
        """Test remaining calls calculation"""
        if not RATE_LIMITER_AVAILABLE:
            self.skipTest("rate_limiter not available")
        
        limiter = RateLimiter(max_calls=5, time_window=60, name="Test API")
        
        self.assertEqual(limiter.get_remaining_calls(), 5)
        
        limiter.record_call()
        self.assertEqual(limiter.get_remaining_calls(), 4)
        
        limiter.record_call()
        self.assertEqual(limiter.get_remaining_calls(), 3)
    
    def test_wait_time_calculation(self):
        """Test wait time calculation when at limit"""
        if not RATE_LIMITER_AVAILABLE:
            self.skipTest("rate_limiter not available")
        
        limiter = RateLimiter(max_calls=2, time_window=10, name="Test API")
        
        # Should have no wait time initially
        self.assertEqual(limiter.get_wait_time(), 0.0)
        
        # Make 2 calls
        limiter.record_call()
        limiter.record_call()
        
        # Should have wait time now
        wait_time = limiter.get_wait_time()
        self.assertGreater(wait_time, 0)
        self.assertLessEqual(wait_time, 10)
    
    def test_old_calls_cleaned_up(self):
        """Test that old calls are cleaned up after time window"""
        if not RATE_LIMITER_AVAILABLE:
            self.skipTest("rate_limiter not available")
        
        limiter = RateLimiter(max_calls=2, time_window=1, name="Test API")
        
        # Make 2 calls (at limit)
        limiter.record_call()
        limiter.record_call()
        
        # Should be at limit
        self.assertFalse(limiter.can_make_call())
        
        # Wait for time window to pass
        time.sleep(1.1)
        
        # Should be able to make calls again
        self.assertTrue(limiter.can_make_call())


class TestRateLimiterIntegration(unittest.TestCase):
    """Test rate limiting integration with actual modules"""
    
    def test_data_fetcher_has_rate_limiters(self):
        """Test that DataFetcher initializes rate limiters"""
        if not DATA_FETCHER_AVAILABLE:
            self.skipTest("data_fetcher not available")
        
        if not RATE_LIMITER_AVAILABLE:
            self.skipTest("rate_limiter not available")
        
        fetcher = DataFetcher()
        
        # Check that rate limiters exist
        self.assertTrue(hasattr(fetcher, 'alpha_vantage_limiter'))
        self.assertTrue(hasattr(fetcher, 'yfinance_limiter'))
        
        # Check that they're RateLimiter instances
        self.assertIsInstance(fetcher.alpha_vantage_limiter, RateLimiter)
        self.assertIsInstance(fetcher.yfinance_limiter, RateLimiter)
    
    def test_ml_optimizer_no_huggingface_rate_limiter(self):
        """HuggingFace was removed; the optimizer no longer carries an HF rate limiter.

        LLM inference now goes through the ALFa AI brain (LiteLLM), which owns its
        own concurrency/timeout behavior, so MLParameterOptimizer must not define
        ``hf_api_limiter`` anymore.
        """
        try:
            from ml_param_optimizer import MLParameterOptimizer

            optimizer = MLParameterOptimizer()

            # HuggingFace rate limiter must be gone after the alfa-ai migration
            self.assertFalse(hasattr(optimizer, 'hf_api_limiter'))

        except ImportError as e:
            self.skipTest(f"MLParameterOptimizer not available: {e}")
    
    def test_async_data_fetcher_has_rate_limiters(self):
        """Test that AsyncDataFetcher initializes rate limiters"""
        if not RATE_LIMITER_AVAILABLE:
            self.skipTest("rate_limiter not available")
        
        try:
            from async_data_fetcher import AsyncDataFetcher
            
            fetcher = AsyncDataFetcher()
            
            # Check that rate limiters exist
            self.assertTrue(hasattr(fetcher, 'alpha_vantage_limiter'))
            self.assertTrue(hasattr(fetcher, 'yfinance_limiter'))
            
            # Check that they're RateLimiter instances
            self.assertIsInstance(fetcher.alpha_vantage_limiter, RateLimiter)
            self.assertIsInstance(fetcher.yfinance_limiter, RateLimiter)
            
        except ImportError as e:
            self.skipTest(f"AsyncDataFetcher not available: {e}")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
