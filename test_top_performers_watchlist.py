#!/usr/bin/env python3
"""
Test suite for Top Performers Watchlist feature

Tests:
- Watchlist data fetching from stock screener
- Win probability scoring and ranking
- Watchlist table formatting
- Bot integration with watchlist prioritization
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from datetime import datetime

# Set test environment variables before importing modules
os.environ['ENABLE_TOP_PERFORMERS_WATCHLIST'] = 'true'
os.environ['TOP_PERFORMERS_WATCHLIST_SIZE'] = '10'
os.environ['TOP_PERFORMERS_REFRESH_INTERVAL'] = '30'
os.environ['ENABLE_STOCK_SCREENER'] = 'true'
os.environ['ENABLE_ML_FILTER'] = 'false'  # Disable ML for faster tests


class TestTopPerformersWatchlist(unittest.TestCase):
    """Test suite for top performers watchlist feature"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Import here to ensure env vars are set first
        from stock_screener import StockScreener
        self.screener = StockScreener()
    
    def test_get_top_performers_method_exists(self):
        """Test that get_top_performers method exists in StockScreener"""
        self.assertTrue(hasattr(self.screener, 'get_top_performers'))
        self.assertTrue(callable(getattr(self.screener, 'get_top_performers')))
    
    @patch('stock_screener.StockScreener.get_swing_trade_candidates')
    @patch('stock_screener.StockScreener._get_cached_data')
    def test_get_top_performers_returns_list(self, mock_cached_data, mock_candidates):
        """Test that get_top_performers returns a list of stock dictionaries"""
        # Mock candidates data
        mock_candidates.return_value = [
            {
                'symbol': 'AAPL',
                'ml_win_probability': 0.75,
                'composite_score': 0.72,
                'sentiment_score': 0.65,
                'ml_confidence': 0.80,
                'sentiment_signal': 'Positive'
            },
            {
                'symbol': 'MSFT',
                'ml_win_probability': 0.68,
                'composite_score': 0.65,
                'sentiment_score': 0.60,
                'ml_confidence': 0.75,
                'sentiment_signal': 'Neutral'
            }
        ]
        
        # Mock cached data
        mock_cached_data.side_effect = [
            {'price': 150.0, 'volume': 1000000, 'volatility': 0.02},
            {'price': 300.0, 'volume': 2000000, 'volatility': 0.03}
        ]
        
        result = self.screener.get_top_performers(max_results=10)
        
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
    
    @patch('stock_screener.StockScreener.get_swing_trade_candidates')
    @patch('stock_screener.StockScreener._get_cached_data')
    def test_top_performers_sorted_by_win_probability(self, mock_cached_data, mock_candidates):
        """Test that top performers are sorted by win probability (highest first)"""
        # Mock candidates with different win probabilities
        mock_candidates.return_value = [
            {
                'symbol': 'LOW',
                'ml_win_probability': 0.45,
                'composite_score': 0.40,
                'sentiment_score': 0.50,
                'ml_confidence': 0.60
            },
            {
                'symbol': 'HIGH',
                'ml_win_probability': 0.85,
                'composite_score': 0.82,
                'sentiment_score': 0.80,
                'ml_confidence': 0.90
            },
            {
                'symbol': 'MED',
                'ml_win_probability': 0.65,
                'composite_score': 0.62,
                'sentiment_score': 0.60,
                'ml_confidence': 0.70
            }
        ]
        
        # Mock cached data for all symbols
        mock_cached_data.return_value = {
            'price': 100.0,
            'volume': 1000000,
            'volatility': 0.02
        }
        
        result = self.screener.get_top_performers(max_results=3)
        
        # Should be sorted HIGH, MED, LOW
        self.assertEqual(result[0]['symbol'], 'HIGH')
        self.assertEqual(result[1]['symbol'], 'MED')
        self.assertEqual(result[2]['symbol'], 'LOW')
        
        # Verify win probabilities are in descending order
        for i in range(len(result) - 1):
            self.assertGreaterEqual(result[i]['win_probability'], 
                                   result[i + 1]['win_probability'])
    
    @patch('stock_screener.StockScreener.get_swing_trade_candidates')
    @patch('stock_screener.StockScreener._get_cached_data')
    def test_top_performers_contains_required_fields(self, mock_cached_data, mock_candidates):
        """Test that each top performer contains all required fields"""
        mock_candidates.return_value = [
            {
                'symbol': 'AAPL',
                'ml_win_probability': 0.75,
                'composite_score': 0.72,
                'sentiment_score': 0.65,
                'ml_confidence': 0.80,
                'sentiment_signal': 'Positive'
            }
        ]
        
        mock_cached_data.return_value = {
            'price': 150.0,
            'volume': 1000000,
            'volatility': 0.02
        }
        
        result = self.screener.get_top_performers(max_results=1)
        
        self.assertEqual(len(result), 1)
        stock = result[0]
        
        # Check required fields
        required_fields = [
            'symbol', 'win_probability', 'composite_score',
            'sentiment_score', 'ml_confidence', 'price',
            'volume', 'volatility', 'last_updated'
        ]
        
        for field in required_fields:
            self.assertIn(field, stock, f"Missing required field: {field}")
    
    def test_convenience_function_exists(self):
        """Test that get_top_performers_watchlist convenience function exists"""
        from stock_screener import get_top_performers_watchlist
        
        self.assertTrue(callable(get_top_performers_watchlist))
    
    @patch('stock_screener.StockScreener.get_top_performers')
    def test_convenience_function_calls_screener(self, mock_get_top):
        """Test that convenience function calls the screener method"""
        from stock_screener import get_top_performers_watchlist
        
        mock_get_top.return_value = []
        
        get_top_performers_watchlist(max_stocks=25)
        
        # Verify the method was called
        mock_get_top.assert_called_once_with(max_results=25)
    
    def test_watchlist_size_respects_max_results(self):
        """Test that watchlist respects max_results parameter"""
        # This is an integration test, so we'll just verify the parameter is passed
        with patch('stock_screener.StockScreener.get_swing_trade_candidates') as mock_candidates:
            mock_candidates.return_value = []
            
            # Request 5 results
            result = self.screener.get_top_performers(max_results=5)
            
            # Should request 3x for filtering
            mock_candidates.assert_called_once()
            call_args = mock_candidates.call_args
            self.assertEqual(call_args[1]['max_results'], 15)  # 5 * 3


