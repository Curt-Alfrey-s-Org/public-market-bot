#!/usr/bin/env python3
"""
Test script for Schwab API Sandbox Integration
Tests market data fetching, trade execution, and fallback behavior
"""

import os
# Set test environment variables
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')
os.environ.setdefault('SCHWAB_SANDBOX_MODE', 'true')

import unittest
from unittest.mock import patch, MagicMock, Mock
import logging
import pytest

# Import after setting environment variables
from main import TradingBot, PAPER_TRADING_MODE, SCHWAB_SANDBOX_MODE


@pytest.mark.integration
class TestSchwabSandboxConfiguration(unittest.TestCase):
    """Test sandbox configuration and environment variables"""
    
    def test_sandbox_mode_enabled(self):
        """Test that sandbox mode is enabled via environment variable"""
        self.assertTrue(SCHWAB_SANDBOX_MODE, "Sandbox mode should be enabled")
    
    def test_paper_trading_mode_enabled(self):
        """Test that paper trading mode is enabled"""
        self.assertTrue(PAPER_TRADING_MODE, "Paper trading mode should be enabled")
    
    def test_api_endpoints_configured(self):
        """Test that sandbox API endpoints are configured"""
        from main import SCHWAB_SANDBOX_API_BASE, SCHWAB_SANDBOX_MARKET_DATA_BASE
        
        self.assertIsNotNone(SCHWAB_SANDBOX_API_BASE)
        self.assertIsNotNone(SCHWAB_SANDBOX_MARKET_DATA_BASE)
        self.assertIn('schwabapi.com', SCHWAB_SANDBOX_API_BASE.lower())


