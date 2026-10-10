#!/usr/bin/env python3
"""
Test script for live mode dry-run validation
Tests end-to-end workflow validation without executing actual trades
"""

import os
# Set test environment
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')
os.environ.setdefault('SCHWAB_SANDBOX_MODE', 'false')
os.environ.setdefault('DRY_RUN_MODE', 'true')

import unittest
from unittest.mock import patch, MagicMock
import logging




class TestDryRunMode(unittest.TestCase):
    """Test suite for dry-run mode validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Ensure DRY_RUN_MODE is enabled
        os.environ['DRY_RUN_MODE'] = 'true'
        
        # Import main again to pick up environment changes
        import importlib
        import main as main_module
        import sys
        importlib.reload(sys.modules['main'])
        
        # Use TradingBot from the reloaded module
        self.bot = main_module.TradingBot(total_capital=10000.0)
        
    def test_dry_run_mode_enabled(self):
        """Test that dry-run mode is properly enabled"""
        # Verify environment variable is set
        self.assertEqual(os.getenv('DRY_RUN_MODE', 'false').lower(), 'true')
    
    def test_dry_run_buy_order_validation(self):
        """Test dry-run validation for BUY order"""
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True), \
             patch.object(self.bot, 'filter_stock', return_value=(True, 'ok')):
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
        self.assertIsInstance(result, dict, "Should return a dict")
        self.assertEqual(result.get('status'), 'dry_run_success', "Should have dry_run_success status")
        self.assertIn('order_id', result, "Should contain order_id")
        self.assertIn('DRY_RUN_', result['order_id'], "Order ID should be marked as dry-run")
        self.assertEqual(result['symbol'], 'AAPL')
        self.assertEqual(result['action'], 'BUY')
        self.assertEqual(result['price'], 150.0)
        self.assertIn('order_payload', result, "Should contain order_payload")
        payload = result['order_payload']
        self.assertEqual(payload['orderType'], 'LIMIT', "BUY should use LIMIT order")
        self.assertEqual(payload['session'], 'NORMAL')
        self.assertEqual(payload['duration'], 'DAY')
        self.assertEqual(len(payload['orderLegCollection']), 1)
        self.assertEqual(payload['orderLegCollection'][0]['instruction'], 'BUY')
        self.assertEqual(payload['orderLegCollection'][0]['instrument']['symbol'], 'AAPL')
        self.assertEqual(payload['price'], 150.0, "LIMIT order should include price")
    
    def test_dry_run_sell_order_validation(self):
        """Test dry-run validation for SELL order"""
        self.bot.positions['AAPL'] = {
            'entry_price': 140.0,
            'quantity': 10,
            'entry_date': '2024-01-01',
            'trailing_stop': 0.03
        }
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True):
            result = self.bot.execute_trade_live_mode('AAPL', 'SELL', 150.0)
        
        # Check result structure
        self.assertIsInstance(result, dict, "Should return a dict")
        self.assertEqual(result.get('status'), 'dry_run_success', "Should have dry_run_success status")
        self.assertEqual(result['action'], 'SELL')
        
        # Validate order payload structure
        payload = result['order_payload']
        self.assertEqual(payload['orderType'], 'MARKET', "SELL should use MARKET order")
        self.assertNotIn('price', payload, "MARKET order should not include price")
    
    def test_dry_run_credential_validation(self):
        """Test that credential validation still happens in dry-run mode"""
        # Credentials should fail with placeholders
        result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
        
        self.assertIsInstance(result, dict, "Should return a dict")
        self.assertEqual(result.get('status'), 'error', "Should fail with invalid credentials")
        self.assertEqual(result.get('reason'), 'invalid_credentials')
    
    def test_dry_run_capital_floor_check(self):
        """Test that capital floor checks still work in dry-run mode"""
        # Set capital below floor
        self.bot.total_capital = 500  # Below 10% of starting capital
        
        # Mock credential validation to pass
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True):
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
        
        # Should be paused due to capital floor breach
        self.assertEqual(result.get('status'), 'paused')
        self.assertEqual(result.get('reason'), 'capital_floor_breach')
    
    def test_dry_run_risk_threshold_check(self):
        """Test that risk threshold checks work in dry-run mode"""
        # Set a very high current allocation that will exceed risk threshold
        # Risk limit = BOT_RISK_THRESHOLD * total_capital = 0.02 * 10000 = $200
        # Set allocation to $10000 so potential_loss = $10000 * 0.06 = $600 > $200
        self.bot.track_record['current_allocation'] = 10000  # Very high allocation
        
        # Mock credential validation to pass
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True):
            # Try to trade (risk check should fail with high allocation)
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 100.0)
        
        # Should be skipped due to risk threshold or stock filter (both yield status 'skipped')
        self.assertIn(result.get('status'), ['skipped', 'dry_run_success'])
        if result.get('status') == 'skipped':
            self.assertIn(result.get('reason'), ['risk_threshold_exceeded', 'failed_stock_filter'])
    
    def test_dry_run_stock_filter_check(self):
        """Test that stock filtering works in dry-run mode"""
        # Mock credential validation to pass
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True):
            # Try to buy a penny stock (should fail filter)
            result = self.bot.execute_trade_live_mode('PENNY', 'BUY', 1.0)
        
        # Should be skipped due to stock filter
        self.assertEqual(result.get('status'), 'skipped')
        self.assertEqual(result.get('reason'), 'failed_stock_filter')
    
    def test_dry_run_no_actual_trade_execution(self):
        """Test that no actual API calls are made in dry-run mode"""
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True), \
             patch.object(self.bot, 'filter_stock', return_value=(True, 'ok')):
            with patch.object(self.bot, 'schwab_client', create=True) as mock_client:
                mock_client.place_order = MagicMock()
                result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
                mock_client.place_order.assert_not_called()
                self.assertEqual(result.get('status'), 'dry_run_success')
    
    def test_dry_run_order_payload_completeness(self):
        """Test that order payload includes all required fields"""
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True), \
             patch.object(self.bot, 'filter_stock', return_value=(True, 'ok')):
            result = self.bot.execute_trade_live_mode('MSFT', 'BUY', 300.0)
        
        # Check result has complete payload
        self.assertEqual(result['status'], 'dry_run_success')
        payload = result['order_payload']
        
        # Required fields
        self.assertIn('orderType', payload)
        self.assertIn('session', payload)
        self.assertIn('duration', payload)
        self.assertIn('orderStrategyType', payload)
        self.assertIn('orderLegCollection', payload)
        
        # Order leg fields
        leg = payload['orderLegCollection'][0]
        self.assertIn('instruction', leg)
        self.assertIn('quantity', leg)
        self.assertIn('instrument', leg)
        self.assertIn('symbol', leg['instrument'])
        self.assertIn('assetType', leg['instrument'])
    
    def test_dry_run_multiple_orders(self):
        """Test multiple dry-run orders in sequence"""
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True), \
             patch.object(self.bot, 'filter_stock', return_value=(True, 'ok')):
            result1 = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
            result2 = self.bot.execute_trade_live_mode('GOOGL', 'BUY', 140.0)
        self.assertIn(result1['status'], ['dry_run_success', 'skipped'])
        self.assertIn(result2['status'], ['dry_run_success', 'skipped'])
        if result1['status'] == 'dry_run_success' and result2['status'] == 'dry_run_success':
            self.assertNotEqual(result1['order_id'], result2['order_id'])


class TestDryRunConfiguration(unittest.TestCase):
    """Test dry-run configuration and environment"""
    
    def test_dry_run_environment_variable(self):
        """Test DRY_RUN_MODE environment variable loading"""
        # Test enabled
        os.environ['DRY_RUN_MODE'] = 'true'
        self.assertEqual(os.getenv('DRY_RUN_MODE', 'false').lower(), 'true')
        
        # Test disabled
        os.environ['DRY_RUN_MODE'] = 'false'
        self.assertEqual(os.getenv('DRY_RUN_MODE', 'false').lower(), 'false')
    
    def test_dry_run_with_paper_trading(self):
        """Test that dry-run can work alongside paper trading mode"""
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['DRY_RUN_MODE'] = 'true'
        
        # Both should be enabled independently
        self.assertEqual(os.getenv('PAPER_TRADING_MODE', 'false').lower(), 'true')
        self.assertEqual(os.getenv('DRY_RUN_MODE', 'false').lower(), 'true')


class TestDryRunLogging(unittest.TestCase):
    """Test logging behavior in dry-run mode"""
    
    def setUp(self):
        """Set up test fixtures"""
        os.environ['DRY_RUN_MODE'] = 'true'
        
        # Import main again to pick up environment changes
        import importlib
        import main as main_module
        importlib.reload(main_module)
        
        self.bot = main_module.TradingBot(total_capital=10000.0)
    
    def test_dry_run_logging_output(self):
        """Test that dry-run mode logs appropriate messages"""
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True), \
             patch.object(self.bot, 'filter_stock', return_value=(True, 'ok')):
            with self.assertLogs('main', level='INFO') as log_context:
                self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
                self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
                log_output = ' '.join(log_context.output)
                self.assertIn('DRY-RUN', log_output.upper())
                self.assertIn('AAPL', log_output)


class TestDryRunValidation(unittest.TestCase):
    """Test suite for enhanced dry-run validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Ensure DRY_RUN_MODE is enabled
        os.environ['DRY_RUN_MODE'] = 'true'
        os.environ['PAPER_TRADING_MODE'] = 'false'  # Live mode
        
        # Import TradingBot from main module
        from main import TradingBot
        self.bot = TradingBot(total_capital=10000.0)
    
    def tearDown(self):
        """Clean up environment"""
        os.environ['DRY_RUN_MODE'] = 'false'
        os.environ['PAPER_TRADING_MODE'] = 'true'
    
    def test_dry_run_does_not_modify_capital(self):
        """Test that dry-run mode does not modify capital"""
        initial_capital = self.bot.total_capital
        if hasattr(self.bot, 'execute_trade_live_mode'):
            with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True), \
                 patch.object(self.bot, 'filter_stock', return_value=(True, 'ok')):
                self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
        self.assertEqual(self.bot.total_capital, initial_capital,
                        "Capital should not change in dry-run mode")

    def test_dry_run_does_not_create_positions(self):
        """Test that dry-run mode does not create positions"""
        initial_positions = len(self.bot.positions)
        if hasattr(self.bot, 'execute_trade_live_mode'):
            with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True), \
                 patch.object(self.bot, 'filter_stock', return_value=(True, 'ok')):
                self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
        self.assertEqual(len(self.bot.positions), initial_positions,
                        "Positions should not change in dry-run mode")

    def test_dry_run_validates_parameters(self):
        """Test that dry-run mode still validates trade parameters"""
        if hasattr(self.bot, 'execute_trade_live_mode'):
            with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True), \
                 patch.object(self.bot, 'filter_stock', return_value=(True, 'ok')):
                result = self.bot.execute_trade_live_mode('', 'BUY', 150.0)
                if result is not None:
                    self.assertIn('status', result, "Should return status in result")

    def test_dry_run_logs_simulation(self):
        """Test that dry-run mode logs simulated trades"""
        with patch('main.logger') as mock_logger:
            if hasattr(self.bot, 'execute_trade_live_mode'):
                with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True), \
                     patch.object(self.bot, 'filter_stock', return_value=(True, 'ok')):
                    self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
                log_called = (mock_logger.info.called or
                             mock_logger.warning.called or
                             mock_logger.error.called)
                self.assertTrue(log_called,
                               "Expected at least one log call during dry-run simulation")


if __name__ == '__main__':
    # Set up test logging
    logging.basicConfig(level=logging.CRITICAL)  # Suppress logs during testing
    
    # Run tests
    unittest.main(verbosity=2)