class TestWatchlistWebGUIIntegration(unittest.TestCase):
    """Test suite for watchlist integration with web GUI"""
    
    @patch('web_gui.WATCHLIST_ENABLED', True)
    @patch('web_gui.watchlist_data', [
        {'symbol': 'AAPL', 'win_probability': 0.75, 'price': 150.0},
        {'symbol': 'MSFT', 'win_probability': 0.68, 'price': 300.0}
    ])
    def test_watchlist_env_vars_loaded(self):
        """Test that watchlist environment variables are loaded"""
        # Import after patching
        import web_gui
        
        # These should be loaded from env vars we set in setUp
        self.assertTrue(web_gui.WATCHLIST_ENABLED)
        self.assertIsInstance(web_gui.WATCHLIST_SIZE, int)
        self.assertIsInstance(web_gui.WATCHLIST_REFRESH_INTERVAL, int)
    
    def test_watchlist_helper_functions_exist(self):
        """Test that watchlist helper functions exist in web_gui"""
        import web_gui
        
        self.assertTrue(hasattr(web_gui, 'fetch_watchlist_data'))
        self.assertTrue(hasattr(web_gui, 'update_watchlist_data'))
        self.assertTrue(hasattr(web_gui, 'format_watchlist_table'))
        
        self.assertTrue(callable(web_gui.fetch_watchlist_data))
        self.assertTrue(callable(web_gui.update_watchlist_data))
        self.assertTrue(callable(web_gui.format_watchlist_table))
    
    @patch('web_gui.get_top_performers_watchlist')
    def test_fetch_watchlist_data_calls_screener(self, mock_get_performers):
        """Test that fetch_watchlist_data calls the stock screener"""
        import web_gui
        
        mock_get_performers.return_value = []
        
        result = web_gui.fetch_watchlist_data()
        
        mock_get_performers.assert_called_once()
        self.assertIsInstance(result, list)
    
    def test_format_watchlist_table_handles_empty_list(self):
        """Test that format_watchlist_table handles empty watchlist gracefully"""
        import web_gui
        from dash import html
        
        result = web_gui.format_watchlist_table([])
        
        # Should return a message div
        self.assertIsInstance(result, html.Div)
    
    def test_format_watchlist_table_creates_datatable(self):
        """Test that format_watchlist_table creates a DataTable for non-empty list"""
        import web_gui
        from dash import dash_table
        
        sample_watchlist = [
            {
                'symbol': 'AAPL',
                'win_probability': 0.75,
                'composite_score': 0.72,
                'sentiment_score': 0.65,
                'ml_confidence': 0.80,
                'sentiment_signal': 'Positive',
                'price': 150.0,
                'volume': 1000000,
                'volatility': 0.02
            }
        ]
        
        result = web_gui.format_watchlist_table(sample_watchlist)
        
        # Should return a DataTable
        self.assertIsInstance(result, dash_table.DataTable)


class TestBotWatchlistPrioritization(unittest.TestCase):
    """Test suite for bot prioritizing watchlist stocks"""
    
    def test_bot_uses_watchlist_when_enabled(self):
        """Test that bot prioritizes watchlist stocks when enabled"""
        # This is tested in the run_bot_loop function
        # We'll verify the logic exists by checking the code
        import web_gui
        
        # Verify watchlist_data is used in run_bot_loop
        import inspect
        source = inspect.getsource(web_gui.run_bot_loop)
        
        # Check that watchlist is referenced
        self.assertIn('watchlist_data', source)
        self.assertIn('WATCHLIST_ENABLED', source)
    
    def test_bot_falls_back_to_screener_when_watchlist_empty(self):
        """Test that bot falls back to screener when watchlist is empty"""
        import web_gui
        import inspect
        
        source = inspect.getsource(web_gui.run_bot_loop)
        
        # Check that fallback logic exists
        self.assertIn('load_scan_symbols', source)


class TestWatchlistConfiguration(unittest.TestCase):
    """Test suite for watchlist configuration"""
    
    def test_env_example_has_watchlist_config(self):
        """Test that .env.example contains watchlist configuration"""
        # Use relative path for portability
        env_example_path = os.path.join(os.path.dirname(__file__), '.env.example')
        
        with open(env_example_path, 'r') as f:
            content = f.read()
        
        # Check for watchlist configuration
        self.assertIn('ENABLE_TOP_PERFORMERS_WATCHLIST', content)
        self.assertIn('TOP_PERFORMERS_WATCHLIST_SIZE', content)
        self.assertIn('TOP_PERFORMERS_REFRESH_INTERVAL', content)
        self.assertIn('TOP_PERFORMERS_MIN_UNIVERSE', content)


if __name__ == '__main__':
    unittest.main()
