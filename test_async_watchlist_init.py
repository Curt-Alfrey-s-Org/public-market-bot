#!/usr/bin/env python3
"""
Test suite for asynchronous watchlist initialization
Tests the optimization of startup sequence with background loading
"""

import os
import sys
import unittest
import time
import threading
from unittest.mock import patch

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set test environment
os.environ["ENABLE_TOP_PERFORMERS_WATCHLIST"] = "true"
os.environ["TOP_PERFORMERS_WATCHLIST_SIZE"] = "10"
os.environ["PAPER_TRADING_MODE"] = "true"


class TestAsyncWatchlistInit(unittest.TestCase):
    """Test cases for asynchronous watchlist initialization"""

    def test_async_initialize_watchlist_function_exists(self):
        """Test that async_initialize_watchlist function exists"""
        import web_gui
        
        self.assertTrue(hasattr(web_gui, 'async_initialize_watchlist'))
        self.assertTrue(callable(web_gui.async_initialize_watchlist))

    def test_watchlist_loading_state_variable_exists(self):
        """Test that watchlist_loading state variable exists"""
        import web_gui
        
        self.assertTrue(hasattr(web_gui, 'watchlist_loading'))
        self.assertIsInstance(web_gui.watchlist_loading, bool)

    @patch('web_gui.update_watchlist_data')
    def test_async_initialize_calls_update(self, mock_update):
        """Test that async_initialize_watchlist calls update_watchlist_data"""
        import web_gui
        
        mock_update.return_value = True
        web_gui.watchlist_data = []  # Reset state
        
        web_gui.async_initialize_watchlist()
        
        mock_update.assert_called_once_with(force_refresh=True)

    @patch('web_gui.update_watchlist_data')
    def test_async_initialize_handles_errors(self, mock_update):
        """Test that async_initialize_watchlist handles errors gracefully"""
        import web_gui
        
        mock_update.side_effect = Exception("Test error")
        
        # Should not raise exception
        try:
            web_gui.async_initialize_watchlist()
        except Exception as e:
            self.fail(f"async_initialize_watchlist raised unexpected exception: {e}")

    def test_update_watchlist_sets_loading_flag(self):
        """Test that update_watchlist_data sets and clears loading flag"""
        import web_gui
        
        # Mock the fetch function to simulate work
        original_fetch = web_gui.fetch_watchlist_data
        call_count = [0]
        
        def mock_fetch():
            call_count[0] += 1
            self.assertTrue(web_gui.watchlist_loading, "Loading flag should be True during fetch")
            time.sleep(0.1)  # Simulate some work
            return []
        
        web_gui.fetch_watchlist_data = mock_fetch
        
        try:
            self.assertFalse(web_gui.watchlist_loading, "Loading flag should start False")
            web_gui.update_watchlist_data(force_refresh=True)
            self.assertFalse(web_gui.watchlist_loading, "Loading flag should be False after completion")
            self.assertEqual(call_count[0], 1, "fetch_watchlist_data should be called once")
        finally:
            web_gui.fetch_watchlist_data = original_fetch

    def test_update_watchlist_prevents_concurrent_loads(self):
        """Test that concurrent calls to update_watchlist_data are prevented"""
        import web_gui
        
        # Mock the fetch function to simulate slow work
        original_fetch = web_gui.fetch_watchlist_data
        call_count = [0]
        fetch_started = threading.Event()
        
        def slow_fetch():
            call_count[0] += 1
            fetch_started.set()  # Signal that fetch has started
            time.sleep(0.2)  # Simulate slow work
            return []
        
        web_gui.fetch_watchlist_data = slow_fetch
        
        try:
            # Start first call in background
            thread1 = threading.Thread(target=lambda: web_gui.update_watchlist_data(force_refresh=True))
            thread1.start()
            
            # Wait for fetch to actually start
            fetch_started.wait(timeout=1.0)
            
            # Try second call (should be skipped)
            result = web_gui.update_watchlist_data(force_refresh=True)
            self.assertFalse(result, "Second concurrent call should return False")
            
            # Wait for first call to complete
            thread1.join()
            
            # Only one call should have been made
            self.assertEqual(call_count[0], 1, "Only one fetch should occur despite concurrent calls")
        finally:
            web_gui.fetch_watchlist_data = original_fetch

    def test_format_watchlist_shows_loading_state(self):
        """Test that format_watchlist_table shows loading message when loading"""
        import web_gui
        from dash import html
        
        # Set loading state
        web_gui.watchlist_loading = True
        
        result = web_gui.format_watchlist_table([])
        
        # Should return a div with loading message (not an error message)
        self.assertIsInstance(result, html.Div)
        # Check that result contains loading indicator
        self.assertTrue(any('Loading' in str(child) or '⏳' in str(child) 
                          for child in result.children if hasattr(result, 'children')))

    def test_watchlist_async_init_is_non_blocking(self):
        """Test that async initialization doesn't block"""
        import web_gui
        
        # Mock the fetch to simulate slow operation
        original_fetch = web_gui.fetch_watchlist_data
        
        def slow_fetch():
            time.sleep(0.3)
            return []
        
        web_gui.fetch_watchlist_data = slow_fetch
        
        try:
            start_time = time.time()
            
            # Start async initialization in thread (simulating what happens in main())
            thread = threading.Thread(target=web_gui.async_initialize_watchlist, daemon=True)
            thread.start()
            
            # Check that we can continue immediately (non-blocking)
            elapsed = time.time() - start_time
            self.assertLess(elapsed, 0.1, "Thread start should be non-blocking")
            
            # Wait for completion
            thread.join(timeout=1.0)
        finally:
            web_gui.fetch_watchlist_data = original_fetch


if __name__ == '__main__':
    unittest.main()
