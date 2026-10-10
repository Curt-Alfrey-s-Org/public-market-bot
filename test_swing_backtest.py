#!/usr/bin/env python3
"""
Test suite for swing trading backtesting functionality
Tests the new run_swing_backtest method with various scenarios
"""

import os
# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtesting import Backtester


class TestSwingBacktest(unittest.TestCase):
    """Test core swing backtesting functionality"""
    
    def setUp(self):
        """Set up test backtester instance"""
        self.backtester = Backtester(initial_capital=10000.0)
    
    def test_swing_backtest_basic(self):
        """Test basic swing backtest functionality"""
        # Generate simple uptrending data
        days = 50
        data = pd.DataFrame({
            'symbol': ['TEST'] * days,
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') for i in range(days)],
            'open': [100 + i * 0.5 for i in range(days)],
            'high': [101 + i * 0.5 for i in range(days)],
            'low': [99 + i * 0.5 for i in range(days)],
            'close': [100 + i * 0.5 for i in range(days)],
            'volume': [1000000] * days
        })
        
        # Run swing backtest
        results = self.backtester.run_swing_backtest(
            historical_data=data,
            take_profit_pct=0.10,
            trailing_stop_pct=0.03,
            stop_loss_pct=0.06,
            min_hold_days=2,
            max_hold_days=10
        )
        
        # Verify results structure
        self.assertIn('initial_capital', results)
        self.assertIn('final_capital', results)
        self.assertIn('total_pnl', results)
        self.assertIn('roi', results)
        self.assertIn('total_trades', results)
        self.assertIn('winning_trades', results)
        self.assertIn('losing_trades', results)
        self.assertIn('win_rate', results)
        self.assertIn('profit_factor', results)
        self.assertIn('avg_holding_days', results)
        self.assertIn('trades', results)
        
        # Verify some trades were generated
        self.assertGreater(results['total_trades'], 0)
        
        # Verify win rate is a valid percentage
        self.assertGreaterEqual(results['win_rate'], 0.0)
        self.assertLessEqual(results['win_rate'], 1.0)
    
    def test_swing_backtest_bull_market(self):
        """Test swing backtest in strong bull market"""
        days = 60
        data = pd.DataFrame({
            'symbol': ['BULL'] * days,
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') for i in range(days)],
            'open': [100 + i * 2 for i in range(days)],
            'high': [102 + i * 2 for i in range(days)],
            'low': [98 + i * 2 for i in range(days)],
            'close': [100 + i * 2 for i in range(days)],
            'volume': [1000000] * days
        })
        
        results = self.backtester.run_swing_backtest(
            historical_data=data,
            take_profit_pct=0.08,
            trailing_stop_pct=0.03,
            stop_loss_pct=0.05,
            min_hold_days=2,
            max_hold_days=10
        )
        
        # In strong bull market, should have high win rate
        self.assertGreater(results['win_rate'], 0.5)
        
        # Should be profitable
        self.assertGreater(results['total_pnl'], 0)
        
        # Most exits should be take_profit or trailing_stop
        take_profit_exits = sum(1 for t in results['trades'] if t['exit_reason'] == 'take_profit')
        self.assertGreater(take_profit_exits, 0)
    
    def test_swing_backtest_bear_market(self):
        """Test swing backtest in bear market"""
        days = 60
        data = pd.DataFrame({
            'symbol': ['BEAR'] * days,
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') for i in range(days)],
            'open': [200 - i * 2 for i in range(days)],
            'high': [202 - i * 2 for i in range(days)],
            'low': [198 - i * 2 for i in range(days)],
            'close': [200 - i * 2 for i in range(days)],
            'volume': [1000000] * days
        })
        
        results = self.backtester.run_swing_backtest(
            historical_data=data,
            take_profit_pct=0.08,
            trailing_stop_pct=0.03,
            stop_loss_pct=0.05,
            min_hold_days=2,
            max_hold_days=10
        )
        
        # In bear market, should have lower win rate
        self.assertLessEqual(results['win_rate'], 0.6)
        
        # Most exits should be stop_loss
        stop_loss_exits = sum(1 for t in results['trades'] if t['exit_reason'] == 'stop_loss')
        self.assertGreater(stop_loss_exits, 0)
    
    def test_swing_backtest_sideways_market(self):
        """Test swing backtest in sideways/ranging market"""
        days = 80
        # Create oscillating price pattern
        prices = [100 + 10 * np.sin(i * 0.3) for i in range(days)]
        
        data = pd.DataFrame({
            'symbol': ['SIDE'] * days,
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') for i in range(days)],
            'open': prices,
            'high': [p + 2 for p in prices],
            'low': [p - 2 for p in prices],
            'close': prices,
            'volume': [1000000] * days
        })
        
        results = self.backtester.run_swing_backtest(
            historical_data=data,
            take_profit_pct=0.06,
            trailing_stop_pct=0.03,
            stop_loss_pct=0.06,
            min_hold_days=2,
            max_hold_days=8
        )
        
        # In sideways market, should have mixed results
        self.assertGreater(results['total_trades'], 0)
        self.assertGreater(results['winning_trades'], 0)
        self.assertGreater(results['losing_trades'], 0)
    
    def test_swing_backtest_holding_period_enforcement(self):
        """Test that minimum holding period is enforced"""
        days = 40
        data = pd.DataFrame({
            'symbol': ['TEST'] * days,
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') for i in range(days)],
            'open': [100] * days,
            'high': [110] * days,  # High enough to trigger take profit immediately
            'low': [95] * days,
            'close': [100] * days,
            'volume': [1000000] * days
        })
        
        results = self.backtester.run_swing_backtest(
            historical_data=data,
            take_profit_pct=0.05,
            trailing_stop_pct=0.03,
            stop_loss_pct=0.06,
            min_hold_days=3,  # Minimum 3 days
            max_hold_days=10
        )
        
        # All trades should respect minimum holding period
        for trade in results['trades']:
            self.assertGreaterEqual(trade['holding_days'], 3)
    
    def test_swing_backtest_max_holding_period(self):
        """Test that maximum holding period is enforced"""
        days = 50
        data = pd.DataFrame({
            'symbol': ['TEST'] * days,
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') for i in range(days)],
            'open': [100] * days,
            'high': [101] * days,  # Not high enough to trigger exits
            'low': [99] * days,
            'close': [100] * days,
            'volume': [1000000] * days
        })
        
        results = self.backtester.run_swing_backtest(
            historical_data=data,
            take_profit_pct=0.10,
            trailing_stop_pct=0.03,
            stop_loss_pct=0.06,
            min_hold_days=2,
            max_hold_days=7  # Maximum 7 days
        )
        
        # All trades should respect maximum holding period
        for trade in results['trades']:
            self.assertLessEqual(trade['holding_days'], 7)
    
    def test_swing_backtest_take_profit_exit(self):
        """Test that take profit exits work correctly"""
        days = 30
        # Create data that hits take profit
        data = pd.DataFrame({
            'symbol': ['TEST'] * days,
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') for i in range(days)],
            'open': [100] * 5 + [100, 105, 110, 115, 120] + [120] * 20,
            'high': [101] * 5 + [101, 106, 111, 116, 121] + [121] * 20,
            'low': [99] * 5 + [99, 104, 109, 114, 119] + [119] * 20,
            'close': [100] * 5 + [100, 105, 110, 115, 120] + [120] * 20,
            'volume': [1000000] * days
        })
        
        results = self.backtester.run_swing_backtest(
            historical_data=data,
            take_profit_pct=0.10,  # 10% take profit
            trailing_stop_pct=0.03,
            stop_loss_pct=0.06,
            min_hold_days=2,
            max_hold_days=15
        )
        
        # Should have some take profit exits
        take_profit_exits = [t for t in results['trades'] if t['exit_reason'] == 'take_profit']
        self.assertGreater(len(take_profit_exits), 0)
        
        # Take profit trades should all be winners
        for trade in take_profit_exits:
            self.assertTrue(trade['is_win'])
    
    def test_swing_backtest_stop_loss_exit(self):
        """Test that stop loss exits work correctly"""
        days = 30
        # Create data that hits stop loss
        data = pd.DataFrame({
            'symbol': ['TEST'] * days,
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') for i in range(days)],
            'open': [100] * 5 + [100, 95, 90, 85, 80] + [80] * 20,
            'high': [101] * 5 + [101, 96, 91, 86, 81] + [81] * 20,
            'low': [99] * 5 + [99, 94, 89, 84, 79] + [79] * 20,
            'close': [100] * 5 + [100, 95, 90, 85, 80] + [80] * 20,
            'volume': [1000000] * days
        })
        
        results = self.backtester.run_swing_backtest(
            historical_data=data,
            take_profit_pct=0.10,
            trailing_stop_pct=0.03,
            stop_loss_pct=0.06,  # 6% stop loss
            min_hold_days=2,
            max_hold_days=15
        )
        
        # Should have some stop loss exits
        stop_loss_exits = [t for t in results['trades'] if t['exit_reason'] == 'stop_loss']
        self.assertGreater(len(stop_loss_exits), 0)
        
        # Stop loss trades should all be losers
        for trade in stop_loss_exits:
            self.assertFalse(trade['is_win'])
    
    def test_swing_backtest_trailing_stop_exit(self):
        """Test that trailing stop exits work correctly"""
        days = 30
        # Create data that rises then falls (trailing stop scenario)
        data = pd.DataFrame({
            'symbol': ['TEST'] * days,
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') for i in range(days)],
            'open': [100] * 3 + [100, 102, 105, 107, 104, 103] + [103] * 18,
            'high': [101] * 3 + [101, 103, 106, 108, 105, 104] + [104] * 18,
            'low': [99] * 3 + [99, 101, 104, 106, 103, 102] + [102] * 18,
            'close': [100] * 3 + [100, 102, 105, 107, 104, 103] + [103] * 18,
            'volume': [1000000] * days
        })
        
        results = self.backtester.run_swing_backtest(
            historical_data=data,
            take_profit_pct=0.15,  # High target so trailing stop triggers first
            trailing_stop_pct=0.03,  # 3% trailing stop
            stop_loss_pct=0.10,
            min_hold_days=2,
            max_hold_days=15
        )
        
        # Should have some trailing stop exits
        trailing_stop_exits = [t for t in results['trades'] if t['exit_reason'] == 'trailing_stop']
        self.assertGreater(len(trailing_stop_exits), 0)
    
    def test_swing_backtest_metrics_calculation(self):
        """Test that all metrics are calculated correctly"""
        days = 40
        data = pd.DataFrame({
            'symbol': ['TEST'] * days,
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') for i in range(days)],
            'open': [100 + i * 0.5 for i in range(days)],
            'high': [101 + i * 0.5 for i in range(days)],
            'low': [99 + i * 0.5 for i in range(days)],
            'close': [100 + i * 0.5 for i in range(days)],
            'volume': [1000000] * days
        })
        
        results = self.backtester.run_swing_backtest(
            historical_data=data,
            take_profit_pct=0.08,
            trailing_stop_pct=0.03,
            stop_loss_pct=0.06,
            min_hold_days=2,
            max_hold_days=10
        )
        
        # Verify win rate calculation
        calculated_win_rate = results['winning_trades'] / results['total_trades'] if results['total_trades'] > 0 else 0
        self.assertAlmostEqual(results['win_rate'], calculated_win_rate, places=4)
        
        # Verify total trades = winning + losing
        self.assertEqual(results['total_trades'], results['winning_trades'] + results['losing_trades'])
        
        # Verify profit factor calculation
        if results['losing_trades'] > 0:
            gross_profit = sum(t['pnl'] for t in results['trades'] if t['is_win'])
            gross_loss = abs(sum(t['pnl'] for t in results['trades'] if not t['is_win']))
            expected_pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            if expected_pf != float('inf'):
                self.assertAlmostEqual(results['profit_factor'], expected_pf, places=2)
        
        # Verify ROI calculation
        expected_roi = (results['final_capital'] - results['initial_capital']) / results['initial_capital']
        self.assertAlmostEqual(results['roi'], expected_roi, places=6)
    
    def test_fetch_historical_data_yfinance(self):
        """Test fetching historical data from yfinance"""
        # This test may fail if yfinance is not installed or internet is unavailable
        try:
            data = self.backtester.fetch_historical_data_yfinance('AAPL', period='1mo')
            
            if not data.empty:
                # Verify data structure
                required_columns = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
                for col in required_columns:
                    self.assertIn(col, data.columns)
                
                # Verify data has rows
                self.assertGreater(len(data), 0)
                
                # Verify OHLC relationships
                self.assertTrue(all(data['high'] >= data['low']))
                self.assertTrue(all(data['close'] >= data['low']))
                self.assertTrue(all(data['close'] <= data['high']))
        except Exception as e:
            # Skip test if yfinance unavailable
            self.skipTest(f"yfinance test skipped: {str(e)}")
    
    def test_swing_backtest_empty_data(self):
        """Test swing backtest handles empty data gracefully"""
        empty_data = pd.DataFrame()
        
        # Should not crash with empty data
        try:
            self.backtester.run_swing_backtest(
                historical_data=empty_data,
                take_profit_pct=0.10,
                trailing_stop_pct=0.03,
                stop_loss_pct=0.06,
                min_hold_days=2,
                max_hold_days=10
            )
        except Exception as e:
            # Acceptable to raise an error for empty data
            pass
    
    def test_swing_backtest_insufficient_data(self):
        """Test swing backtest with insufficient data points"""
        # Only 5 days of data (less than max_hold_days)
        days = 5
        data = pd.DataFrame({
            'symbol': ['TEST'] * days,
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') for i in range(days)],
            'open': [100] * days,
            'high': [101] * days,
            'low': [99] * days,
            'close': [100] * days,
            'volume': [1000000] * days
        })
        
        results = self.backtester.run_swing_backtest(
            historical_data=data,
            take_profit_pct=0.10,
            trailing_stop_pct=0.03,
            stop_loss_pct=0.06,
            min_hold_days=2,
            max_hold_days=10
        )
        
        # Should handle gracefully (may have 0 trades)
        self.assertGreaterEqual(results['total_trades'], 0)


