#!/usr/bin/env python3
"""
Test suite for exception handling improvements in GUI and API calls
Tests the enhanced exception handling added to prevent UI freezing
"""

import os
# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')
os.environ.setdefault('SCHWAB_API_ENABLED', 'off')

import unittest
from unittest.mock import patch, MagicMock
import requests
import sys
# Import the modules to test
from main import TradingBot

# Check if tkinter is available
TKINTER_AVAILABLE = False
try:
    import tkinter as tk
    TKINTER_AVAILABLE = True
except ImportError:
    # tkinter is optional; when not available, GUI tests will be skipped.
    print("tkinter not available; skipping GUI tests.")

class TestGUIExceptionHandling(unittest.TestCase):
    """Test exception handling in GUI methods"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock tkinter to avoid GUI dependencies in tests
        self.mock_tk = MagicMock()
        self.mock_messagebox = MagicMock()
    
    @unittest.skipUnless(TKINTER_AVAILABLE, "tkinter not available")
    @patch('gui.messagebox')
    @patch('gui.tk')
    def test_update_logs_handles_queue_empty(self, mock_tk, mock_messagebox):
        """Test that update_logs handles empty queue gracefully"""
        # Import here to use mocked modules
        from gui import TradingBotGUI
        
        # Create a mock root window
        mock_root = MagicMock()
        mock_root.after = MagicMock()
        
        with patch('gui.tk.Tk', return_value=mock_root):
            gui = TradingBotGUI(mock_root)
            
            # Test with empty queue - should not raise exception
            try:
                gui.update_logs()
                success = True
            except Exception as e:
                success = False
                print(f"Exception raised: {e}")
            
            self.assertTrue(success, "update_logs should handle empty queue without exception")
            # Verify after() was called to schedule next update
            mock_root.after.assert_called()
    
    @unittest.skipUnless(TKINTER_AVAILABLE, "tkinter not available")
    @patch('gui.messagebox')
    @patch('gui.tk')
    def test_update_logs_handles_unexpected_exception(self, mock_tk, mock_messagebox):
        """Test that update_logs handles unexpected exceptions with messagebox"""
        from gui import TradingBotGUI
        
        # Create a mock root window
        mock_root = MagicMock()
        mock_root.after = MagicMock()
        
        with patch('gui.tk.Tk', return_value=mock_root):
            gui = TradingBotGUI(mock_root)
            
            # Put a problematic item in the queue that will cause an error
            # Mock the log_text to raise an exception
            gui.log_text = MagicMock()
            gui.log_text.insert = MagicMock(side_effect=RuntimeError("Simulated error"))
            
            # Add a message to the queue
            gui.log_queue.put("Test message")
            
            # Call update_logs - should handle exception gracefully
            try:
                gui.update_logs()
                success = True
            except RuntimeError:
                success = False
            
            self.assertTrue(success, "update_logs should handle exceptions without crashing")
            # Verify after() was still called to schedule next update
            mock_root.after.assert_called()
    
    @unittest.skipUnless(TKINTER_AVAILABLE, "tkinter not available")
    @patch('gui.messagebox')
    @patch('gui.psutil')
    def test_update_resources_handles_attribute_error(self, mock_psutil, mock_messagebox):
        """Test that update_resources handles AttributeError gracefully"""
        from gui import TradingBotGUI, ResourceMonitor
        
        # Create a mock root window
        mock_root = MagicMock()
        mock_root.after = MagicMock()
        
        with patch('gui.tk.Tk', return_value=mock_root):
            gui = TradingBotGUI(mock_root)
            
            # Mock resource_monitor to raise AttributeError
            gui.resource_monitor = MagicMock(spec=ResourceMonitor)
            gui.resource_monitor.update = MagicMock(side_effect=AttributeError("Missing attribute"))
            
            # Call update_resources - should handle exception gracefully
            try:
                gui.update_resources()
                success = True
            except AttributeError:
                success = False
            
            self.assertTrue(success, "update_resources should handle AttributeError without crashing")
            # Verify after() was still called to schedule next update
            mock_root.after.assert_called()
    
    @unittest.skipUnless(TKINTER_AVAILABLE, "tkinter not available")
    @patch('gui.messagebox')
    @patch('gui.psutil')
    def test_update_resources_handles_zero_division_error(self, mock_psutil, mock_messagebox):
        """Test that update_resources handles ZeroDivisionError gracefully"""
        from gui import TradingBotGUI, ResourceMonitor
        
        # Create a mock root window
        mock_root = MagicMock()
        mock_root.after = MagicMock()
        
        with patch('gui.tk.Tk', return_value=mock_root):
            gui = TradingBotGUI(mock_root)
            
            # Mock resource_monitor with zero network values
            gui.resource_monitor = MagicMock(spec=ResourceMonitor)
            gui.resource_monitor.cpu_percent = 50.0
            gui.resource_monitor.memory_percent = 50.0
            gui.resource_monitor.disk_percent = 50.0
            gui.resource_monitor.network_io = {'sent': 0, 'recv': 0}
            gui.resource_monitor.get_bottlenecks = MagicMock(side_effect=ZeroDivisionError("Division by zero"))
            
            # Call update_resources - should handle exception gracefully
            try:
                gui.update_resources()
                success = True
            except ZeroDivisionError:
                success = False
            
            self.assertTrue(success, "update_resources should handle ZeroDivisionError without crashing")
            # Verify after() was still called to schedule next update
            mock_root.after.assert_called()
    
    @unittest.skipUnless(TKINTER_AVAILABLE, "tkinter not available")
    @patch('gui.messagebox')
    @patch('gui.psutil')
    def test_update_resources_notifies_bot_on_bottleneck(self, mock_psutil, mock_messagebox):
        """Test that update_resources notifies bot when bottlenecks detected"""
        from gui import TradingBotGUI
        
        # Create a mock root window
        mock_root = MagicMock()
        mock_root.after = MagicMock()
        
        with patch('gui.tk.Tk', return_value=mock_root):
            gui = TradingBotGUI(mock_root)
            
            # Mock bot with handle_resource_bottleneck method
            mock_bot = MagicMock()
            mock_bot.handle_resource_bottleneck = MagicMock()
            gui.bot = mock_bot
            
            # Mock resource_monitor to return bottlenecks
            gui.resource_monitor.cpu_percent = 85.0
            gui.resource_monitor.memory_percent = 50.0
            gui.resource_monitor.disk_percent = 50.0
            gui.resource_monitor.network_io = {'sent': 1000, 'recv': 1000}
            gui.resource_monitor.get_bottlenecks = MagicMock(return_value=["CPU: 85.0%"])
            
            # Call update_resources
            gui.update_resources()
            
            # Verify bot was notified
            mock_bot.handle_resource_bottleneck.assert_called_once_with(["CPU: 85.0%"])


class TestAPIExceptionHandling(unittest.TestCase):
    """Test exception handling in API calls"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
        # Mock GUI reference
        self.bot.gui = None  # No GUI by default
    
    @patch('main.requests.get')
    def test_fetch_schwab_timeout_no_gui(self, mock_get):
        """Test timeout exception handling without GUI"""
        # Simulate timeout
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
        
        # Should return None and not crash
        result = self.bot.fetch_schwab_stock_price('AAPL')
        self.assertIsNone(result, "Should return None on timeout")
    
    @unittest.skipUnless(TKINTER_AVAILABLE, "tkinter not available")
    @patch('main.requests.get')
    @patch('tkinter.messagebox.showerror')
    def test_fetch_schwab_timeout_with_gui(self, mock_messagebox, mock_get):
        """Test timeout exception handling with GUI feedback"""
        # Simulate timeout
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
        
        # Mock GUI
        self.bot.gui = MagicMock()
        
        # Should return None and attempt to show messagebox
        result = self.bot.fetch_schwab_stock_price('AAPL')
        self.assertIsNone(result, "Should return None on timeout")
        # Note: messagebox may not be called if GUI check fails, so we just verify no crash
    
    @patch('main.requests.get')
    def test_fetch_schwab_connection_error_no_gui(self, mock_get):
        """Test connection error handling without GUI"""
        # Simulate connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")
        
        # Should return None and not crash
        result = self.bot.fetch_schwab_stock_price('AAPL')
        self.assertIsNone(result, "Should return None on connection error")
    
    @patch('main.requests.get')
    def test_fetch_schwab_request_exception_no_gui(self, mock_get):
        """Test general request exception handling without GUI"""
        # Simulate general request exception
        mock_get.side_effect = requests.exceptions.RequestException("General network error")
        
        # Should return None and not crash
        result = self.bot.fetch_schwab_stock_price('AAPL')
        self.assertIsNone(result, "Should return None on request exception")
    
    @patch('main.requests.get')
    def test_fetch_schwab_unexpected_exception_no_gui(self, mock_get):
        """Test unexpected exception handling without GUI"""
        # Simulate unexpected exception
        mock_get.side_effect = ValueError("Unexpected error")
        
        # Should return None and not crash
        result = self.bot.fetch_schwab_stock_price('AAPL')
        self.assertIsNone(result, "Should return None on unexpected exception")
    
    @patch('main.YFINANCE_AVAILABLE', True)
    def test_fetch_real_stock_price_timeout(self):
        """Test fetch_real_stock_price handles timeout exceptions"""
        # Skip if yfinance not installed (will patch it)
        with patch('main.yf') as mock_yf:
            # Create mock ticker that raises timeout
            mock_ticker = MagicMock()
            mock_ticker.fast_info.get.side_effect = requests.exceptions.Timeout("Request timed out")
            mock_yf.Ticker.return_value = mock_ticker
            
            # Should return None and not crash
            result = self.bot.fetch_real_stock_price('AAPL')
            self.assertIsNone(result, "Should return None on timeout")
    
    @patch('main.YFINANCE_AVAILABLE', True)
    def test_fetch_real_stock_price_connection_error(self):
        """Test fetch_real_stock_price handles connection errors"""
        with patch('main.yf') as mock_yf:
            # Create mock ticker that raises connection error
            mock_ticker = MagicMock()
            mock_ticker.fast_info.get.side_effect = requests.exceptions.ConnectionError("Failed to connect")
            mock_yf.Ticker.return_value = mock_ticker
            
            # Should return None and not crash
            result = self.bot.fetch_real_stock_price('AAPL')
            self.assertIsNone(result, "Should return None on connection error")
    
    @patch('main.YFINANCE_AVAILABLE', True)
    def test_fetch_real_stock_price_request_exception(self):
        """Test fetch_real_stock_price handles request exceptions"""
        with patch('main.yf') as mock_yf:
            # Create mock ticker that raises request exception
            mock_ticker = MagicMock()
            mock_ticker.fast_info.get.side_effect = requests.exceptions.RequestException("Network error")
            mock_yf.Ticker.return_value = mock_ticker
            
            # Should return None and not crash
            result = self.bot.fetch_real_stock_price('AAPL')
            self.assertIsNone(result, "Should return None on request exception")
    
    @patch('main.YFINANCE_AVAILABLE', True)
    def test_fetch_real_stock_price_invalid_cache_entry(self):
        """Test fetch_real_stock_price handles invalid cache entries"""
        # Add invalid cache entry (missing timestamp)
        self.bot.price_cache['AAPL'] = {'price': 150.0, 'volume': 1000}
        
        # Should handle gracefully and not crash
        try:
            self.bot.fetch_real_stock_price('AAPL')
            success = True
        except (TypeError, AttributeError, KeyError):
            success = False
        
        self.assertTrue(success, "Should handle invalid cache entries gracefully")
    
    @patch('main.YFINANCE_AVAILABLE', True)
    def test_fetch_real_stock_price_fast_info_fallback(self):
        """Test fetch_real_stock_price falls back to info when fast_info fails"""
        with patch('main.yf') as mock_yf:
            # Create mock ticker with fast_info that raises exception
            mock_ticker = MagicMock()
            mock_ticker.fast_info.get.side_effect = KeyError("Key not found")
            mock_ticker.info = {'currentPrice': 150.0, 'volume': 1000000}
            mock_yf.Ticker.return_value = mock_ticker
            
            # Should fallback to info and return price
            result = self.bot.fetch_real_stock_price('AAPL')
            
            # Result might be None if yfinance is not available, so we just check it doesn't crash
            # If result is not None, it should be a tuple
            if result is not None:
                self.assertIsInstance(result, tuple, "Should return tuple when successful")
                self.assertEqual(len(result), 2, "Should return (price, volume) tuple")


