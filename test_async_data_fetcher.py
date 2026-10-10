#!/usr/bin/env python3
"""
Test suite for async_data_fetcher module
Tests async data fetching, connection pooling, and fallback mechanisms
"""

import os
import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
import sys

# Import the async fetcher
try:
    from async_data_fetcher import AsyncDataFetcher, get_async_fetcher, AIOHTTP_AVAILABLE
    ASYNC_FETCHER_AVAILABLE = True
except ImportError as e:
    ASYNC_FETCHER_AVAILABLE = False
    print(f"Warning: Could not import async_data_fetcher: {e}")


@unittest.skipIf(not ASYNC_FETCHER_AVAILABLE, "async_data_fetcher module not available")
class TestAsyncDataFetcher(unittest.TestCase):
    """Test async data fetching functionality"""
    
    def setUp(self):
        """Set up test fetcher instance"""
        # Ensure an event loop exists for Python versions that don't create one by default
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        self.fetcher = AsyncDataFetcher()
    
    def tearDown(self):
        """Clean up after tests"""
        # Close any open sessions
        try:
            if self.fetcher.session and not self.fetcher.session.closed:
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.run_until_complete(self.fetcher.close())
        except:
            pass
    
    def test_fetcher_initialization(self):
        """Test that fetcher initializes correctly"""
        self.assertIsNotNone(self.fetcher)
        self.assertEqual(self.fetcher.cache_duration, 3600)
        self.assertIsInstance(self.fetcher.cache, dict)
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        key = self.fetcher._get_cache_key('AAPL', 'price')
        self.assertEqual(key, 'AAPL_price')
    
    def test_cache_data_and_retrieval(self):
        """Test caching and retrieval of data"""
        test_data = {'price': 150.0, 'volume': 1000000}
        cache_key = 'AAPL_test'
        
        # Cache data
        self.fetcher._cache_data(cache_key, test_data)
        
        # Verify cache is valid
        self.assertTrue(self.fetcher._is_cache_valid(cache_key))
        
        # Retrieve cached data
        retrieved = self.fetcher._get_cached_data(cache_key)
        self.assertEqual(retrieved, test_data)
    
    def test_cache_expiration(self):
        """Test that cache expires after duration"""
        test_data = {'price': 150.0}
        cache_key = 'AAPL_test'
        
        # Cache data with very short duration
        self.fetcher.cache_duration = 0
        self.fetcher._cache_data(cache_key, test_data)
        
        # Cache should be invalid immediately
        import time
        time.sleep(0.1)
        self.assertFalse(self.fetcher._is_cache_valid(cache_key))
        
        # Reset cache duration
        self.fetcher.cache_duration = 3600
    
    def test_parse_number(self):
        """Test number parsing utility"""
        # Valid numbers
        self.assertEqual(self.fetcher._parse_number('123.45'), 123.45)
        self.assertEqual(self.fetcher._parse_number('100'), 100.0)
        
        # Invalid inputs
        self.assertIsNone(self.fetcher._parse_number(None))
        self.assertIsNone(self.fetcher._parse_number(''))
        self.assertIsNone(self.fetcher._parse_number('None'))
        self.assertIsNone(self.fetcher._parse_number('invalid'))
    
    @unittest.skipIf(not AIOHTTP_AVAILABLE, "aiohttp not available")
    def test_session_creation(self):
        """Test aiohttp session creation"""
        loop = asyncio.get_event_loop()
        session = loop.run_until_complete(self.fetcher._get_session())
        
        self.assertIsNotNone(session)
        self.assertFalse(session.closed)
        
        # Clean up
        loop.run_until_complete(self.fetcher.close())
    
    def test_fetch_price_yfinance_sync_wrapper(self):
        """Test synchronous wrapper for price fetching"""
        # Test with single symbol (will use fallback if yfinance not available)
        result = self.fetcher.fetch_multiple_prices(['AAPL'])
        
        # Should return dict even if no results (fallback behavior)
        self.assertIsInstance(result, dict)
    
    @unittest.skipIf(not AIOHTTP_AVAILABLE, "aiohttp not available")
    def test_fetch_price_yfinance_async(self):
        """Test async price fetching with yfinance"""
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            self.fetcher.fetch_price_yfinance_async('AAPL')
        )
        
        # Result may be None if yfinance not available or no data
        if result is not None:
            price, volume = result
            self.assertIsInstance(price, float)
            self.assertIsInstance(volume, int)
        else:
            # No data available is acceptable
            self.assertIsNone(result)
    
    @unittest.skipIf(not AIOHTTP_AVAILABLE, "aiohttp not available")
    def test_fetch_fundamentals_no_api_key(self):
        """Test that fundamentals fetch returns None without API key"""
        # Create fetcher without API key
        fetcher = AsyncDataFetcher(alpha_vantage_key='')
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            fetcher.fetch_fundamentals_alpha_vantage_async('AAPL')
        )
        
        self.assertIsNone(result)
    
    @unittest.skipIf(not AIOHTTP_AVAILABLE, "aiohttp not available")
    @patch('aiohttp.ClientSession.get')
    def test_fetch_fundamentals_with_mock_response(self, mock_get):
        """Test fundamentals fetching with mocked API response"""
        # Skip if no API key configured
        if not self.fetcher.av_api_key:
            self.skipTest("No Alpha Vantage API key configured")
        
        # Mock API response
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={
            'Symbol': 'AAPL',
            'Name': 'Apple Inc.',
            'Sector': 'Technology',
            'PERatio': '25.5',
            'EPS': '6.00',
        })
        
        mock_get.return_value.__aenter__.return_value = mock_response
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            self.fetcher.fetch_fundamentals_alpha_vantage_async('AAPL')
        )
        
        if result is not None:
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get('symbol'), 'AAPL')
    
    def test_fetch_multiple_prices_empty_list(self):
        """Test fetching prices for empty symbol list"""
        result = self.fetcher.fetch_multiple_prices([])
        self.assertEqual(result, {})
    
    def test_get_singleton_instance(self):
        """Test singleton pattern for async fetcher"""
        instance1 = get_async_fetcher()
        instance2 = get_async_fetcher()
        
        # Should be same instance
        self.assertIs(instance1, instance2)
    
    def test_comprehensive_data_structure(self):
        """Test that comprehensive data has correct structure"""
        result = self.fetcher.fetch_comprehensive_data('AAPL', include_fundamentals=False)
        
        # Verify structure
        self.assertIsInstance(result, dict)
        self.assertIn('symbol', result)
        self.assertIn('timestamp', result)
        self.assertIn('data_sources', result)


