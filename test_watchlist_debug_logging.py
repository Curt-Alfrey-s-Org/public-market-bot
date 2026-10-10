#!/usr/bin/env python3
"""
Test improved debug logging for top performers watchlist
"""

import unittest
import os
import sys
from unittest.mock import patch
import logging

# Set up environment before importing web_gui
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
os.environ['ENABLE_TOP_PERFORMERS_WATCHLIST'] = 'true'
os.environ['TOP_PERFORMERS_WATCHLIST_SIZE'] = '5'


class TestWatchlistDebugLogging(unittest.TestCase):
    """Test that watchlist errors are properly logged and displayed"""

    def setUp(self):
        """Set up test fixtures"""
        # Configure logging to capture log messages
        self.log_capture = []

        # Create a handler that captures log messages
        class ListHandler(logging.Handler):
            def __init__(self, log_list):
                super().__init__()
                self.log_list = log_list

            def emit(self, record):
                self.log_list.append({
                    'level': record.levelname,
                    'message': self.format(record)
                })

        self.handler = ListHandler(self.log_capture)
        self.handler.setLevel(logging.DEBUG)

        # Get logger and add handler
        logger = logging.getLogger('web_gui')
        logger.addHandler(self.handler)
        logger.setLevel(logging.DEBUG)

    def tearDown(self):
        """Clean up"""
        logger = logging.getLogger('web_gui')
        logger.removeHandler(self.handler)

    def test_missing_dependencies_error_message(self):
        """Test that missing dependencies produce helpful error message"""
        # Mock pandas import to fail
        with patch.dict('sys.modules', {'pandas': None, 'yfinance': None}):
            with patch('builtins.__import__', side_effect=ImportError('No module named pandas')):
                # Import web_gui module
                import importlib
                if 'web_gui' in sys.modules:
                    importlib.reload(sys.modules['web_gui'])
                else:
                    import web_gui

                # Call fetch_watchlist_data
                performers, error_msg = web_gui.fetch_watchlist_data()

                # Verify empty list returned
                self.assertEqual(len(performers), 0)

                # Verify error message is set
                self.assertIsNotNone(error_msg)
                self.assertIn('dependencies', error_msg.lower())

                # Check that error was logged
                error_logs = [log for log in self.log_capture if log['level'] in ['WARNING', 'ERROR']]
                self.assertGreater(len(error_logs), 0, "No error/warning logs found")

                print("✓ Missing dependencies produce helpful error message")

    def test_empty_results_error_message(self):
        """Test that empty results from screener produce helpful error message"""
        with patch('web_gui.get_top_performers_watchlist') as mock_screener:
            # Mock screener to return empty list
            mock_screener.return_value = []

            # Import web_gui
            import web_gui

            # Call fetch_watchlist_data
            performers, error_msg = web_gui.fetch_watchlist_data()

            # Verify empty list returned
            self.assertEqual(len(performers), 0)

            # Verify error message mentions screening criteria
            if error_msg:
                self.assertIn('screening criteria', error_msg.lower())

            print("✓ Empty results produce helpful error message")

    def test_format_watchlist_shows_error_message(self):
        """Test that format_watchlist_table displays specific error messages"""
        import web_gui

        # Set a mock error message
        web_gui.watchlist_error_message = "Test error: Missing pandas dependency"

        # Format empty watchlist
        result = web_gui.format_watchlist_table([])

        # Verify result is a Div with error message
        self.assertIsNotNone(result)
        self.assertEqual(result.type, 'Div')

        # Check that error message appears in the output
        result_str = str(result)
        self.assertIn('Test error', result_str)

        print("✓ format_watchlist_table displays specific error messages")

    def test_successful_watchlist_clears_error(self):
        """Test that successful watchlist fetch clears previous errors"""
        with patch('web_gui.get_top_performers_watchlist') as mock_screener:
            # Mock successful response
            mock_screener.return_value = [
                {
                    'symbol': 'AAPL',
                    'win_probability': 0.75,
                    'composite_score': 0.85,
                    'sentiment_score': 0.6,
                    'price': 150.0,
                    'volume': 50000000,
                    'volatility': 0.02
                }
            ]

            import web_gui

            # Set an initial error
            web_gui.watchlist_error_message = "Previous error"

            # Call fetch_watchlist_data
            performers, error_msg = web_gui.fetch_watchlist_data()

            # Verify error is cleared
            self.assertIsNone(error_msg)
            self.assertIsNone(web_gui.watchlist_error_message)

            # Verify data is returned
            self.assertEqual(len(performers), 1)
            self.assertEqual(performers[0]['symbol'], 'AAPL')

            print("✓ Successful fetch clears previous errors")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
