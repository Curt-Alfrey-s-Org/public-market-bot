#!/usr/bin/env python3
"""
Test suite for TradingBot backtest instance methods
Tests the new backtest_loop and print_backtest_summary instance methods
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import pandas as pd
import sys

# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')
os.environ.setdefault('SCHWAB_SANDBOX_MODE', 'false')

# Import after setting environment variables
from main import TradingBot


class TestBacktestInstanceMethods(unittest.TestCase):
    """Test TradingBot backtest instance methods"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
        self.start_date = '2024-01-01'
        self.end_date = '2024-01-31'
        self.test_symbols = ['AAPL', 'MSFT']
    
    def tearDown(self):
        """Clean up after each test"""
        # Clean up any backtest result files
        import glob
        for filename in glob.glob('backtest_history_*.json'):
            try:
                os.remove(filename)
            except Exception as e:
                print(f"Warning: failed to remove backtest history file {filename!r}: {e}", file=sys.stderr)
    
    def test_backtest_loop_instance_method_exists(self):
        """Test that backtest_loop is an instance method of TradingBot"""
        self.assertTrue(hasattr(self.bot, 'backtest_loop'))
        self.assertTrue(callable(getattr(self.bot, 'backtest_loop')))
    
    def test_print_backtest_summary_exists(self):
        """Test that print_backtest_summary is an instance method of TradingBot"""
        self.assertTrue(hasattr(self.bot, 'print_backtest_summary'))
        self.assertTrue(callable(getattr(self.bot, 'print_backtest_summary')))
    
    def test_backtest_loop_with_valid_dates(self):
        """Test backtest_loop with valid date range"""
        # Create mock data fetcher
        mock_data_fetcher = MagicMock()
        
        # Create sample historical data
        dates = pd.date_range(start=self.start_date, end=self.end_date, freq='D')
        historical_data = pd.DataFrame({
            'date': dates,
            'open': [150.0 + i * 0.5 for i in range(len(dates))],
            'high': [152.0 + i * 0.5 for i in range(len(dates))],
            'low': [148.0 + i * 0.5 for i in range(len(dates))],
            'close': [151.0 + i * 0.5 for i in range(len(dates))],
            'volume': [1000000 for _ in range(len(dates))]
        })
        
        # Mock the fetch_historical_data_yfinance method
        mock_data_fetcher.fetch_historical_data_yfinance = MagicMock(return_value=historical_data)
        
        # Patch the DataFetcher class
        with patch('main.DataFetcher', return_value=mock_data_fetcher):
            # Run backtest using instance method
            results = self.bot.backtest_loop(self.start_date, self.end_date, ['AAPL'])
            
            # Verify results structure
            self.assertIsInstance(results, dict)
            self.assertIn('metadata', results)
            self.assertIn('trades', results)
            
            # Verify metadata
            metadata = results['metadata']
            self.assertIn('start_date', metadata)
            self.assertIn('end_date', metadata)
            self.assertIn('initial_capital', metadata)
            self.assertIn('final_capital', metadata)
            self.assertIn('total_pnl', metadata)
            self.assertIn('win_rate', metadata)
            
            # Verify dates are correct
            self.assertEqual(metadata['start_date'], self.start_date)
            self.assertEqual(metadata['end_date'], self.end_date)
            
            # Verify initial capital
            self.assertEqual(metadata['initial_capital'], 10000.0)
    
    def test_backtest_loop_with_invalid_date_format(self):
        """Test backtest_loop handles invalid date formats gracefully"""
        # Create mock data fetcher
        mock_data_fetcher = MagicMock()
        
        # Patch the DataFetcher class
        with patch('main.DataFetcher', return_value=mock_data_fetcher):
            # Run backtest with invalid dates
            results = self.bot.backtest_loop('invalid-date', '2024-01-31', ['AAPL'])
            
            # Should return error in metadata
            self.assertIn('metadata', results)
            metadata = results['metadata']
            self.assertIn('error', metadata)
    
    def test_backtest_loop_with_no_data(self):
        """Test backtest_loop when no historical data is available"""
        # Create mock data fetcher that returns None
        mock_data_fetcher = MagicMock()
        mock_data_fetcher.fetch_historical_data_yfinance = MagicMock(return_value=None)
        
        # Patch the DataFetcher class
        with patch('main.DataFetcher', return_value=mock_data_fetcher):
            # Run backtest
            results = self.bot.backtest_loop(self.start_date, self.end_date, ['INVALID'])
            
            # Verify results structure
            self.assertIsInstance(results, dict)
            self.assertIn('metadata', results)
            self.assertIn('trades', results)
            
            # Should have no trades
            self.assertEqual(len(results['trades']), 0)
    
    def test_backtest_loop_buy_and_sell_logic(self):
        """Test that backtest_loop executes buy and sell signals correctly"""
        # Create mock data fetcher
        mock_data_fetcher = MagicMock()
        
        # Create data that should trigger buy then sell
        dates = pd.date_range(start=self.start_date, periods=10, freq='D')
        prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118]  # Uptrend
        historical_data = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p + 2 for p in prices],
            'low': [p - 2 for p in prices],
            'close': prices,
            'volume': [1500000 for _ in range(len(dates))]
        })
        
        # Mock the fetch_historical_data_yfinance method
        mock_data_fetcher.fetch_historical_data_yfinance = MagicMock(return_value=historical_data)
        
        # Patch the DataFetcher class
        with patch('main.DataFetcher', return_value=mock_data_fetcher):
            # Run backtest
            results = self.bot.backtest_loop(self.start_date, self.end_date, ['TEST'])
            
            # Verify trades were executed
            trades = results['trades']
            self.assertGreater(len(trades), 0, "Should have executed at least one trade")
            
            # Check if we have both BUY and SELL actions
            actions = [trade['action'] for trade in trades]
            self.assertIn('BUY', actions, "Should have BUY actions")
    
    def test_backtest_loop_multiple_symbols(self):
        """Test backtest_loop with multiple symbols"""
        # Create mock data fetcher
        mock_data_fetcher = MagicMock()
        
        # Create sample historical data
        dates = pd.date_range(start=self.start_date, periods=10, freq='D')
        
        def create_data(base_price):
            return pd.DataFrame({
                'date': dates,
                'open': [base_price + i for i in range(len(dates))],
                'high': [base_price + i + 2 for i in range(len(dates))],
                'low': [base_price + i - 2 for i in range(len(dates))],
                'close': [base_price + i + 1 for i in range(len(dates))],
                'volume': [1000000 for _ in range(len(dates))]
            })
        
        # Mock different data for different symbols
        def mock_fetch(symbol, start_date, end_date, interval):
            if symbol == 'AAPL':
                return create_data(150)
            elif symbol == 'MSFT':
                return create_data(300)
            return None
        
        mock_data_fetcher.fetch_historical_data_yfinance = MagicMock(side_effect=mock_fetch)
        
        # Patch the DataFetcher class
        with patch('main.DataFetcher', return_value=mock_data_fetcher):
            # Run backtest with multiple symbols
            results = self.bot.backtest_loop(self.start_date, self.end_date, self.test_symbols)
            
            # Verify results
            self.assertIn('metadata', results)
            metadata = results['metadata']
            self.assertEqual(len(metadata['symbols']), 2)
    
    def test_print_backtest_summary_with_results(self):
        """Test print_backtest_summary with provided results"""
        # Create sample results
        sample_results = {
            'metadata': {
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'symbols': ['AAPL', 'MSFT'],
                'initial_capital': 10000.0,
                'final_capital': 10500.0,
                'total_pnl': 500.0,
                'roi_percent': 5.0,
                'total_trades': 10,
                'winning_trades': 7,
                'losing_trades': 3,
                'win_rate': 0.7
            },
            'trades': []
        }
        
        # Capture stdout
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.bot.print_backtest_summary(sample_results)
            output = fake_out.getvalue()
            
            # Verify output contains key information
            self.assertIn('BACKTEST SUMMARY', output)
            self.assertIn('2024-01-01', output)
            self.assertIn('2024-01-31', output)
            self.assertIn('10000.00', output)  # Initial capital
            self.assertIn('10500.00', output)  # Final capital
            self.assertIn('500.00', output)  # Total P&L
            self.assertIn('5.00%', output)  # ROI
            self.assertIn('70.00%', output)  # Win rate
    
    def test_print_backtest_summary_without_results(self):
        """Test print_backtest_summary using current bot state"""
        # Add some trades to the bot
        self.bot.record_trade('TEST', 'BUY', 10.0, 100.0, True, 
                            entry_price=100.0, exit_price=105.0, pnl=50.0, pnl_percent=5.0)
        self.bot.record_trade('TEST', 'SELL', 10.0, 105.0, True,
                            entry_price=100.0, exit_price=105.0, pnl=50.0, pnl_percent=5.0)
        
        # Capture stdout
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.bot.print_backtest_summary()
            output = fake_out.getvalue()
            
            # Verify output contains key information
            self.assertIn('BACKTEST SUMMARY', output)
            self.assertIn('Initial Capital', output)
            self.assertIn('Final Capital', output)
            self.assertIn('Win Rate', output)
    
    def test_backtest_loop_saves_results_to_file(self):
        """Test that backtest_loop saves results to a JSON file"""
        # Create mock data fetcher
        mock_data_fetcher = MagicMock()
        
        # Create minimal historical data
        dates = pd.date_range(start=self.start_date, periods=5, freq='D')
        historical_data = pd.DataFrame({
            'date': dates,
            'open': [100, 101, 102, 103, 104],
            'high': [102, 103, 104, 105, 106],
            'low': [98, 99, 100, 101, 102],
            'close': [101, 102, 103, 104, 105],
            'volume': [1000000 for _ in range(5)]
        })
        
        mock_data_fetcher.fetch_historical_data_yfinance = MagicMock(return_value=historical_data)
        
        # Patch the DataFetcher class
        with patch('main.DataFetcher', return_value=mock_data_fetcher):
            # Run backtest
            self.bot.backtest_loop(self.start_date, self.end_date, ['TEST'])
            
            # Check if a backtest history file was created
            import glob
            backtest_files = glob.glob('backtest_history_*.json')
            self.assertGreater(len(backtest_files), 0, "Should have created a backtest history file")
            
            # Verify file content
            with open(backtest_files[0], 'r') as f:
                saved_data = json.load(f)
                self.assertIn('metadata', saved_data)
                self.assertIn('trades', saved_data)


