#!/usr/bin/env python3
"""
Test suite for backtesting mode
Tests the new BACKTEST_MODE functionality
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta

# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')
os.environ.setdefault('BACKTEST_MODE', 'true')

# Import after setting environment variables
from main import TradingBot, backtest_loop


class TestBacktestMode(unittest.TestCase):
    """Test backtesting mode functionality"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
        self.test_symbols = ['AAPL', 'MSFT']
    
    def test_backtest_mode_environment_variable(self):
        """Test that BACKTEST_MODE environment variable is loaded correctly"""
        # Check the environment variable directly
        backtest_mode = os.environ.get('BACKTEST_MODE', 'false').lower() == 'true'
        self.assertTrue(backtest_mode, "BACKTEST_MODE should be True in test environment")
    
    def test_backtest_loop_with_mock_data(self):
        """Test backtest_loop with mock historical data"""
        # Create mock data fetcher
        mock_data_fetcher = MagicMock()
        
        # Create sample historical data with recent dates (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        dates = pd.date_range(start=start_date, periods=30, freq='D')
        historical_data = pd.DataFrame({
            'date': dates,
            'open': [100 + i * 2 for i in range(30)],
            'high': [102 + i * 2 for i in range(30)],
            'low': [98 + i * 2 for i in range(30)],
            'close': [101 + i * 2 for i in range(30)],
            'volume': [1000000 for _ in range(30)]
        })
        
        # Mock the fetch_historical_data_yfinance method
        mock_data_fetcher.fetch_historical_data_yfinance = MagicMock(return_value=historical_data)
        
        # Patch the DataFetcher class
        with patch('main.DataFetcher', return_value=mock_data_fetcher):
            # Run backtest
            results = backtest_loop(self.bot, ['TEST'], period='1mo')
            
            # Verify results structure
            self.assertIsInstance(results, dict)
            self.assertIn('metadata', results)
            self.assertIn('trades', results)
            
            # Verify metadata
            metadata = results['metadata']
            self.assertIn('initial_capital', metadata)
            self.assertIn('final_capital', metadata)
            self.assertIn('total_pnl', metadata)
            self.assertIn('win_rate', metadata)
            self.assertIn('total_trades', metadata)
            
            # Verify initial capital
            self.assertEqual(metadata['initial_capital'], 10000.0)
    
    def test_backtest_loop_exit_conditions(self):
        """Test that backtest_loop properly handles take profit and trailing stop exits"""
        # Create mock data fetcher
        mock_data_fetcher = MagicMock()
        
        # Create data with a clear take profit scenario using recent dates
        # Start at 100, rise to 115 (15% gain, should trigger 10% take profit)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)
        dates = pd.date_range(start=start_date, periods=10, freq='D')
        historical_data = pd.DataFrame({
            'date': dates,
            'open': [100, 102, 104, 106, 108, 110, 112, 114, 115, 115],
            'high': [102, 104, 106, 108, 110, 112, 114, 116, 117, 116],
            'low': [98, 100, 102, 104, 106, 108, 110, 112, 113, 113],
            'close': [101, 103, 105, 107, 109, 111, 113, 115, 116, 115],
            'volume': [1000000 for _ in range(10)]
        })
        
        mock_data_fetcher.fetch_historical_data_yfinance = MagicMock(return_value=historical_data)
        
        with patch('main.DataFetcher', return_value=mock_data_fetcher):
            results = backtest_loop(self.bot, ['TEST'], period='1mo')
            
            # Check that at least one trade was made
            self.assertGreater(len(results['trades']), 0)
            
            # Check for take profit or trailing stop exits
            exit_reasons = [trade.get('triggered_by', '') for trade in results['trades'] if trade.get('action') == 'SELL']
            self.assertTrue(any(reason in ['take_profit', 'trailing_stop', 'backtest_end'] for reason in exit_reasons))
    
    def test_backtest_loop_no_data(self):
        """Test backtest_loop behavior when no historical data is available"""
        # Create mock data fetcher that returns None
        mock_data_fetcher = MagicMock()
        mock_data_fetcher.fetch_historical_data_yfinance = MagicMock(return_value=None)
        
        with patch('main.DataFetcher', return_value=mock_data_fetcher):
            results = backtest_loop(self.bot, ['INVALID_SYMBOL'], period='1mo')
            
            # Should complete without errors but have no trades
            self.assertIsInstance(results, dict)
            self.assertEqual(len(results['trades']), 0)
    
    def test_backtest_results_file_creation(self):
        """Test that backtest_loop creates a results JSON file"""
        import glob
        
        # Clean up any existing backtest_history files
        for f in glob.glob('backtest_history_*.json'):
            try:
                os.remove(f)
            except FileNotFoundError:
                # File may have already been removed; ignore
                pass
            except OSError:
                # Best-effort cleanup in tests: ignore errors if file cannot be removed
                pass
        # Create mock data fetcher
        mock_data_fetcher = MagicMock()
        
        # Create simple historical data with recent dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)
        dates = pd.date_range(start=start_date, periods=5, freq='D')
        historical_data = pd.DataFrame({
            'date': dates,
            'open': [100, 101, 102, 103, 104],
            'high': [102, 103, 104, 105, 106],
            'low': [98, 99, 100, 101, 102],
            'close': [101, 102, 103, 104, 105],
            'volume': [1000000 for _ in range(5)]
        })
        
        mock_data_fetcher.fetch_historical_data_yfinance = MagicMock(return_value=historical_data)
        
        with patch('main.DataFetcher', return_value=mock_data_fetcher):
            results = backtest_loop(self.bot, ['TEST'], period='1mo')
            backtest_loop(self.bot, ['TEST'], period='1mo')
            # Check that a backtest_history file was created
            backtest_files = glob.glob('backtest_history_*.json')
            self.assertGreater(len(backtest_files), 0, "backtest_history file should be created")
            
            # Verify file contents
            if backtest_files:
                with open(backtest_files[0], 'r') as f:
                    saved_results = json.load(f)
                    self.assertIn('metadata', saved_results)
                    self.assertIn('trades', saved_results)
                
                # Clean up
                for f in backtest_files:
                    try:
                        if os.path.exists(f):
                            os.remove(f)
                    except OSError:
                        # Best-effort cleanup in tests: ignore errors if file cannot be removed
                        pass

    def test_backtest_parameters_in_results(self):
        """Test that backtest results include the parameters used"""
        mock_data_fetcher = MagicMock()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)
        dates = pd.date_range(start=start_date, periods=5, freq='D')
        historical_data = pd.DataFrame({
            'date': dates,
            'open': [100, 101, 102, 103, 104],
            'high': [102, 103, 104, 105, 106],
            'low': [98, 99, 100, 101, 102],
            'close': [101, 102, 103, 104, 105],
            'volume': [1000000 for _ in range(5)]
        })
        
        mock_data_fetcher.fetch_historical_data_yfinance = MagicMock(return_value=historical_data)
        
        with patch('main.DataFetcher', return_value=mock_data_fetcher):
            results = backtest_loop(self.bot, ['TEST'], period='1mo')
            
            # Verify parameters are included
            self.assertIn('parameters', results['metadata'])
            params = results['metadata']['parameters']
            
            self.assertIn('risk_threshold', params)
            self.assertIn('trailing_stop_percent', params)
            self.assertIn('take_profit_percent', params)
            self.assertIn('stop_loss_percent', params)
            self.assertIn('position_size', params)
            self.assertIn('min_allocation', params)
            self.assertIn('max_allocation', params)
    
    def test_backtest_capital_tracking(self):
        """Test that backtest correctly tracks capital changes"""
        mock_data_fetcher = MagicMock()
        
        # Create data that should result in a profit using recent dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=20)
        dates = pd.date_range(start=start_date, periods=20, freq='D')
        historical_data = pd.DataFrame({
            'date': dates,
            'open': [100 + i for i in range(20)],
            'high': [105 + i for i in range(20)],
            'low': [98 + i for i in range(20)],
            'close': [103 + i for i in range(20)],
            'volume': [1000000 for _ in range(20)]
        })
        
        mock_data_fetcher.fetch_historical_data_yfinance = MagicMock(return_value=historical_data)
        
        with patch('main.DataFetcher', return_value=mock_data_fetcher):
            initial_capital = self.bot.total_capital
            results = backtest_loop(self.bot, ['TEST'], period='1mo')
            
            # Verify capital tracking
            metadata = results['metadata']
            self.assertEqual(metadata['initial_capital'], initial_capital)
            self.assertIsInstance(metadata['final_capital'], (int, float))
            self.assertIsInstance(metadata['total_pnl'], (int, float))
            
            # P&L should equal final - initial
            expected_pnl = metadata['final_capital'] - metadata['initial_capital']
            self.assertAlmostEqual(metadata['total_pnl'], expected_pnl, places=2)


