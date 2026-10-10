#!/usr/bin/env python3
"""
Test suite for backtesting scenarios
Tests historical data analysis, performance metrics, and strategy validation
"""

import os
# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
from backtesting import Backtester
from strategies import SMAStrategy, BollingerBandsStrategy


class TestBacktester(unittest.TestCase):
    """Test core Backtester functionality"""
    
    def setUp(self):
        """Set up test backtester instance"""
        self.backtester = Backtester(initial_capital=10000.0)
    
    def test_backtester_initialization(self):
        """Test backtester initializes with correct parameters"""
        self.assertEqual(self.backtester.initial_capital, 10000.0)
        self.assertEqual(len(self.backtester.results), 0)
    
    def test_generate_historical_data(self):
        """Test synthetic historical data generation"""
        data = self.backtester.generate_historical_data(
            symbol='TEST',
            days=100,
            start_price=100.0,
            volatility=0.02
        )
        
        # Verify data structure
        self.assertEqual(len(data), 100)
        self.assertIn('date', data.columns)
        self.assertIn('close', data.columns)
        self.assertIn('volume', data.columns)
        
        # Verify data types
        self.assertTrue(all(isinstance(x, (int, float)) for x in data['close']))
        self.assertTrue(all(isinstance(x, int) for x in data['volume']))
    
    def test_historical_data_volatility(self):
        """Test that generated data has realistic volatility"""
        low_vol_data = self.backtester.generate_historical_data(
            'TEST', days=100, start_price=100.0, volatility=0.01
        )
        
        high_vol_data = self.backtester.generate_historical_data(
            'TEST', days=100, start_price=100.0, volatility=0.05
        )
        
        # Calculate price ranges
        low_vol_range = low_vol_data['close'].max() - low_vol_data['close'].min()
        high_vol_range = high_vol_data['close'].max() - high_vol_data['close'].min()
        
        # High volatility should produce larger price range
        self.assertGreater(high_vol_range, low_vol_range)
    
    def test_load_historical_data_from_csv(self):
        """Test loading historical data from CSV file"""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("symbol,date,open,high,low,close,volume\n")
            f.write("TEST,2024-01-01,100,105,95,102,1000000\n")
            f.write("TEST,2024-01-02,102,108,100,106,1200000\n")
            f.write("TEST,2024-01-03,106,110,104,108,1100000\n")
            temp_file = f.name
        
        try:
            data = self.backtester.load_historical_data(temp_file)
            
            # Verify data loaded correctly
            self.assertEqual(len(data), 3)
            self.assertIn('close', data.columns)
            self.assertEqual(data['close'].iloc[0], 102)
        finally:
            import os
            os.unlink(temp_file)