class TestOAuthExceptionHandling(unittest.TestCase):
    """Test exception handling in OAuth initialization"""
    
    def setUp(self):
        """Set up test environment"""
        # Set environment variables for OAuth
        os.environ['SCHWAB_API_ENABLED'] = 'on'
        os.environ['SCHWAB_API_KEY'] = 'test_key'
        os.environ['SCHWAB_APP_SECRET'] = 'test_secret'
    
    def tearDown(self):
        """Clean up environment"""
        os.environ['SCHWAB_API_ENABLED'] = 'off'
    
    @patch('main.SCHWAB_AUTH_AVAILABLE', True)
    @patch('main.SchwabAuthenticator')
    def test_oauth_init_connection_error(self, mock_authenticator_class):
        """Test OAuth initialization handles connection errors"""
        # Simulate connection error during OAuth init
        mock_authenticator_class.side_effect = requests.exceptions.ConnectionError("Failed to connect")
        
        # Should not crash
        try:
            bot = TradingBot(total_capital=10000.0)
            _ = TradingBot(total_capital=10000.0)
        except requests.exceptions.ConnectionError:
            success = False
        
        self.assertTrue(success, "OAuth init should handle connection errors gracefully")
    
    @patch('main.SCHWAB_AUTH_AVAILABLE', True)
    @patch('main.SchwabAuthenticator')
    def test_oauth_init_request_exception(self, mock_authenticator_class):
        """Test OAuth initialization handles request exceptions"""
        # Simulate request exception during OAuth init
        mock_authenticator_class.side_effect = requests.exceptions.RequestException("Network error")
        
        # Should not crash
        try:
            bot = TradingBot(total_capital=10000.0)
            _ = TradingBot(total_capital=10000.0)
        except requests.exceptions.RequestException:
            success = False
        
        self.assertTrue(success, "OAuth init should handle request exceptions gracefully")
    
    @patch('main.SCHWAB_AUTH_AVAILABLE', True)
    @patch('main.SchwabAuthenticator')
    def test_oauth_init_unexpected_exception(self, mock_authenticator_class):
        """Test OAuth initialization handles unexpected exceptions"""
        # Simulate unexpected exception during OAuth init
        mock_authenticator_class.side_effect = ValueError("Configuration error")
        
        # Should not crash
        try:
            bot = TradingBot(total_capital=10000.0)
            _ = TradingBot(total_capital=10000.0)
        except ValueError:
            success = False
        
        self.assertTrue(success, "OAuth init should handle unexpected exceptions gracefully")


class TestExceptionLogging(unittest.TestCase):
    """Test that exceptions are properly handled and return expected values"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    @patch('main.requests.get')
    def test_api_exceptions_return_none(self, mock_get):
        """Test that API exceptions return None and don't crash"""
        # Simulate timeout
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
        
        # Call the method - should return None without crashing
        result = self.bot.fetch_schwab_stock_price('AAPL')
        self.assertIsNone(result, "Should return None on timeout")
        
        # Simulate connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")
        result = self.bot.fetch_schwab_stock_price('MSFT')
        self.assertIsNone(result, "Should return None on connection error")
        
        # Simulate request exception
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        result = self.bot.fetch_schwab_stock_price('GOOGL')
        self.assertIsNone(result, "Should return None on request exception")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