@pytest.mark.integration
class TestSchwabMarketDataAPI(unittest.TestCase):
    """Test Schwab market data API integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TradingBot(total_capital=10000.0)
    
    @patch('main.requests.get')
    def test_fetch_schwab_stock_price_success(self, mock_get):
        """Test successful price fetch from Schwab sandbox API"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'AAPL': {
                'quote': {
                    'lastPrice': 150.25,
                    'totalVolume': 50000000,
                    'bidPrice': 150.20,
                    'askPrice': 150.30
                }
            }
        }
        mock_get.return_value = mock_response
        
        # Test price fetch
        result = self.bot.fetch_schwab_stock_price('AAPL')
        
        self.assertIsNotNone(result)
        price, volume = result
        self.assertEqual(price, 150.25)
        self.assertEqual(volume, 50000000)
        
        # Verify API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn('symbols', call_args[1]['params'])
        self.assertEqual(call_args[1]['params']['symbols'], 'AAPL')
    
    @patch('main.requests.get')
    def test_fetch_schwab_stock_price_with_bid_ask_fallback(self, mock_get):
        """Test price calculation using bid/ask when lastPrice is not available"""
        # Mock API response without lastPrice
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'MSFT': {
                'quote': {
                    'bidPrice': 380.00,
                    'askPrice': 380.50,
                    'totalVolume': 30000000
                }
            }
        }
        mock_get.return_value = mock_response
        
        result = self.bot.fetch_schwab_stock_price('MSFT')
        
        self.assertIsNotNone(result)
        price, volume = result
        # Should use average of bid and ask
        self.assertEqual(price, 380.25)
        self.assertEqual(volume, 30000000)
    
    @patch('main.requests.get')
    def test_fetch_schwab_stock_price_caching(self, mock_get):
        """Test that price caching works correctly"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'GOOGL': {
                'quote': {
                    'lastPrice': 140.50,
                    'totalVolume': 20000000
                }
            }
        }
        mock_get.return_value = mock_response
        
        # First call should hit API
        result1 = self.bot.fetch_schwab_stock_price('GOOGL')
        self.assertIsNotNone(result1)
        self.assertEqual(mock_get.call_count, 1)
        
        # Second call within 60 seconds should use cache
        result2 = self.bot.fetch_schwab_stock_price('GOOGL')
        self.assertIsNotNone(result2)
        self.assertEqual(mock_get.call_count, 1)  # Still just 1 call
        
        # Results should be identical
        self.assertEqual(result1, result2)
    
    @patch('main.requests.get')
    def test_fetch_schwab_stock_price_authentication_error(self, mock_get):
        """Test handling of authentication errors"""
        # Mock 401 authentication error
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = self.bot.fetch_schwab_stock_price('AAPL')
        
        self.assertIsNone(result)
    
    @patch('main.requests.get')
    def test_fetch_schwab_stock_price_rate_limit(self, mock_get):
        """Test handling of rate limit errors"""
        # Mock 429 rate limit error
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        result = self.bot.fetch_schwab_stock_price('AAPL')
        
        self.assertIsNone(result)
    
    @patch('main.requests.get')
    def test_fetch_schwab_stock_price_timeout(self, mock_get):
        """Test handling of timeout errors"""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        
        result = self.bot.fetch_schwab_stock_price('AAPL')
        
        self.assertIsNone(result)
    
    @patch('main.requests.get')
    def test_fetch_schwab_stock_price_connection_error(self, mock_get):
        """Test handling of connection errors"""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        
        result = self.bot.fetch_schwab_stock_price('AAPL')
        
        self.assertIsNone(result)
    
    @patch('main.requests.get')
    def test_fetch_schwab_stock_price_symbol_not_found(self, mock_get):
        """Test handling of symbol not found errors"""
        # Mock 404 not found
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = self.bot.fetch_schwab_stock_price('INVALID')
        
        self.assertIsNone(result)


@pytest.mark.integration
class TestGetStockPriceFallback(unittest.TestCase):
    """Test get_stock_price fallback logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TradingBot(total_capital=10000.0)
    
    @patch.object(TradingBot, 'fetch_schwab_stock_price')
    @patch.object(TradingBot, 'fetch_real_stock_price')
    def test_get_stock_price_uses_schwab_first_in_sandbox(self, mock_yf, mock_schwab):
        """Test that Schwab sandbox is tried first when enabled"""
        # Mock successful Schwab fetch
        mock_schwab.return_value = (150.0, 1000000)
        
        result = self.bot.get_stock_price('AAPL')
        
        # Should call Schwab and return result
        mock_schwab.assert_called_once_with('AAPL')
        mock_yf.assert_not_called()  # Should not fallback
        
        self.assertEqual(result, (150.0, 1000000))
    
    @patch.object(TradingBot, 'fetch_schwab_stock_price')
    def test_get_stock_price_no_fallback_to_yfinance_in_sandbox(self, mock_schwab):
        """Test that sandbox mode does NOT fallback to yfinance (fails immediately)"""
        # Mock Schwab failure
        mock_schwab.return_value = None
        
        # Should raise error immediately, not try yfinance fallback
        with self.assertRaises(ValueError) as context:
            self.bot.get_stock_price('AAPL')
        
        error_msg = str(context.exception)
        self.assertIn('CRITICAL ERROR', error_msg)
        self.assertIn('Schwab sandbox API failed', error_msg)
        
        # Verify Schwab was called
        mock_schwab.assert_called_once_with('AAPL')
    
    @patch.object(TradingBot, 'fetch_schwab_stock_price')
    def test_get_stock_price_fallback_to_simulation_raises_error_in_sandbox(self, mock_schwab):
        """Test that sandbox mode raises error instead of falling back to simulation"""
        # Mock Schwab API failure
        mock_schwab.return_value = None
        
        # In sandbox mode, should raise ValueError immediately (no yfinance fallback, no simulation fallback)
        with self.assertRaises(ValueError) as context:
            self.bot.get_stock_price('AAPL', use_random_fallback=True)
        
        # Verify error message explains the issue
        error_msg = str(context.exception)
        self.assertIn('CRITICAL ERROR', error_msg)
        self.assertIn('Schwab sandbox API failed', error_msg)
        self.assertIn('stopped immediately', error_msg)
    
    @patch.object(TradingBot, 'fetch_schwab_stock_price')
    @patch.object(TradingBot, 'fetch_real_stock_price')
    def test_get_stock_price_no_fallback_raises_error(self, mock_yf, mock_schwab):
        """Test that error is raised when fallback is disabled"""
        # Mock all API failures
        mock_schwab.return_value = None
        mock_yf.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.bot.get_stock_price('AAPL', use_random_fallback=False)
        
        # In sandbox mode, error message should mention sandbox requirements
        self.assertIn('sandbox mode', str(context.exception).lower())


