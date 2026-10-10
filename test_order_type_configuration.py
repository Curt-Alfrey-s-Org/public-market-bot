#!/usr/bin/env python3
"""
Test script for order type configuration
Tests the new order_type parameter and environment variable configuration
"""

import os
# Set test environment (use [] not setdefault so we override .env on Linux)
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
os.environ['DRY_RUN_MODE'] = 'true'  # Must override .env so dry-run path is used

import unittest
from unittest.mock import patch

# Import the trading bot
import main
TradingBot = main.TradingBot
BOT_DEFAULT_BUY_ORDER_TYPE = main.BOT_DEFAULT_BUY_ORDER_TYPE
BOT_DEFAULT_SELL_ORDER_TYPE = main.BOT_DEFAULT_SELL_ORDER_TYPE

class TestOrderTypeConfiguration(unittest.TestCase):
    """Test suite for order type configuration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = main.TradingBot(total_capital=10000.0)
    def test_default_order_types_loaded(self):
        """Test that default order types are loaded from environment"""
        # Should default to LIMIT for BUY, MARKET for SELL
        self.assertEqual(BOT_DEFAULT_BUY_ORDER_TYPE, 'LIMIT')
        self.assertEqual(main.BOT_DEFAULT_BUY_ORDER_TYPE, 'LIMIT')
        self.assertEqual(main.BOT_DEFAULT_SELL_ORDER_TYPE, 'MARKET')
    def test_custom_buy_order_type(self):
        """Test custom BUY order type from environment"""
        # Save original value
        original_value = main.BOT_DEFAULT_BUY_ORDER_TYPE
        # Set new env var and reload
        os.environ['BOT_DEFAULT_BUY_ORDER_TYPE'] = 'MARKET'
        import importlib
        importlib.reload(main)
        
        # Check new value
        self.assertEqual(main.BOT_DEFAULT_BUY_ORDER_TYPE, 'MARKET')
        
        # Restore original
        os.environ['BOT_DEFAULT_BUY_ORDER_TYPE'] = original_value
        importlib.reload(main)
        self.assertEqual(main.BOT_DEFAULT_BUY_ORDER_TYPE, original_value)
    
    def test_custom_sell_order_type(self):
        """Test custom SELL order type from environment"""
        # Save original value
        original_value = main.BOT_DEFAULT_SELL_ORDER_TYPE
        # Set new env var and reload
        os.environ['BOT_DEFAULT_SELL_ORDER_TYPE'] = 'LIMIT'
        import importlib
        importlib.reload(main)
        
        # Check new value
        self.assertEqual(main.BOT_DEFAULT_SELL_ORDER_TYPE, 'LIMIT')
        
        # Restore original
        os.environ['BOT_DEFAULT_SELL_ORDER_TYPE'] = original_value
        importlib.reload(main)
        self.assertEqual(main.BOT_DEFAULT_SELL_ORDER_TYPE, original_value)
    
    def test_execute_trade_default_order_type_buy(self):
        """Test that BUY uses default LIMIT order type in dry-run mode"""
        with patch('main.DRY_RUN_MODE', True), \
             patch.object(self.bot, '_validate_live_mode_credentials', return_value=True), \
             patch.object(self.bot, 'filter_stock', return_value=(True, 'ok')):
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
            self.assertIn('order_type', result)
            self.assertEqual(result['order_type'], 'LIMIT')
            self.assertEqual(result['status'], 'dry_run_success')
    
    def test_execute_trade_default_order_type_sell(self):
        """Test that SELL uses default MARKET order type in dry-run mode"""
        # Add a position first
        self.bot.positions['AAPL'] = {'quantity': 10, 'entry_price': 140.0, 'entry_date': '2024-01-01'}
        
        # Mock credential validation and force dry-run (import order can leave main.DRY_RUN_MODE false)
        with patch('main.DRY_RUN_MODE', True), \
             patch.object(self.bot, '_validate_live_mode_credentials', return_value=True):
            result = self.bot.execute_trade_live_mode('AAPL', 'SELL', 150.0)
            
            # Check that order_type is MARKET
            self.assertIn('order_type', result)
            self.assertEqual(result['order_type'], 'MARKET')
            self.assertEqual(result['status'], 'dry_run_success')
    
    def test_execute_trade_custom_order_type_buy(self):
        """Test that BUY can use custom MARKET order type via parameter"""
        with patch('main.DRY_RUN_MODE', True), \
             patch.object(self.bot, '_validate_live_mode_credentials', return_value=True), \
             patch.object(self.bot, 'filter_stock', return_value=(True, 'ok')):
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0, order_type='MARKET')
            self.assertIn('order_type', result)
            self.assertEqual(result['order_type'], 'MARKET')
            self.assertEqual(result['status'], 'dry_run_success')
    
    def test_execute_trade_custom_order_type_sell(self):
        """Test that SELL can use custom LIMIT order type via parameter"""
        # Add a position first
        self.bot.positions['AAPL'] = {'quantity': 10, 'entry_price': 140.0, 'entry_date': '2024-01-01'}
        
        with patch('main.DRY_RUN_MODE', True), \
             patch.object(self.bot, '_validate_live_mode_credentials', return_value=True):
            result = self.bot.execute_trade_live_mode('AAPL', 'SELL', 150.0, order_type='LIMIT')
            
            # Check that order_type is LIMIT (overridden)
            self.assertIn('order_type', result)
            self.assertEqual(result['order_type'], 'LIMIT')
            self.assertEqual(result['status'], 'dry_run_success')
    
    def test_execute_trade_invalid_order_type(self):
        """Test that invalid order type falls back to default"""
        with patch('main.DRY_RUN_MODE', True), \
             patch.object(self.bot, '_validate_live_mode_credentials', return_value=True), \
             patch.object(self.bot, 'filter_stock', return_value=(True, 'ok')):
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0, order_type='INVALID')
            self.assertIn('order_type', result)
            self.assertEqual(result['order_type'], 'LIMIT')
            self.assertEqual(result['status'], 'dry_run_success')
    
    def test_order_payload_includes_price_for_limit(self):
        """Test that LIMIT orders include price in payload"""
        with patch('main.DRY_RUN_MODE', True), \
             patch.object(self.bot, '_validate_live_mode_credentials', return_value=True), \
             patch.object(self.bot, 'filter_stock', return_value=(True, 'ok')), \
             patch('main.LIMIT_ORDER_OFFSET_PCT', 0.0):
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0, order_type='LIMIT')
            self.assertIn('order_payload', result)
            self.assertIn('price', result['order_payload'])
            self.assertEqual(result['order_payload']['price'], 150.0)
            self.assertEqual(result['status'], 'dry_run_success')

    def test_order_payload_no_price_for_market(self):
        """Test that MARKET orders do not include price in payload"""
        with patch('main.DRY_RUN_MODE', True), \
             patch.object(self.bot, '_validate_live_mode_credentials', return_value=True), \
             patch.object(self.bot, 'filter_stock', return_value=(True, 'ok')):
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0, order_type='MARKET')
            self.assertIn('order_payload', result)
            self.assertNotIn('price', result['order_payload'])
            self.assertEqual(result['status'], 'dry_run_success')


if __name__ == '__main__':
    unittest.main()
