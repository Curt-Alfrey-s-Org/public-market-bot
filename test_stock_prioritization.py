#!/usr/bin/env python3
"""
Test stock prioritization and TOS-like scanning behavior
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import yfinance before importing stock_screener
try:
    import yfinance as yf
except ImportError:
    yf = None

from stock_screener import StockScreener


class TestStockPrioritization(unittest.TestCase):
    """Test stock scoring and prioritization features"""

    def setUp(self):
        """Set up test fixtures"""
        # Use a small predefined universe for testing
        self.test_universe = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMD', 'INTC']

    def test_calculate_stock_score(self):
        """Test that stock scoring produces valid scores"""
        screener = StockScreener(stock_universe=self.test_universe)
        
        # Test stock data
        stock_data = {
            'symbol': 'AAPL',
            'price': 150.0,
            'volume': 50000000,
            'avgVolume': 50000000,
            'volatility': 0.05,
            'marketCap': 2500000000000
        }
        
        # Calculate score (no yfinance needed - just scoring logic)
        scores = screener.calculate_stock_score('AAPL', stock_data)
        
        # Verify score structure
        self.assertIn('symbol', scores)
        self.assertIn('momentum_score', scores)
        self.assertIn('volume_score', scores)
        self.assertIn('volatility_score', scores)
        self.assertIn('liquidity_score', scores)
        self.assertIn('sentiment_score', scores)
        self.assertIn('composite_score', scores)
        
        # Verify score is a number
        self.assertIsInstance(scores['composite_score'], float)
        
        # Verify score is in reasonable range (0-100)
        self.assertGreaterEqual(scores['composite_score'], 0.0)
        self.assertLessEqual(scores['composite_score'], 100.0)

    def test_screen_stocks_prioritization_parameter(self):
        """Test that prioritize parameter is accepted"""
        screener = StockScreener(stock_universe=self.test_universe)
        
        # Just test that the parameter is accepted (don't actually fetch data)
        # This tests the API/interface without needing yfinance
        try:
            # Call with prioritize=True - should not raise error
            # (will fail to fetch data but that's OK for this test)
            screener.screen_stocks(
                candidate_symbols=[],  # Empty list to avoid fetching
                max_results=3,
                use_cache=False,
                use_advanced_filters=False,
                prioritize=True
            )
        except Exception as e:
            # Should not fail due to parameter issues
            if "prioritize" in str(e):
                self.fail(f"prioritize parameter not accepted: {e}")

    def test_screen_stocks_without_prioritization_parameter(self):
        """Test that non-prioritized screening parameter works"""
        screener = StockScreener(stock_universe=self.test_universe)
        
        # Test that the parameter is accepted
        try:
            screener.screen_stocks(
                candidate_symbols=[],  # Empty list to avoid fetching
                max_results=3,
                use_cache=False,
                use_advanced_filters=False,
                prioritize=False
            )
        except Exception as e:
            # Should not fail due to parameter issues
            if "prioritize" in str(e):
                self.fail(f"prioritize parameter not accepted: {e}")

    def test_scoring_weights_configuration(self):
        """Test that scoring weights are configurable via environment"""
        # These should be loaded from environment
        from stock_screener import (
            SCORE_WEIGHT_MOMENTUM,
            SCORE_WEIGHT_VOLUME,
            SCORE_WEIGHT_VOLATILITY,
            SCORE_WEIGHT_LIQUIDITY,
            SCORE_WEIGHT_SENTIMENT
        )
        
        # Verify weights are numbers
        self.assertIsInstance(SCORE_WEIGHT_MOMENTUM, float)
        self.assertIsInstance(SCORE_WEIGHT_VOLUME, float)
        self.assertIsInstance(SCORE_WEIGHT_VOLATILITY, float)
        self.assertIsInstance(SCORE_WEIGHT_LIQUIDITY, float)
        self.assertIsInstance(SCORE_WEIGHT_SENTIMENT, float)
        
        # Weights should be between 0 and 1
        for weight in [SCORE_WEIGHT_MOMENTUM, SCORE_WEIGHT_VOLUME, 
                      SCORE_WEIGHT_VOLATILITY, SCORE_WEIGHT_LIQUIDITY, 
                      SCORE_WEIGHT_SENTIMENT]:
            self.assertGreaterEqual(weight, 0.0)
            self.assertLessEqual(weight, 1.0)

    def test_scoring_differentiates_stocks(self):
        """Test that scoring differentiates between good and bad stocks"""
        screener = StockScreener(stock_universe=['GOOD', 'BAD'])
        
        # Create two clearly different stock profiles
        good_stock = {
            'symbol': 'GOOD',
            'price': 150.0,
            'volume': 50000000,
            'avgVolume': 50000000,
            'volatility': 0.05,  # Moderate volatility
            'marketCap': 2000000000000  # 2T market cap
        }
        
        bad_stock = {
            'symbol': 'BAD',
            'price': 150.0,
            'volume': 100000,  # Low volume
            'avgVolume': 100000,
            'volatility': 0.20,  # High volatility
            'marketCap': 500000000  # 500M market cap
        }
        
        # Score both stocks
        good_scores = screener.calculate_stock_score('GOOD', good_stock)
        bad_scores = screener.calculate_stock_score('BAD', bad_stock)
        
        # Good stock should have higher composite score
        self.assertGreater(
            good_scores['composite_score'], 
            bad_scores['composite_score'],
            "Good stock should score higher than bad stock"
        )


class TestEnvironmentConfiguration(unittest.TestCase):
    """Test environment variable configuration for prioritization"""

    def test_max_stocks_to_scan_config(self):
        """Test MAX_STOCKS_TO_SCAN is loaded from environment"""
        from stock_screener import MAX_STOCKS_TO_SCAN
        self.assertIsInstance(MAX_STOCKS_TO_SCAN, int)
        self.assertGreater(MAX_STOCKS_TO_SCAN, 0)

    def test_top_stocks_to_trade_config(self):
        """Test TOP_STOCKS_TO_TRADE is loaded from environment"""
        from stock_screener import TOP_STOCKS_TO_TRADE
        self.assertIsInstance(TOP_STOCKS_TO_TRADE, int)
        self.assertGreater(TOP_STOCKS_TO_TRADE, 0)


if __name__ == '__main__':
    unittest.main()
