#!/usr/bin/env python3
"""
Test suite for Better Mimic Live in Sim features
Tests historical simulation, PDT enforcement, and ML parameter optimization
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from datetime import timedelta
import pandas as pd

# Set test environment variables before importing main
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
os.environ['SCHWAB_API_ENABLED'] = 'off'
os.environ['ALLOW_RANDOM_FALLBACK'] = 'false'

# Import after setting environment
from main import TradingBot


class TestHistoricalSimulation(unittest.TestCase):
    """Test historical simulation with frozen time"""
    
    def setUp(self):
        """Set up test bot"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_enable_historical_mode(self):
        """Test enabling historical mode"""
        self.bot.enable_historical_mode('2023-01-01', '2023-12-31')
        
        self.assertTrue(self.bot.historical_mode)
        self.assertEqual(self.bot.historical_start.year, 2023)
        self.assertEqual(self.bot.historical_end.year, 2023)
        self.assertIsNotNone(self.bot.current_sim_date)
    
    @patch('main.YFINANCE_AVAILABLE', True)
    @patch('main.yf.Ticker')
    def test_load_historical_data(self, mock_ticker):
        """Test loading historical data"""
        # Mock yfinance data
        mock_data = MagicMock()
        mock_data.empty = False
        mock_data.__len__ = lambda self: 252
        mock_ticker.return_value.history.return_value = mock_data
        
        self.bot.load_historical_data('AAPL', '2023-01-01', '2023-12-31')
        
        self.assertIn('AAPL', self.bot.historical_data)
        mock_ticker.assert_called_once_with('AAPL')
    
    def test_advance_sim_date(self):
        """Test advancing simulation date"""
        self.bot.enable_historical_mode('2023-01-01', '2023-12-31')
        initial_date = self.bot.current_sim_date
        
        self.bot.advance_sim_date(5)
        
        expected_date = initial_date + timedelta(days=5)
        self.assertEqual(self.bot.current_sim_date, expected_date)
    
    def test_get_historical_price_no_data(self):
        """Test getting historical price with no data loaded"""
        self.bot.enable_historical_mode('2023-01-01', '2023-12-31')
        
        result = self.bot.get_historical_price('AAPL')
        
        self.assertIsNone(result)
    
    def test_get_stock_price_historical_mode(self):
        """Test that get_stock_price checks historical mode first"""
        # Enable historical mode and load fake data
        self.bot.enable_historical_mode('2023-01-01', '2023-01-31')
        
        # Create fake historical data
        dates = pd.date_range(start='2023-01-01', end='2023-01-31', freq='D')
        fake_data = pd.DataFrame({
            'Close': [150.0] * len(dates),
            'Volume': [1000000] * len(dates)
        }, index=dates)
        
        self.bot.historical_data['AAPL'] = fake_data
        
        # Get price should use historical data
        price, volume = self.bot.get_stock_price('AAPL')
        
        self.assertEqual(price, 150.0)
        self.assertEqual(volume, 1000000)


class TestPDTEnforcement(unittest.TestCase):
    """Test PDT enforcement in all modes"""
    
    def test_pdt_enforced_in_paper_mode(self):
        """Test that PDT rules are enforced in paper mode"""
        with patch('main.PAPER_TRADING_MODE', True):
            with patch('main.SCHWAB_SANDBOX_MODE', False):
                bot = TradingBot(total_capital=500.0)  # Less than $25k
                
                # Add 3 day trades
                for i in range(3):
                    bot.add_day_trade(f"TEST{i}")
                
                # Check PDT compliance - should block trading
                can_trade, msg = bot.check_pdt_compliance()
                
                self.assertFalse(can_trade, "PDT should be enforced in paper mode")
                self.assertIn("PDT Limit Reached", msg)
    
    def test_pdt_enforced_in_sandbox_mode(self):
        """Test that PDT rules are enforced in sandbox mode"""
        with patch('main.PAPER_TRADING_MODE', True):
            with patch('main.SCHWAB_SANDBOX_MODE', True):
                bot = TradingBot(total_capital=500.0)  # Less than $25k
                
                # Add 3 day trades
                for i in range(3):
                    bot.add_day_trade(f"TEST{i}")
                
                # Check PDT compliance - should block trading
                can_trade, msg = bot.check_pdt_compliance()
                
                self.assertFalse(can_trade, "PDT should be enforced in sandbox mode")
                self.assertIn("PDT Limit Reached", msg)
    
    def test_pdt_enforced_in_production_mode(self):
        """Test that PDT rules are enforced in production mode"""
        with patch('main.PAPER_TRADING_MODE', False):
            bot = TradingBot(total_capital=500.0)  # Less than $25k
            
            # Add 3 day trades
            for i in range(3):
                bot.add_day_trade(f"TEST{i}")
            
            # Check PDT compliance - should block trading
            can_trade, msg = bot.check_pdt_compliance()
            
            self.assertFalse(can_trade, "PDT should be enforced in production mode")
            self.assertIn("PDT Limit Reached", msg)
    
    def test_pdt_allows_trading_under_limit(self):
        """Test that PDT allows trading when under the limit"""
        bot = TradingBot(total_capital=500.0)  # Less than $25k
        
        # Add only 2 day trades
        for i in range(2):
            bot.add_day_trade(f"TEST{i}")
        
        # Check PDT compliance - should allow trading
        can_trade, msg = bot.check_pdt_compliance()
        
        self.assertTrue(can_trade, "PDT should allow trading under the limit")
        self.assertIn("PDT OK", msg)
        self.assertIn("2/3", msg)
    
    def test_pdt_allows_unlimited_with_high_capital(self):
        """Test that PDT allows unlimited trades with $25k+ capital"""
        bot = TradingBot(total_capital=30000.0)  # Over $25k
        
        # Add many day trades
        for i in range(10):
            bot.add_day_trade(f"TEST{i}")
        
        # Check PDT compliance - should allow trading
        can_trade, msg = bot.check_pdt_compliance()
        
        self.assertTrue(can_trade, "PDT should allow unlimited trades with high capital")
        self.assertIn("PDT OK", msg)