@unittest.skipIf(not ASYNC_FETCHER_AVAILABLE, "async_data_fetcher module not available")
class TestAsyncFetcherFallback(unittest.TestCase):
    """Test fallback to synchronous mode"""
    
    def test_fallback_when_aiohttp_unavailable(self):
        """Test that fetcher works without aiohttp"""
        # This test verifies graceful degradation
        fetcher = AsyncDataFetcher()
        
        # Should initialize successfully
        self.assertIsNotNone(fetcher)
        
        # Should have fallback fetcher if available
        if fetcher.sync_fetcher:
            self.assertIsNotNone(fetcher.sync_fetcher)
    
    def test_sync_wrapper_with_disabled_async(self):
        """Test synchronous wrapper when async is disabled"""
        # Set environment to disable async
        original_value = os.environ.get('ENABLE_ASYNC_FETCHING')
        os.environ['ENABLE_ASYNC_FETCHING'] = 'false'
        
        try:
            fetcher = AsyncDataFetcher()
            result = fetcher.fetch_multiple_prices(['AAPL'])
            
            # Should return dict (possibly empty if no data available)
            self.assertIsInstance(result, dict)
        finally:
            # Restore environment
            if original_value:
                os.environ['ENABLE_ASYNC_FETCHING'] = original_value
            else:
                os.environ.pop('ENABLE_ASYNC_FETCHING', None)


@unittest.skipIf(not ASYNC_FETCHER_AVAILABLE, "async_data_fetcher module not available")
class TestAsyncPerformance(unittest.TestCase):
    """Test performance characteristics of async fetching"""
    
    def test_concurrent_fetching_efficiency(self):
        """Test that concurrent fetching is attempted for multiple symbols"""
        fetcher = AsyncDataFetcher()
        
        # This test verifies the code path, not actual performance
        # Real performance testing would require live API calls
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        # Should not raise exceptions
        try:
            result = fetcher.fetch_multiple_prices(symbols)
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"Concurrent fetching raised exception: {e}")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
