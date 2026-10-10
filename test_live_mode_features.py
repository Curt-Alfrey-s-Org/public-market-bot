#!/usr/bin/env python3
"""
Test script for live mode features
Tests logging, error handling, and validation
"""

import os
# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import logging

# Import the trading bot
from main import TradingBot, validate_configuration, PAPER_TRADING_MODE


class TestLiveModeFeatures(unittest.TestCase):
    """Test suite for live mode features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_paper_mode_configuration(self):
        """Test that paper mode is configurable via environment variable"""
        # Should default to True in our environment
        self.assertTrue(PAPER_TRADING_MODE)
    
    def test_configuration_validation_paper_mode(self):
        """Test configuration validation in paper mode"""
        is_valid, issues = validate_configuration()
        self.assertTrue(is_valid, "Paper mode configuration should be valid")
        self.assertEqual(len(issues), 0, "Paper mode should have no validation issues")
    
    def test_credential_validation(self):
        """Test that credential validation works"""
        result = self.bot._validate_live_mode_credentials()
        # Should fail with placeholder credentials
        self.assertFalse(result, "Placeholder credentials should not validate")
    
    def test_execute_trade_live_mode_without_credentials(self):
        """Test that live mode trade fails gracefully without credentials"""
        result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
        
        self.assertIsInstance(result, dict, "Should return a dict")
        self.assertEqual(result.get('status'), 'error', "Should have error status")
        self.assertEqual(result.get('reason'), 'invalid_credentials', "Should fail due to invalid credentials")
    
    @patch('main.requests.post')
    def test_execute_trade_live_mode_timeout(self, mock_post):
        """Test that API timeout is handled correctly"""
        # Mock a timeout
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        # Temporarily override credential validation
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True):
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
        
        self.assertEqual(result.get('status'), 'error')
        self.assertEqual(result.get('reason'), 'timeout')
    
    @patch('main.requests.post')
    def test_execute_trade_live_mode_connection_error(self, mock_post):
        """Test that connection errors are handled correctly"""
        # Mock a connection error
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        # Temporarily override credential validation
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True):
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
        
        self.assertEqual(result.get('status'), 'error')
        self.assertEqual(result.get('reason'), 'connection_error')
    
    @patch('main.requests.post')
    def test_execute_trade_live_mode_auth_error(self, mock_post):
        """Test that authentication errors are handled correctly"""
        # Mock a 401 auth error
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        # Temporarily override credential validation
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True):
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
        
        self.assertEqual(result.get('status'), 'error')
        self.assertEqual(result.get('reason'), 'authentication_failed')
    
    @patch('main.requests.post')
    def test_execute_trade_live_mode_rate_limit(self, mock_post):
        """Test that rate limit errors are handled correctly"""
        # Mock a 429 rate limit error
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"
        mock_post.return_value = mock_response
        
        # Temporarily override credential validation
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True):
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
        
        self.assertEqual(result.get('status'), 'error')
        self.assertEqual(result.get('reason'), 'rate_limit_exceeded')
    
    @patch('main.requests.post')
    def test_execute_trade_live_mode_success(self, mock_post):
        """Test successful live mode trade execution"""
        # Mock a successful response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"orderId": "12345"}'
        mock_response.json.return_value = {"orderId": "12345"}
        mock_post.return_value = mock_response
        
        # Temporarily override credential validation
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True):
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
        
        self.assertEqual(result.get('status'), 'success')
        self.assertEqual(result.get('order_id'), '12345')
    
    def test_capital_floor_check_in_live_mode(self):
        """Test that capital floor check works in live mode"""
        # Set capital below floor
        self.bot.total_capital = 500  # Below 10% of 10000
        can_trade, msg = self.bot.check_capital_floor()
        
        self.assertFalse(can_trade, "Should not allow trading below capital floor")
        self.assertTrue(self.bot.is_paused, "Bot should be paused")
    
    def test_risk_check_in_live_mode(self):
        """Test that risk checks work correctly"""
        # Try to execute a trade that exceeds risk threshold
        result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 1.0)  # Low price = high quantity
        
        # Should fail risk check since allocation would be too high relative to capital
        self.assertIn(result.get('status'), ['error', 'skipped'])


class TestLogging(unittest.TestCase):
    """Test logging configuration"""
    
    def test_logging_configured(self):
        """Test that logging is properly configured"""
        # Import main and set up logging
        import main
        main.setup_logging()
        
        # Check that logger exists
        logger = logging.getLogger('main')
        self.assertIsNotNone(logger)
        
        # Check that handlers are configured
        root_logger = logging.getLogger()
        self.assertGreater(len(root_logger.handlers), 0, "Should have at least one handler")
    
    def test_log_file_creation(self):
        """Test that log file is created"""
        import main
        main.setup_logging()
        
        # Log something
        logger = logging.getLogger('main')
        logger.info("Test log message")
        
        # Check if log file exists
        self.assertTrue(os.path.exists('trading_bot.log'), "Log file should be created")


if __name__ == '__main__':
    # Set up test logging
    logging.basicConfig(level=logging.CRITICAL)  # Suppress logs during testing
    
    # Run tests
    unittest.main(verbosity=2)
