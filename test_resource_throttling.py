#!/usr/bin/env python3
"""
Test Resource Throttling functionality
"""

import unittest
import time
import os
from unittest.mock import patch, MagicMock
from main import ResourceThrottler, TradingBot


class TestResourceThrottler(unittest.TestCase):
    """Test ResourceThrottler class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock psutil availability
        self.psutil_available_patcher = patch('main.PSUTIL_AVAILABLE', True)
        self.psutil_available_patcher.start()
    
    def tearDown(self):
        """Clean up after tests"""
        self.psutil_available_patcher.stop()
    
    @patch('main.psutil')
    def test_throttler_enabled(self, mock_psutil):
        """Test that throttler can be enabled"""
        throttler = ResourceThrottler(enabled=True)
        self.assertTrue(throttler.enabled)
    
    def test_throttler_disabled(self):
        """Test that throttler can be disabled"""
        throttler = ResourceThrottler(enabled=False)
        self.assertFalse(throttler.enabled)
    
    @patch('main.psutil')
    @patch('main.time')
    def test_check_resources_within_limits(self, mock_time, mock_psutil):
        """Test resource check when within limits"""
        # Mock resource usage below thresholds
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0)
        mock_psutil.disk_usage.return_value = MagicMock(percent=60.0)
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=1000)
        mock_time.time.return_value = 1.0
        
        throttler = ResourceThrottler(enabled=True)
        throttler.max_cpu_percent = 75.0
        throttler.max_memory_percent = 75.0
        throttler.max_disk_percent = 90.0
        throttler.max_network_mbps = 100.0
        
        is_ok, message = throttler.check_resources()
        
        self.assertTrue(is_ok)
        self.assertIn("Resources OK", message)
        self.assertIn("50.0%", message)
    
    @patch('main.psutil')
    @patch('main.time')
    def test_check_resources_cpu_exceeds(self, mock_time, mock_psutil):
        """Test resource check when CPU exceeds threshold"""
        # Mock CPU usage above threshold
        mock_psutil.cpu_percent.return_value = 80.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0)
        mock_psutil.disk_usage.return_value = MagicMock(percent=60.0)
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=1000)
        mock_time.time.return_value = 1.0
        
        throttler = ResourceThrottler(enabled=True)
        throttler.max_cpu_percent = 75.0
        throttler.max_memory_percent = 75.0
        throttler.max_disk_percent = 90.0
        throttler.max_network_mbps = 100.0
        
        is_ok, message = throttler.check_resources()
        
        self.assertFalse(is_ok)
        self.assertIn("CPU usage", message)
        self.assertIn("80.0%", message)
        self.assertIn("exceeds", message)
        self.assertEqual(throttler.throttle_count, 1)
    
    @patch('main.psutil')
    @patch('main.time')
    def test_check_resources_memory_exceeds(self, mock_time, mock_psutil):
        """Test resource check when memory exceeds threshold"""
        # Mock memory usage above threshold
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=80.0)
        mock_psutil.disk_usage.return_value = MagicMock(percent=60.0)
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=1000)
        mock_time.time.return_value = 1.0
        
        throttler = ResourceThrottler(enabled=True)
        throttler.max_cpu_percent = 75.0
        throttler.max_memory_percent = 75.0
        throttler.max_disk_percent = 90.0
        throttler.max_network_mbps = 100.0
        
        is_ok, message = throttler.check_resources()
        
        self.assertFalse(is_ok)
        self.assertIn("Memory usage", message)
        self.assertIn("80.0%", message)
        self.assertIn("exceeds", message)
        self.assertEqual(throttler.throttle_count, 1)
    
    @patch('main.psutil')
    @patch('main.time')
    def test_check_resources_disk_exceeds(self, mock_time, mock_psutil):
        """Test resource check when disk exceeds threshold"""
        # Mock disk usage above threshold
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0)
        mock_psutil.disk_usage.return_value = MagicMock(percent=95.0)
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=1000)
        mock_time.time.return_value = 1.0
        
        throttler = ResourceThrottler(enabled=True)
        throttler.max_cpu_percent = 75.0
        throttler.max_memory_percent = 75.0
        throttler.max_disk_percent = 90.0
        throttler.max_network_mbps = 100.0
        
        is_ok, message = throttler.check_resources()
        
        self.assertFalse(is_ok)
        self.assertIn("Disk usage", message)
        self.assertIn("95.0%", message)
        self.assertIn("exceeds", message)
        self.assertEqual(throttler.throttle_count, 1)
    
    @patch('main.psutil')
    @patch('main.time')
    def test_check_resources_network_exceeds(self, mock_time, mock_psutil):
        """Test resource check when network throughput exceeds threshold"""
        # Mock high network throughput
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0)
        mock_psutil.disk_usage.return_value = MagicMock(percent=60.0)
        
        # First call - establish baseline
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=0, bytes_recv=0)
        mock_time.time.return_value = 0.0
        
        throttler = ResourceThrottler(enabled=True)
        throttler.max_cpu_percent = 75.0
        throttler.max_memory_percent = 75.0
        throttler.max_disk_percent = 90.0
        throttler.max_network_mbps = 100.0
        
        # First check - establish baseline
        throttler.check_resources()
        
        # Second call - high network throughput
        # 200 MB/s = 200 * 1024 * 1024 bytes/s
        # In 1 second, that's 209715200 bytes
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=104857600, bytes_recv=104857600)
        mock_time.time.return_value = 1.0
        
        is_ok, message = throttler.check_resources()
        
        self.assertFalse(is_ok)
        self.assertIn("Network throughput", message)
        self.assertIn("exceeds", message)
        self.assertEqual(throttler.throttle_count, 1)
    
    @patch('main.time')
    @patch('main.logger')
    def test_apply_throttle(self, mock_logger, mock_time):
        """Test that throttle delay is applied"""
        throttler = ResourceThrottler(enabled=True)
        throttler.throttle_delay = 5
        
        throttler.apply_throttle("Test reason")
        
        # Verify sleep was called with correct delay
        mock_time.sleep.assert_called_once_with(5)
        
        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        self.assertIn("THROTTLE", call_args)
        self.assertIn("Test reason", call_args)
    
    def test_get_stats(self):
        """Test getting throttler statistics"""
        throttler = ResourceThrottler(enabled=True)
        throttler.max_cpu_percent = 75.0
        throttler.max_memory_percent = 80.0
        throttler.max_disk_percent = 90.0
        throttler.max_network_mbps = 100.0
        throttler.throttle_delay = 10
        throttler.throttle_count = 5
        
        stats = throttler.get_stats()
        
        self.assertTrue(stats['enabled'])
        self.assertEqual(stats['throttle_count'], 5)
        self.assertEqual(stats['max_cpu_percent'], 75.0)
        self.assertEqual(stats['max_memory_percent'], 80.0)
        self.assertEqual(stats['max_disk_percent'], 90.0)
        self.assertEqual(stats['max_network_mbps'], 100.0)
        self.assertEqual(stats['throttle_delay'], 10)
    
    def test_check_resources_when_disabled(self):
        """Test that resource check always passes when disabled"""
        throttler = ResourceThrottler(enabled=False)
        
        is_ok, message = throttler.check_resources()
        
        self.assertTrue(is_ok)
        self.assertEqual(message, "Throttling disabled")
    
    @patch('main.psutil')
    @patch('main.time')
    def test_multiple_throttle_events(self, mock_time, mock_psutil):
        """Test that throttle count increments correctly"""
        # Mock high resource usage
        mock_psutil.cpu_percent.return_value = 85.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=85.0)
        mock_psutil.disk_usage.return_value = MagicMock(percent=60.0)
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=1000)
        mock_time.time.return_value = 1.0
        
        throttler = ResourceThrottler(enabled=True)
        throttler.max_cpu_percent = 75.0
        throttler.max_memory_percent = 75.0
        throttler.max_disk_percent = 90.0
        throttler.max_network_mbps = 100.0
        
        # Trigger multiple checks
        for i in range(5):
            is_ok, message = throttler.check_resources()
            self.assertFalse(is_ok)
        
        # Verify counter incremented
        self.assertEqual(throttler.throttle_count, 5)


class TestResourceThrottlerIntegration(unittest.TestCase):
    """Test ResourceThrottler integration with TradingBot methods"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Set environment variables for paper trading mode
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['ENABLE_PDT_RULES'] = 'false'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
        os.environ['BOT_ENABLE_THROTTLING'] = 'true'
        
        # Mock psutil availability
        self.psutil_available_patcher = patch('main.PSUTIL_AVAILABLE', True)
        self.psutil_available_patcher.start()
    
    def tearDown(self):
        """Clean up after tests"""
        self.psutil_available_patcher.stop()
    
    @patch('main.psutil')
    @patch('main.time')
    def test_throttle_on_optimize_parameters_ml(self, mock_time, mock_psutil):
        """Test that optimize_parameters_ml checks throttling"""
        # Mock high CPU usage
        mock_psutil.cpu_percent.return_value = 85.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0)
        mock_psutil.disk_usage.return_value = MagicMock(percent=60.0)
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=1000)
        mock_time.time.return_value = 1.0
        
        bot = TradingBot(total_capital=10000.0)
        bot.throttler.max_cpu_percent = 75.0
        bot.throttler.throttle_delay = 0.1  # Small delay for testing
        
        # Call optimize_parameters_ml (will fail early but should check throttling)
        bot.optimize_parameters_ml()
        
        # Verify throttle was triggered (count incremented)
        self.assertGreater(bot.throttler.throttle_count, 0)
    
    @patch('main.psutil')
    @patch('main.time')
    @patch('main.requests.post')
    def test_throttle_on_send_track_record_to_ai(self, mock_post, mock_time, mock_psutil):
        """Test that send_track_record_to_ai checks throttling"""
        # Mock high memory usage
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=85.0)
        mock_psutil.disk_usage.return_value = MagicMock(percent=60.0)
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=1000)
        mock_time.time.return_value = 1.0
        
        bot = TradingBot(total_capital=10000.0)
        bot.throttler.max_memory_percent = 75.0
        bot.throttler.throttle_delay = 0.1  # Small delay for testing
        
        # Call send_track_record_to_ai (will fail but should check throttling)
        bot.send_track_record_to_ai()
        
        # Verify throttle was triggered
        self.assertGreater(bot.throttler.throttle_count, 0)
    
    @patch('main.psutil')
    @patch('main.time')
    def test_throttle_on_load_scan_symbols(self, mock_time, mock_psutil):
        """Test that load_scan_symbols checks throttling"""
        # Mock high disk usage
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0)
        mock_psutil.disk_usage.return_value = MagicMock(percent=95.0)
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=1000)
        mock_time.time.return_value = 1.0
        
        bot = TradingBot(total_capital=10000.0)
        bot.throttler.max_disk_percent = 90.0
        bot.throttler.throttle_delay = 0.1  # Small delay for testing
        
        # Call load_scan_symbols
        bot.load_scan_symbols(use_screener=False)
        
        # Verify throttle was triggered
        self.assertGreater(bot.throttler.throttle_count, 0)
    
    @patch('main.psutil')
    @patch('main.time')
    @patch('main.YFINANCE_AVAILABLE', True)
    @patch('main.yf')
    def test_throttle_on_fetch_real_stock_price(self, mock_yf, mock_time, mock_psutil):
        """Test that fetch_real_stock_price checks throttling"""
        # Mock high disk usage (easier to test than network)
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0)
        mock_psutil.disk_usage.return_value = MagicMock(percent=95.0)
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=1000)
        mock_time.time.return_value = 1.0
        
        bot = TradingBot(total_capital=10000.0)
        bot.throttler.max_disk_percent = 90.0
        bot.throttler.throttle_delay = 0.1  # Small delay for testing
        
        # Mock yfinance ticker
        mock_ticker = MagicMock()
        mock_ticker.fast_info.get.side_effect = lambda key: {'lastPrice': 150.0, 'lastVolume': 1000000}.get(key)
        mock_yf.Ticker.return_value = mock_ticker
        
        # Call fetch_real_stock_price
        bot.fetch_real_stock_price('AAPL')
        
        # Verify throttle was triggered (disk exceeded)
        self.assertGreater(bot.throttler.throttle_count, 0)
    
    @patch('main.psutil')
    @patch('main.time')
    def test_throttle_on_search_stocks(self, mock_time, mock_psutil):
        """Test that search_stocks checks throttling"""
        # Mock high CPU usage
        mock_psutil.cpu_percent.return_value = 85.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0)
        mock_psutil.disk_usage.return_value = MagicMock(percent=60.0)
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=1000)
        mock_time.time.return_value = 1.0
        
        bot = TradingBot(total_capital=10000.0)
        bot.throttler.max_cpu_percent = 75.0
        bot.throttler.throttle_delay = 0.1  # Small delay for testing
        
        # Call search_stocks with a small list
        bot.search_stocks(symbols=['AAPL'], use_screener=False, max_stocks=1)
        
        # Verify throttle was triggered
        self.assertGreater(bot.throttler.throttle_count, 0)
    
    @patch('main.psutil')
    @patch('main.time')
    def test_throttle_on_filter_stock(self, mock_time, mock_psutil):
        """Test that filter_stock checks throttling"""
        # Mock high CPU usage
        mock_psutil.cpu_percent.return_value = 85.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0)
        mock_psutil.disk_usage.return_value = MagicMock(percent=60.0)
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=1000)
        mock_time.time.return_value = 1.0
        
        bot = TradingBot(total_capital=10000.0)
        bot.throttler.max_cpu_percent = 75.0
        bot.throttler.throttle_delay = 0.1  # Small delay for testing
        
        # Call filter_stock
        bot.filter_stock('AAPL', 150.0, 1000000)
        
        # Verify throttle was triggered
        self.assertGreater(bot.throttler.throttle_count, 0)
    
    @patch('main.psutil')
    @patch('main.time')
    def test_no_throttle_when_resources_ok(self, mock_time, mock_psutil):
        """Test that throttling does not occur when resources are within limits"""
        # Mock low resource usage
        mock_psutil.cpu_percent.return_value = 30.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=40.0)
        mock_psutil.disk_usage.return_value = MagicMock(percent=50.0)
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=1000)
        mock_time.time.return_value = 1.0
        
        bot = TradingBot(total_capital=10000.0)
        bot.throttler.max_cpu_percent = 75.0
        bot.throttler.max_memory_percent = 75.0
        bot.throttler.throttle_delay = 0.1  # Small delay for testing
        
        # Call filter_stock
        bot.filter_stock('AAPL', 150.0, 1000000)
        
        # Verify no throttle was triggered
        self.assertEqual(bot.throttler.throttle_count, 0)


if __name__ == '__main__':
    unittest.main()
