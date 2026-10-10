#!/usr/bin/env python3
"""
Test suite to verify MAX_STOCK_PRICE filtering is working correctly
Tests the fix for the issue where MSFT and AAPL were trading despite MAX_STOCK_PRICE limit
"""

import os
import unittest

# Disable PDT rules and set paper trading mode for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')

# Set specific test values for stock price limits
os.environ['MIN_STOCK_PRICE'] = '5.0'
os.environ['MAX_STOCK_PRICE'] = '60.0'  # Set to $60 as mentioned in the issue

from main import TradingBot, MIN_STOCK_PRICE, MAX_STOCK_PRICE


class TestMaxStockPriceFiltering(unittest.TestCase):
    """Test that MAX_STOCK_PRICE is properly enforced in filter_stock()"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_max_stock_price_environment_variable(self):
        """Test that MAX_STOCK_PRICE is loaded from environment"""
        self.assertEqual(MAX_STOCK_PRICE, 60.0, "MAX_STOCK_PRICE should be loaded as 60.0")
    
    def test_filter_stock_below_minimum(self):
        """Test that stocks below MIN_STOCK_PRICE are rejected"""
        is_valid, reason = self.bot.filter_stock('PENNY', price=3.0, volume=1000000)
        self.assertFalse(is_valid, "Stock below MIN_STOCK_PRICE should be rejected")
        self.assertIn('below minimum', reason.lower())
    
    def test_filter_stock_above_maximum(self):
        """Test that stocks above MAX_STOCK_PRICE are rejected"""
        # Test with MSFT-like price (~$420)
        is_valid, reason = self.bot.filter_stock('MSFT', price=420.0, volume=10000000)
        self.assertFalse(is_valid, "Stock above MAX_STOCK_PRICE should be rejected")
        self.assertIn('exceeds maximum', reason.lower())
    
    def test_filter_stock_above_maximum_aapl(self):
        """Test that AAPL-like prices (~$230) are rejected when MAX_STOCK_PRICE is $60"""
        is_valid, reason = self.bot.filter_stock('AAPL', price=230.0, volume=50000000)
        self.assertFalse(is_valid, "AAPL price above MAX_STOCK_PRICE should be rejected")
        self.assertIn('exceeds maximum', reason.lower())
        self.assertIn('$230.00', reason)
        self.assertIn('$60.00', reason)
    
    def test_filter_stock_within_range(self):
        """Test that stocks within MIN and MAX price range are accepted"""
        is_valid, reason = self.bot.filter_stock('VALID', price=50.0, volume=1000000)
        self.assertTrue(is_valid, f"Stock within price range should be accepted: {reason}")
        self.assertIn('passed', reason.lower())
    
    def test_filter_stock_at_max_boundary(self):
        """Test edge case: stock at exactly MAX_STOCK_PRICE"""
        is_valid, reason = self.bot.filter_stock('BOUNDARY', price=60.0, volume=1000000)
        self.assertTrue(is_valid, "Stock at MAX_STOCK_PRICE should be accepted")
    
    def test_filter_stock_just_above_max(self):
        """Test edge case: stock just above MAX_STOCK_PRICE"""
        is_valid, reason = self.bot.filter_stock('OVER', price=60.01, volume=1000000)
        self.assertFalse(is_valid, "Stock above MAX_STOCK_PRICE should be rejected")
        self.assertIn('exceeds maximum', reason.lower())
    
    def test_validation_metadata_max_price_check(self):
        """Test that max_price check is added to validation metadata"""
        # Clear any previous validation logs
        if hasattr(self.bot, 'stock_validation_log'):
            self.bot.stock_validation_log = []
        
        # Run filter on valid stock
        is_valid, reason = self.bot.filter_stock('TEST', price=40.0, volume=1000000)
        self.assertTrue(is_valid)
        
        # Check that validation metadata includes max_price check
        if hasattr(self.bot, 'stock_validation_log') and len(self.bot.stock_validation_log) > 0:
            last_validation = self.bot.stock_validation_log[-1]
            checks_passed = last_validation.get('metadata', {}).get('checks_passed', [])
            self.assertIn('max_price', checks_passed, "Validation should include max_price check")


class TestParameterConsistency(unittest.TestCase):
    """Test that stock price parameters are consistent and not conflicting"""
    
    def test_min_max_price_consistency(self):
        """Test that MIN_STOCK_PRICE is less than MAX_STOCK_PRICE"""
        self.assertLess(MIN_STOCK_PRICE, MAX_STOCK_PRICE,
                       f"MIN_STOCK_PRICE ({MIN_STOCK_PRICE}) should be less than MAX_STOCK_PRICE ({MAX_STOCK_PRICE})")
    
    def test_min_price_positive(self):
        """Test that MIN_STOCK_PRICE is positive"""
        self.assertGreater(MIN_STOCK_PRICE, 0, "MIN_STOCK_PRICE should be positive")
    
    def test_max_price_positive(self):
        """Test that MAX_STOCK_PRICE is positive"""
        self.assertGreater(MAX_STOCK_PRICE, 0, "MAX_STOCK_PRICE should be positive")
    
    def test_reasonable_price_range(self):
        """Test that price range is reasonable"""
        price_range = MAX_STOCK_PRICE - MIN_STOCK_PRICE
        self.assertGreater(price_range, 0, "Price range should be positive")
        self.assertGreater(price_range, 10, "Price range should be at least $10 for reasonable trading")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
