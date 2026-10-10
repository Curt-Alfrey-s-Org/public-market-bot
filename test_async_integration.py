#!/usr/bin/env python3
"""
Integration test for async data fetcher with main.py
Tests that main.py can properly use async fetching
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import pytest

# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')

# Import the bot
try:
    from main import TradingBot, ASYNC_DATA_FETCHER_AVAILABLE
    MAIN_AVAILABLE = True
except ImportError as e:
    MAIN_AVAILABLE = False
    print(f"Warning: Could not import main: {e}")


@pytest.mark.integration
@unittest.skipIf(not MAIN_AVAILABLE, "main module not available")
class TestAsyncIntegration(unittest.TestCase):
    """Test integration of async fetcher with main trading bot"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_async_fetcher_availability(self):
        """Test that async fetcher availability is tracked"""
        # Should have ASYNC_DATA_FETCHER_AVAILABLE constant
        self.assertIsInstance(ASYNC_DATA_FETCHER_AVAILABLE, bool)
        print(f"✓ Async data fetcher available: {ASYNC_DATA_FETCHER_AVAILABLE}")
    
    def test_search_stocks_with_empty_list(self):
        """Test that search_stocks handles empty symbol list"""
        result = self.bot.search_stocks(symbols=[], use_screener=False)
        
        # Should return empty list
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)
        print("✓ search_stocks handles empty list correctly")
    
    @patch('main.get_async_fetcher')
    def test_search_stocks_uses_async_fetcher(self, mock_get_fetcher):
        """Test that search_stocks attempts to use async fetcher when available"""
        if not ASYNC_DATA_FETCHER_AVAILABLE:
            self.skipTest("Async data fetcher not available")
        
        # Mock async fetcher
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_multiple_prices.return_value = {
            'AAPL': (150.0, 1000000),
            'MSFT': (300.0, 500000)
        }
        mock_get_fetcher.return_value = mock_fetcher
        
        # Test search_stocks
        result = self.bot.search_stocks(
            symbols=['AAPL', 'MSFT'],
            use_screener=False,
            max_stocks=10
        )
        
        # Should have called the async fetcher
        self.assertTrue(mock_get_fetcher.called)
        print("✓ search_stocks uses async fetcher when available")
    
    def test_search_stocks_without_async(self):
        """Test that search_stocks works without async fetcher"""
        # Temporarily disable async fetching
        original_value = os.environ.get('ENABLE_ASYNC_FETCHING')
        os.environ['ENABLE_ASYNC_FETCHING'] = 'false'
        
        try:
            # Create new bot instance
            bot = TradingBot(total_capital=10000.0)
            
            # Should not crash when searching stocks
            result = bot.search_stocks(
                symbols=['AAPL'],
                use_screener=False,
                max_stocks=1
            )
            
            # Should return list (may be empty if no data available)
            self.assertIsInstance(result, list)
            print("✓ search_stocks works without async fetcher")
            
        finally:
            # Restore environment
            if original_value:
                os.environ['ENABLE_ASYNC_FETCHING'] = original_value
            else:
                os.environ.pop('ENABLE_ASYNC_FETCHING', None)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