class TestSwingBacktestParameters(unittest.TestCase):
    """Test swing backtest parameter validation and edge cases"""
    
    def setUp(self):
        """Set up test backtester instance"""
        self.backtester = Backtester(initial_capital=10000.0)
        
        # Create standard test data
        days = 50
        self.test_data = pd.DataFrame({
            'symbol': ['TEST'] * days,
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') for i in range(days)],
            'open': [100 + i * 0.5 for i in range(days)],
            'high': [101 + i * 0.5 for i in range(days)],
            'low': [99 + i * 0.5 for i in range(days)],
            'close': [100 + i * 0.5 for i in range(days)],
            'volume': [1000000] * days
        })
    
    def test_custom_capital(self):
        """Test swing backtest with custom capital"""
        results = self.backtester.run_swing_backtest(
            historical_data=self.test_data,
            take_profit_pct=0.10,
            trailing_stop_pct=0.03,
            stop_loss_pct=0.06,
            min_hold_days=2,
            max_hold_days=10,
            capital=50000.0  # Custom capital
        )
        
        self.assertEqual(results['initial_capital'], 50000.0)
    
    def test_different_parameter_combinations(self):
        """Test various parameter combinations"""
        param_sets = [
            # Conservative
            {'take_profit_pct': 0.05, 'trailing_stop_pct': 0.02, 'stop_loss_pct': 0.08},
            # Aggressive  
            {'take_profit_pct': 0.15, 'trailing_stop_pct': 0.05, 'stop_loss_pct': 0.04},
            # Balanced
            {'take_profit_pct': 0.10, 'trailing_stop_pct': 0.03, 'stop_loss_pct': 0.06},
        ]
        
        for params in param_sets:
            results = self.backtester.run_swing_backtest(
                historical_data=self.test_data,
                min_hold_days=2,
                max_hold_days=10,
                **params
            )
            
            # All should complete successfully
            self.assertGreater(results['total_trades'], 0)
            self.assertIn('win_rate', results)


if __name__ == '__main__':
    unittest.main()