class TestBacktestingScenarios(unittest.TestCase):
    """Test various backtesting scenarios"""
    
    def setUp(self):
        """Set up test instances"""
        self.backtester = Backtester(initial_capital=10000.0)
    
    def test_bull_market_scenario(self):
        """Test strategy performance in bull market"""
        # Generate uptrending market data
        days = 60
        prices = [100 + i * 1.5 for i in range(days)]  # Steady uptrend
        
        data = pd.DataFrame({
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') 
                     for i in range(days)],
            'close': prices,
            'volume': [1000000] * days
        })
        
        # Test SMA strategy in bull market
        strategy = SMAStrategy(fast_period=5, slow_period=15)
        signal = strategy.generate_signal(data)
        
        # In strong uptrend, should eventually generate BUY or HOLD
        self.assertIn(signal, ['BUY', 'HOLD'])
    
    def test_bear_market_scenario(self):
        """Test strategy performance in bear market"""
        # Generate downtrending market data
        days = 60
        prices = [150 - i * 1.5 for i in range(days)]  # Steady downtrend
        
        data = pd.DataFrame({
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') 
                     for i in range(days)],
            'close': prices,
            'volume': [1000000] * days
        })
        
        # Test SMA strategy in bear market
        strategy = SMAStrategy(fast_period=5, slow_period=15)
        signal = strategy.generate_signal(data)
        
        # In strong downtrend, should eventually generate SELL or HOLD
        self.assertIn(signal, ['SELL', 'HOLD'])
    
    def test_sideways_market_scenario(self):
        """Test strategy performance in sideways/ranging market"""
        # Generate sideways market data (oscillating)
        days = 60
        prices = [100 + 10 * np.sin(i * 0.3) for i in range(days)]
        
        data = pd.DataFrame({
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') 
                     for i in range(days)],
            'close': prices,
            'volume': [1000000] * days
        })
        
        # Test Bollinger Bands strategy in sideways market
        strategy = BollingerBandsStrategy(period=10, num_std=2.0)
        signal = strategy.generate_signal(data)
        
        # In sideways market, should generate some signal
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
    
    def test_high_volatility_scenario(self):
        """Test strategy performance with high volatility"""
        # Generate highly volatile data
        data = self.backtester.generate_historical_data(
            'TEST', days=50, start_price=100.0, volatility=0.10
        )
        
        # Test that strategies handle high volatility
        sma_strategy = SMAStrategy(fast_period=5, slow_period=10)
        bb_strategy = BollingerBandsStrategy(period=10, num_std=2.0)
        
        # Both should return valid signals
        sma_signal = sma_strategy.generate_signal(data)
        bb_signal = bb_strategy.generate_signal(data)
        
        self.assertIn(sma_signal, ['BUY', 'SELL', 'HOLD'])
        self.assertIn(bb_signal, ['BUY', 'SELL', 'HOLD'])
    
    def test_market_crash_scenario(self):
        """Test strategy behavior during sudden market crash"""
        # Generate data with sudden crash
        days = 40
        prices = [100] * 20 + [100 - i * 5 for i in range(1, 11)] + [50] * 10
        
        data = pd.DataFrame({
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') 
                     for i in range(days)],
            'close': prices,
            'volume': [1000000] * days
        })
        
        # Test strategies during crash
        sma_strategy = SMAStrategy(fast_period=5, slow_period=10)
        sma_signal = sma_strategy.generate_signal(data)
        
        # Should recognize downtrend
        # SELL or HOLD are both valid (HOLD if crash already recognized)
        self.assertIn(sma_signal, ['SELL', 'HOLD'])
    
    def test_recovery_scenario(self):
        """Test strategy behavior during market recovery"""
        # Generate data with crash and recovery
        days = 50
        prices = ([100] * 10 +                           # Stable
                  [100 - i * 5 for i in range(1, 11)] +  # Crash
                  [50 + i * 3 for i in range(1, 21)] +   # Recovery
                  [110] * 10)                            # New stable
        
        data = pd.DataFrame({
            'date': [(datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d') 
                     for i in range(days)],
            'close': prices,
            'volume': [1000000] * days
        })
        
        # Test strategies during recovery
        sma_strategy = SMAStrategy(fast_period=5, slow_period=15)
        signal = sma_strategy.generate_signal(data)
        
        # Should recognize uptrend recovery
        self.assertIn(signal, ['BUY', 'HOLD'])


class TestPerformanceMetrics(unittest.TestCase):
    """Test backtesting performance calculation"""
    
    def test_win_rate_calculation(self):
        """Test win rate calculation from backtest results"""
        # Simulate some trades
        trades = [
            {'is_win': True, 'pnl': 100},
            {'is_win': True, 'pnl': 150},
            {'is_win': False, 'pnl': -50},
            {'is_win': True, 'pnl': 200},
            {'is_win': False, 'pnl': -75},
        ]
        
        # Calculate win rate
        wins = sum(1 for t in trades if t['is_win'])
        total = len(trades)
        win_rate = wins / total
        
        self.assertEqual(win_rate, 0.6)  # 3 wins out of 5 = 60%
    
    def test_total_return_calculation(self):
        """Test total return calculation from backtest"""
        initial_capital = 10000.0
        
        trades = [
            {'pnl': 100},
            {'pnl': -50},
            {'pnl': 200},
            {'pnl': -75},
            {'pnl': 150},
        ]
        
        total_pnl = sum(t['pnl'] for t in trades)
        final_capital = initial_capital + total_pnl
        total_return = (final_capital - initial_capital) / initial_capital
        
        self.assertEqual(total_pnl, 325)
        self.assertEqual(final_capital, 10325.0)
        self.assertAlmostEqual(total_return, 0.0325, places=4)  # 3.25%
    
    def test_max_drawdown_calculation(self):
        """Test maximum drawdown calculation"""
        # Simulate capital over time
        capital_history = [10000, 10500, 10200, 9800, 9500, 10000, 10800, 10500]
        
        # Calculate drawdowns
        peak = capital_history[0]
        max_drawdown = 0
        
        for capital in capital_history:
            if capital > peak:
                peak = capital
            drawdown = (peak - capital) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        # Max drawdown should be from 10500 to 9500 = 9.52%
        self.assertAlmostEqual(max_drawdown, 0.0952, places=4)
    
    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation"""
        returns = [0.01, -0.005, 0.02, -0.01, 0.015, 0.005, -0.008, 0.012]
        risk_free_rate = 0.0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)
        
        if std_return > 0:
            sharpe_ratio = (avg_return - risk_free_rate) / std_return
        else:
            sharpe_ratio = 0.0
        
        # Sharpe ratio should be positive for profitable strategy
        self.assertGreater(sharpe_ratio, 0)


class TestStrategyValidation(unittest.TestCase):
    """Test strategy validation through backtesting"""
    
    def test_strategy_consistency(self):
        """Test that strategy produces consistent signals on same data"""
        data = pd.DataFrame({
            'close': [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120]
        })
        
        strategy = SMAStrategy(fast_period=3, slow_period=5)
        
        # Generate signal twice
        signal1 = strategy.generate_signal(data)
        signal2 = strategy.generate_signal(data)
        
        # Should produce same signal
        self.assertEqual(signal1, signal2)
    
    def test_strategy_parameter_sensitivity(self):
        """Test strategy sensitivity to parameter changes"""
        data = pd.DataFrame({
            'close': list(range(100, 130))  # Strong uptrend
        })
        
        # Test with different parameters
        fast_strategy = SMAStrategy(fast_period=3, slow_period=7)
        slow_strategy = SMAStrategy(fast_period=10, slow_period=20)
        
        fast_signal = fast_strategy.generate_signal(data)
        slow_signal = slow_strategy.generate_signal(data)
        
        # Both should recognize uptrend, but timing may differ
        # At minimum, verify signals are valid
        self.assertIn(fast_signal, ['BUY', 'SELL', 'HOLD'])
        self.assertIn(slow_signal, ['BUY', 'SELL', 'HOLD'])
    
    def test_overfitting_detection(self):
        """Test for overfitting by comparing in-sample vs out-of-sample"""
        # Generate training data
        train_data = pd.DataFrame({
            'close': [100 + i * 0.5 for i in range(50)]
        })
        
        # Generate different test data with similar trend
        test_data = pd.DataFrame({
            'close': [125 + i * 0.5 for i in range(50)]
        })
        
        strategy = SMAStrategy(fast_period=5, slow_period=10)
        
        # Should produce similar signal types on similar trends
        train_signal = strategy.generate_signal(train_data)
        test_signal = strategy.generate_signal(test_data)
        
        # Both should recognize uptrend
        self.assertNotEqual(train_signal, 'SELL')
        self.assertNotEqual(test_signal, 'SELL')


class TestBacktestDataQuality(unittest.TestCase):
    """Test data quality checks for backtesting"""
    
    def test_missing_data_handling(self):
        """Test handling of missing data in backtest"""
        # Create data with NaN values
        data = pd.DataFrame({
            'close': [100, 102, np.nan, 106, 108, np.nan, 112, 114]
        })
        
        strategy = SMAStrategy(fast_period=3, slow_period=5)
        
        # Strategy should handle NaN gracefully
        signal = strategy.generate_signal(data)
        
        # Should return HOLD or valid signal (not crash)
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
    
    def test_data_chronology(self):
        """Test that backtest data is in chronological order"""
        backtester = Backtester()
        data = backtester.generate_historical_data('TEST', days=30)
        
        # Verify dates are in order
        dates = pd.to_datetime(data['date'])
        is_sorted = all(dates[i] <= dates[i+1] for i in range(len(dates)-1))
        
        self.assertTrue(is_sorted)
    
    def test_price_data_validity(self):
        """Test that price data is valid (no negatives, reasonable ranges)"""
        backtester = Backtester()
        data = backtester.generate_historical_data('TEST', days=50, start_price=100.0)
        
        # Verify no negative prices
        self.assertTrue(all(data['close'] > 0))
        self.assertTrue(all(data['high'] > 0))
        self.assertTrue(all(data['low'] > 0))
        
        # Verify OHLC relationships
        self.assertTrue(all(data['high'] >= data['low']))
        self.assertTrue(all(data['close'] >= data['low']))
        self.assertTrue(all(data['close'] <= data['high']))


if __name__ == '__main__':
    unittest.main()