class TestMLParameterOptimization(unittest.TestCase):
    """Test ML parameter optimization for 70% win rate"""
    
    def setUp(self):
        """Set up test bot with ML optimizer"""
        with patch('main.ML_OPTIMIZER_AVAILABLE', True):
            self.bot = TradingBot(total_capital=10000.0)
    
    def test_ml_optimizer_initialization(self):
        """Test that ML optimizer is initialized"""
        with patch('main.ML_OPTIMIZER_AVAILABLE', True):
            bot = TradingBot(total_capital=10000.0)
            # ML optimizer should be initialized if available
            # (but may be None if module import failed)
            self.assertTrue(hasattr(bot, 'ml_optimizer'))
    
    @patch('main.ML_OPTIMIZER_AVAILABLE', True)
    def test_optimize_parameters_ml_no_history(self):
        """Test ML optimization with no trade history"""
        bot = TradingBot(total_capital=10000.0)
        bot.ml_optimizer = MagicMock()
        bot.ml_optimizer.is_api_configured.return_value = True
        
        # Should return empty results
        optimized_params, predicted_win_rate = bot.optimize_parameters_ml()
        
        # With no history, should use trade history
        self.assertEqual(len(optimized_params), 0)
        self.assertEqual(predicted_win_rate, 0.0)
    
    @patch('main.ML_OPTIMIZER_AVAILABLE', True)
    def test_optimize_parameters_ml_with_backtest_results(self):
        """Test ML optimization with backtest results"""
        bot = TradingBot(total_capital=10000.0)
        
        # Mock ML optimizer
        mock_optimizer = MagicMock()
        mock_optimizer.is_api_configured.return_value = True
        mock_optimizer.optimize_parameters.return_value = (
            {'BOT_RISK_THRESHOLD': 0.03, 'BOT_TRAILING_STOP_PERCENT': 0.04},
            0.72
        )
        mock_optimizer.save_optimization_result.return_value = 'test.json'
        bot.ml_optimizer = mock_optimizer
        
        # Provide backtest results
        backtest_results = [
            {'win_rate': 0.55, 'roi': 0.08, 'sharpe_ratio': 1.2, 'max_drawdown': -0.12},
            {'win_rate': 0.58, 'roi': 0.10, 'sharpe_ratio': 1.4, 'max_drawdown': -0.10}
        ]
        
        # Run optimization
        optimized_params, predicted_win_rate = bot.optimize_parameters_ml(backtest_results)
        
        # Verify results
        self.assertGreater(len(optimized_params), 0)
        self.assertGreater(predicted_win_rate, 0.0)
        self.assertEqual(predicted_win_rate, 0.72)
        mock_optimizer.optimize_parameters.assert_called_once()
        mock_optimizer.save_optimization_result.assert_called_once()


class TestIntegration(unittest.TestCase):
    """Integration tests for all features together"""
    
    def test_historical_simulation_with_pdt_enforcement(self):
        """Test historical simulation respects PDT rules"""
        bot = TradingBot(total_capital=500.0)  # Less than $25k
        
        # Enable historical mode
        bot.enable_historical_mode('2023-01-01', '2023-01-31')
        
        # Load fake historical data
        dates = pd.date_range(start='2023-01-01', end='2023-01-31', freq='D')
        fake_data = pd.DataFrame({
            'Close': [150.0] * len(dates),
            'Volume': [1000000] * len(dates)
        }, index=dates)
        bot.historical_data['AAPL'] = fake_data
        
        # Simulate 3 day trades
        for i in range(3):
            bot.add_day_trade('AAPL')
        
        # Try to get price for another trade
        price, volume = bot.get_stock_price('AAPL')
        price, _ = bot.get_stock_price('AAPL')
        # PDT check should block the trade
        can_trade, msg = bot.check_pdt_compliance()
        self.assertFalse(can_trade, "PDT should block 4th day trade even in historical mode")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