@pytest.mark.integration
class TestSchwabTradeExecution(unittest.TestCase):
    """Test trade execution via Schwab sandbox API"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_execute_trade_sandbox_success(self):
        """Test successful trade execution in sandbox mode using OAuth client"""
        # Mock OAuth client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.headers = {'Location': 'https://api.schwabapi.com/trader/v1/accounts/123456/orders/sandbox_12345'}
        mock_response.text = '{"orderId": "sandbox_12345"}'
        mock_response.json.return_value = {"orderId": "sandbox_12345"}
        mock_client.place_order.return_value = mock_response
        
        # Set the mock client on the bot
        self.bot.schwab_client = mock_client
        
        # Mock credential validation
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True):
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['order_id'], 'sandbox_12345')
        self.assertEqual(result['mode'], 'SANDBOX')
        
        # Verify OAuth client was called
        mock_client.place_order.assert_called_once()
    
    def test_execute_trade_sandbox_with_rate_limit(self):
        """Test rate limit handling in sandbox with OAuth client"""
        # Mock OAuth client with rate limit error
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"
        mock_client.place_order.return_value = mock_response
        
        # Set the mock client on the bot
        self.bot.schwab_client = mock_client
        
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True):
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['reason'], 'rate_limit_exceeded')
        self.assertEqual(result['mode'], 'SANDBOX')
    
    def test_execute_trade_oauth_authentication_error(self):
        """Test OAuth authentication error handling (401)"""
        # Mock OAuth client with authentication error
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_client.place_order.return_value = mock_response
        
        # Set the mock client on the bot
        self.bot.schwab_client = mock_client
        
        with patch.object(self.bot, '_validate_live_mode_credentials', return_value=True):
            result = self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['reason'], 'authentication_failed')
        # Check for key phrases in the improved error message
        self.assertIn('OAuth token', result['message'])
        self.assertIn('Solutions:', result['message'])


@pytest.mark.integration
class TestLoggingAndMonitoring(unittest.TestCase):
    """Test enhanced logging and monitoring"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_print_summary_shows_sandbox_mode(self):
        """Test that summary correctly displays sandbox mode"""
        import io
        import sys
        
        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            self.bot.print_summary()
            output = captured_output.getvalue()
            
            # Should show sandbox mode
            self.assertIn('PAPER TRADING', output)
            self.assertIn('Sandbox', output)
        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__
    
    @patch('main.requests.get')
    def test_cache_source_tracking(self, mock_get):
        """Test that cache tracks data source"""
        # Mock Schwab API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'AAPL': {
                'quote': {
                    'lastPrice': 150.0,
                    'totalVolume': 1000000
                }
            }
        }
        mock_get.return_value = mock_response
        
        # Fetch price
        self.bot.fetch_schwab_stock_price('AAPL')
        
        # Check cache includes source
        self.assertIn('AAPL', self.bot.price_cache)
        self.assertIn('source', self.bot.price_cache['AAPL'])
        self.assertIn('schwab', self.bot.price_cache['AAPL']['source'])


@pytest.mark.integration
class TestModeDetection(unittest.TestCase):
    """Test mode detection and configuration"""
    
    def test_paper_mode_with_sandbox(self):
        """Test configuration when paper mode + sandbox enabled"""
        from main import PAPER_TRADING_MODE, SCHWAB_SANDBOX_MODE
        
        # Both should be enabled in our test environment
        self.assertTrue(PAPER_TRADING_MODE)
        self.assertTrue(SCHWAB_SANDBOX_MODE)
    
    def test_execute_trade_paper_mode_logging(self):
        """Test that paper mode shows correct mode in logs"""
        import io
        import sys
        
        bot = TradingBot(total_capital=10000.0)
        
        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            # Execute a paper trade
            bot.execute_trade_paper_mode('AAPL', 'BUY', 150.0, volume=1000000)
            output = captured_output.getvalue()
            
            # Should indicate sandbox mode
            self.assertIn('SANDBOX', output)
        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__


@pytest.mark.integration
class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TradingBot(total_capital=10000.0)
    
    @patch.object(TradingBot, 'fetch_schwab_stock_price')
    def test_sandbox_mode_requires_api(self, mock_schwab):
        """Test that sandbox mode requires API and doesn't fall back to simulation"""
        # Mock Schwab API failure
        mock_schwab.return_value = None
        
        # In sandbox mode, should raise error immediately (no yfinance fallback, no simulation)
        with self.assertRaises(ValueError) as context:
            self.bot.get_stock_price('TEST', use_random_fallback=True)
        
        error_msg = str(context.exception).lower()
        self.assertIn('critical error', error_msg)
        self.assertIn('schwab sandbox api failed', error_msg)
        self.assertIn('stopped immediately', error_msg)
    
    def test_execute_trade_wrapper_still_works(self):
        """Test that execute_trade wrapper routes correctly in sandbox mode"""
        # In sandbox mode, should route to live mode (with sandbox API endpoints)
        # This ensures orders go through the API and are visible in ThinkorSwim
        with patch.object(self.bot, 'execute_trade_live_mode') as mock_live:
            self.bot.execute_trade('AAPL', 'BUY', 150.0, volume=1000000)
            mock_live.assert_called_once()


if __name__ == '__main__':
    # Set up test logging
    logging.basicConfig(level=logging.CRITICAL)  # Suppress logs during testing
    
    # Run tests
    unittest.main(verbosity=2)