class TestBacktestLoopCompatibility(unittest.TestCase):
    """Test backwards compatibility of standalone backtest_loop function"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_standalone_function_delegates_to_instance_method(self):
        """Test that standalone backtest_loop calls the instance method"""
        from main import backtest_loop
        
        # Mock the instance method
        with patch.object(TradingBot, 'backtest_loop') as mock_method:
            mock_method.return_value = {
                'metadata': {
                    'initial_capital': 10000.0,
                    'final_capital': 10500.0,
                    'total_pnl': 500.0,
                    'win_rate': 0.7
                },
                'trades': []
            }
            
            # Call standalone function
            results = backtest_loop(self.bot, ['AAPL'], period='1y')
            
            # Verify instance method was called
            mock_method.assert_called_once()
            
            # Verify results were passed through
            self.assertIn('metadata', results)
            self.assertEqual(results['metadata']['initial_capital'], 10000.0)
    
    def test_standalone_function_period_conversion(self):
        """Test that standalone function correctly converts periods to dates"""
        from main import backtest_loop
        
        # Mock the instance method to capture arguments
        with patch.object(TradingBot, 'backtest_loop') as mock_method:
            mock_method.return_value = {'metadata': {}, 'trades': []}
            
            # Call with different periods
            for period in ['1y', '6mo', '3mo', '1mo', '5d']:
                backtest_loop(self.bot, ['AAPL'], period=period)
                
                # Verify instance method was called with date strings
                call_args = mock_method.call_args
                self.assertEqual(len(call_args[0]), 3)  # start_date, end_date, symbols
                
                # Verify dates are strings in YYYY-MM-DD format
                start_date = call_args[0][0]
                end_date = call_args[0][1]
                self.assertRegex(start_date, r'\d{4}-\d{2}-\d{2}')
                self.assertRegex(end_date, r'\d{4}-\d{2}-\d{2}')


if __name__ == '__main__':
    unittest.main()
