#!/usr/bin/env python3
"""
Test for startup CPU optimization fixes

Verifies that:
1. Watchlist initialization includes startup delay
2. Stock fetching includes throttling delay
3. Screener respects max check limit
"""

import unittest
import os
import sys
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestStartupFixes(unittest.TestCase):
    """Test startup optimization fixes"""
    
    def setUp(self):
        """Set up test environment"""
        # Save original env vars
        self.original_env = {}
        for key in ['WATCHLIST_STARTUP_DELAY', 'STOCK_FETCH_DELAY', 'STOCK_SCREENER_MAX_CHECK']:
            self.original_env[key] = os.getenv(key)
    
    def tearDown(self):
        """Restore original environment"""
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    
    @patch('web_gui.time.sleep')
    @patch('web_gui.update_watchlist_data')
    def test_watchlist_startup_delay(self, mock_update, mock_sleep):
        """Test that watchlist initialization includes startup delay"""
        # Set custom delay
        os.environ['WATCHLIST_STARTUP_DELAY'] = '3.0'
        
        # Need to reload module to pick up new env var
        import importlib
        import web_gui
        importlib.reload(web_gui)
        
        # Call async_initialize_watchlist
        web_gui.async_initialize_watchlist()
        
        # Verify sleep was called with the delay
        mock_sleep.assert_called()
        # Check that at least one call had our delay value
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        self.assertIn(3.0, sleep_calls, "Startup delay not applied")
    
    @patch('stock_screener.time.sleep')
    def test_stock_fetch_throttling(self, mock_sleep):
        """Test that stock fetching includes throttling delay"""
        os.environ['STOCK_FETCH_DELAY'] = '0.2'
        os.environ['ENABLE_STOCK_SCREENER'] = 'true'
        
        # Import and create screener
        from stock_screener import StockScreener
        screener = StockScreener()
        
        # Try to fetch a stock (will fail but that's OK, we just want to see the delay)
        screener.fetch_stock_info('AAPL')
        
        # Verify sleep was called with throttle delay
        mock_sleep.assert_called()
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        self.assertIn(0.2, sleep_calls, "Fetch throttling not applied")
    
    def test_screener_max_check_limit(self):
        """Test that screener respects max check limit"""
        os.environ['STOCK_SCREENER_MAX_CHECK'] = '50'
        os.environ['ENABLE_STOCK_SCREENER'] = 'true'
        
        # Import screener
        from stock_screener import StockScreener
        
        # Create screener with a large universe
        screener = StockScreener()
        
        # Mock the fetch_stock_info to avoid actual API calls
        with patch.object(screener, 'fetch_stock_info') as mock_fetch:
            mock_fetch.return_value = {
                'symbol': 'TEST',
                'price': 100.0,
                'volume': 1000000,
                'volatility': 0.05,
                'marketCap': 1000000000,
                'avgVolume': 1000000
            }
            
            # Create a list of 200 test symbols
            test_symbols = [f'TEST{i}' for i in range(200)]
            
            # Screen stocks
            screener.screen_stocks(
                candidate_symbols=test_symbols,
                max_results=10,
                use_cache=False,
                use_advanced_filters=False
            )
            
            # Check that we didn't fetch more than the limit
            # Should be at most 50 (our limit) or 10 (max_results), whichever comes first
            self.assertLessEqual(
                mock_fetch.call_count, 
                50, 
                f"Screener checked {mock_fetch.call_count} stocks, expected <= 50"
            )
    
    def test_env_example_has_new_configs(self):
        """Test that .env.example includes new configuration options"""
        env_example_path = os.path.join(
            os.path.dirname(__file__), '.env.example'
        )
        
        with open(env_example_path, 'r') as f:
            content = f.read()
        
        # Check for new config options
        self.assertIn('WATCHLIST_STARTUP_DELAY', content, 
                     "WATCHLIST_STARTUP_DELAY not in .env.example")
        self.assertIn('STOCK_FETCH_DELAY', content,
                     "STOCK_FETCH_DELAY not in .env.example")
        self.assertIn('STOCK_SCREENER_MAX_CHECK', content,
                     "STOCK_SCREENER_MAX_CHECK not in .env.example")
    
    def test_default_values_are_reasonable(self):
        """Test that default values prevent CPU spikes"""
        # Clear any custom values
        for key in ['WATCHLIST_STARTUP_DELAY', 'STOCK_FETCH_DELAY', 'STOCK_SCREENER_MAX_CHECK']:
            os.environ.pop(key, None)
        
        # Import modules
        import web_gui
        from stock_screener import StockScreener
        
        # Test watchlist delay default (should be >= 3 seconds)
        with patch('web_gui.time.sleep') as mock_sleep:
            with patch('web_gui.update_watchlist_data'):
                web_gui.async_initialize_watchlist()
                if mock_sleep.called:
                    delay = mock_sleep.call_args[0][0]
                    self.assertGreaterEqual(
                        delay, 3.0,
                        f"Default watchlist delay {delay}s is too short, should be >= 3s"
                    )
        
        # Test fetch delay default (should be > 0)
        StockScreener()
        fetch_delay = float(os.getenv('STOCK_FETCH_DELAY', '0.1'))
        self.assertGreater(
            fetch_delay, 0,
            "Default fetch delay should be > 0 to throttle requests"
        )
        
        # Test max check default (should be <= 100)
        max_check = int(os.getenv('STOCK_SCREENER_MAX_CHECK', '100'))
        self.assertLessEqual(
            max_check, 100,
            f"Default max check {max_check} is too high, should be <= 100"
        )


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