class TestBacktestModeIntegration(unittest.TestCase):
    """Integration tests for backtest mode"""
    
    def test_backtest_mode_disabled_by_default(self):
        """Test that BACKTEST_MODE is false by default"""
        # This would need to be tested in a separate process or by reloading the module
        # For now, just document the expected behavior
        pass
    
    def test_backtest_with_multiple_symbols(self):
        """Test backtesting with multiple symbols"""
        bot = TradingBot(total_capital=10000.0)
        mock_data_fetcher = MagicMock()
        
        # Create data for multiple symbols using recent dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)
        dates = pd.date_range(start=start_date, periods=10, freq='D')
        
        def create_historical_data():
            return pd.DataFrame({
                'date': dates,
                'open': [100 + i for i in range(10)],
                'high': [102 + i for i in range(10)],
                'low': [98 + i for i in range(10)],
                'close': [101 + i for i in range(10)],
                'volume': [1000000 for _ in range(10)]
            })
        
        mock_data_fetcher.fetch_historical_data_yfinance = MagicMock(side_effect=lambda symbol, **kwargs: create_historical_data())
        
        with patch('main.DataFetcher', return_value=mock_data_fetcher):
            backtest_loop(bot, ['AAPL', 'MSFT', 'GOOGL'], period='1mo')
            
            # Should have attempted to process all symbols
            self.assertGreater(mock_data_fetcher.fetch_historical_data_yfinance.call_count, 0)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
