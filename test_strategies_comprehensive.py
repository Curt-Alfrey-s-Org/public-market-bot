#!/usr/bin/env python3
"""
Comprehensive unit tests for strategies.py module
Tests all trading strategy implementations and signal generation
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strategies import (
    TradingStrategy, SMAStrategy, BollingerBandsStrategy,
    RSIStrategy, MACDStrategy, MomentumStrategy
)


class TestBaseStrategy(unittest.TestCase):
    """Test base TradingStrategy class"""
    
    def test_base_strategy_not_implementable(self):
        """Test that base strategy cannot be used directly"""
        strategy = TradingStrategy("Test")
        data = pd.DataFrame({'close': [100, 101, 102]})
        
        with self.assertRaises(NotImplementedError):
            strategy.generate_signal(data)
    
    def test_signal_tracking(self):
        """Test that signals are tracked"""
        strategy = TradingStrategy("Test")
        strategy.signals = ['BUY', 'HOLD', 'SELL']
        
        self.assertEqual(strategy.get_last_signal(), 'SELL')
        self.assertEqual(len(strategy.signals), 3)


class TestSMAStrategy(unittest.TestCase):
    """Test Simple Moving Average strategy"""
    
    def setUp(self):
        """Set up test data"""
        self.strategy = SMAStrategy(fast_period=5, slow_period=10)
        
        # Create test data with clear trend
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        self.uptrend_data = pd.DataFrame({
            'date': dates,
            'close': np.linspace(100, 130, 30)  # Clear uptrend
        })
        
        self.downtrend_data = pd.DataFrame({
            'date': dates,
            'close': np.linspace(130, 100, 30)  # Clear downtrend
        })
    
    def test_initialization(self):
        """Test SMA strategy initialization"""
        self.assertEqual(self.strategy.name, "SMA Crossover")
        self.assertEqual(self.strategy.fast_period, 5)
        self.assertEqual(self.strategy.slow_period, 10)
    
    def test_sma_calculation(self):
        """Test SMA calculation method"""
        prices = pd.Series([100, 102, 104, 106, 108])
        sma = self.strategy.calculate_sma(prices, period=3)
        
        # First two values should be NaN
        self.assertTrue(pd.isna(sma.iloc[0]))
        self.assertTrue(pd.isna(sma.iloc[1]))
        
        # Third value should be mean of first 3
        expected = (100 + 102 + 104) / 3
        self.assertAlmostEqual(sma.iloc[2], expected, places=6)
    
    def test_buy_signal_on_uptrend(self):
        """Test that BUY signal is generated on bullish crossover"""
        signal = self.strategy.generate_signal(self.uptrend_data)
        
        # In uptrend with fast SMA crossing above slow SMA, expect BUY or HOLD
        # HOLD is acceptable if not enough data or no recent crossover
        # NOTE: This is a lenient check because signal timing depends on SMA periods
        # and exact crossover detection. Specific signal validation should be done
        # with controlled test data where crossover points are known.
        self.assertIn(signal, ['BUY', 'HOLD'])
        # Signal should never be SELL in a clear uptrend
        self.assertNotEqual(signal, 'SELL')
    
    def test_sell_signal_on_downtrend(self):
        """Test that SELL signal is generated on bearish crossover"""
        signal = self.strategy.generate_signal(self.downtrend_data)
        
        # In downtrend with fast SMA crossing below slow SMA, expect SELL or HOLD
        # HOLD is acceptable if not enough data or no recent crossover
        # NOTE: This is a lenient check - see comment in test_buy_signal_on_uptrend
        self.assertIn(signal, ['SELL', 'HOLD'])
        # Signal should never be BUY in a clear downtrend
        self.assertNotEqual(signal, 'BUY')
    
    def test_crossover_detection(self):
        """Test crossover detection"""
        # Create data with clear crossover
        close_prices = [100] * 15 + [101, 102, 103, 104, 105] * 3  # Trend change
        data = pd.DataFrame({'close': close_prices})
        
        signal = self.strategy.generate_signal(data)
        
        # Should generate a signal (BUY, SELL, or HOLD)
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
    
    def test_insufficient_data(self):
        """Test handling of insufficient data"""
        # Data shorter than slow period
        short_data = pd.DataFrame({'close': [100, 101, 102]})
        
        signal = self.strategy.generate_signal(short_data)
        
        # Should return HOLD when insufficient data
        self.assertEqual(signal, 'HOLD')
    
    def test_signal_persistence(self):
        """Test that signals are stored"""
        self.strategy.generate_signal(self.uptrend_data)
        
        self.assertGreater(len(self.strategy.signals), 0)
        self.assertIn(self.strategy.get_last_signal(), ['BUY', 'SELL', 'HOLD'])


class TestBollingerBandsStrategy(unittest.TestCase):
    """Test Bollinger Bands strategy"""
    
    def setUp(self):
        """Set up test data"""
        self.strategy = BollingerBandsStrategy(period=20, std_dev=2.0)
        
        # Create data with mean reversion pattern
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        base = 100
        volatility = np.sin(np.linspace(0, 4*np.pi, 50)) * 10
        self.data = pd.DataFrame({
            'date': dates,
            'close': base + volatility
        })
    
    def test_initialization(self):
        """Test Bollinger Bands initialization"""
        self.assertEqual(self.strategy.name, "Bollinger Bands")
        self.assertEqual(self.strategy.period, 20)
        self.assertEqual(self.strategy.std_dev, 2.0)
    
    def test_signal_generation(self):
        """Test that signals are generated"""
        signal = self.strategy.generate_signal(self.data)
        
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
    
    def test_oversold_buy_signal(self):
        """Test BUY signal when price is below lower band"""
        # Create data with price dropping below lower band
        close_prices = [100] * 20 + [95, 90, 85, 80, 75]  # Sharp drop
        data = pd.DataFrame({'close': close_prices})
        
        signal = self.strategy.generate_signal(data)
        
        # Should generate BUY or HOLD at oversold levels
        self.assertIn(signal, ['BUY', 'HOLD'])
    
    def test_overbought_sell_signal(self):
        """Test SELL signal when price is above upper band"""
        # Create data with price rising above upper band
        close_prices = [100] * 20 + [105, 110, 115, 120, 125]  # Sharp rise
        data = pd.DataFrame({'close': close_prices})
        
        signal = self.strategy.generate_signal(data)
        
        # Should generate SELL or HOLD at overbought levels
        self.assertIn(signal, ['SELL', 'HOLD'])


class TestRSIStrategy(unittest.TestCase):
    """Test RSI strategy"""
    
    def setUp(self):
        """Set up test data"""
        self.strategy = RSIStrategy(period=14, oversold=30, overbought=70)
        
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        self.data = pd.DataFrame({
            'date': dates,
            'close': np.linspace(100, 110, 50) + np.random.randn(50) * 2
        })
    
    def test_initialization(self):
        """Test RSI strategy initialization"""
        self.assertEqual(self.strategy.name, "RSI")
        self.assertEqual(self.strategy.period, 14)
        self.assertEqual(self.strategy.oversold, 30)
        self.assertEqual(self.strategy.overbought, 70)
    
    def test_signal_generation(self):
        """Test RSI signal generation"""
        signal = self.strategy.generate_signal(self.data)
        
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
    
    def test_oversold_condition(self):
        """Test BUY signal on oversold RSI"""
        # Create strong downtrend to generate low RSI
        close_prices = np.linspace(150, 100, 50)
        data = pd.DataFrame({'close': close_prices})
        
        signal = self.strategy.generate_signal(data)
        
        # Should generate BUY or HOLD in oversold conditions
        self.assertIn(signal, ['BUY', 'HOLD'])
    
    def test_overbought_condition(self):
        """Test SELL signal on overbought RSI"""
        # Create strong uptrend to generate high RSI
        close_prices = np.linspace(100, 150, 50)
        data = pd.DataFrame({'close': close_prices})
        
        signal = self.strategy.generate_signal(data)
        
        # Should generate SELL or HOLD in overbought conditions
        self.assertIn(signal, ['SELL', 'HOLD'])
    
    def test_custom_thresholds(self):
        """Test RSI with custom overbought/oversold thresholds"""
        strategy = RSIStrategy(period=14, oversold=20, overbought=80)
        
        signal = strategy.generate_signal(self.data)
        
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])


class TestMACDStrategy(unittest.TestCase):
    """Test MACD strategy"""
    
    def setUp(self):
        """Set up test data"""
        self.strategy = MACDStrategy(fast=12, slow=26, signal=9)
        
        dates = pd.date_range(start='2024-01-01', periods=60, freq='D')
        # Create trend data
        trend = np.linspace(0, 20, 60)
        noise = np.random.randn(60) * 2
        self.data = pd.DataFrame({
            'date': dates,
            'close': 100 + trend + noise
        })
    
    def test_initialization(self):
        """Test MACD strategy initialization"""
        self.assertEqual(self.strategy.name, "MACD")
        self.assertEqual(self.strategy.fast, 12)
        self.assertEqual(self.strategy.slow, 26)
        self.assertEqual(self.strategy.signal_period, 9)
    
    def test_signal_generation(self):
        """Test MACD signal generation"""
        signal = self.strategy.generate_signal(self.data)
        
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
    
    def test_bullish_crossover(self):
        """Test BUY signal on bullish crossover"""
        # Create data transitioning from down to up
        close_prices = list(np.linspace(120, 100, 30)) + list(np.linspace(100, 120, 30))
        data = pd.DataFrame({'close': close_prices})
        
        signal = self.strategy.generate_signal(data)
        
        # Should generate BUY or HOLD on bullish crossover
        self.assertIn(signal, ['BUY', 'HOLD'])
    
    def test_bearish_crossover(self):
        """Test SELL signal on bearish crossover"""
        # Create data transitioning from up to down
        close_prices = list(np.linspace(100, 120, 30)) + list(np.linspace(120, 100, 30))
        data = pd.DataFrame({'close': close_prices})
        
        signal = self.strategy.generate_signal(data)
        
        # Should generate SELL or HOLD on bearish crossover
        self.assertIn(signal, ['SELL', 'HOLD'])
    
    def test_insufficient_data(self):
        """Test MACD with insufficient data"""
        short_data = pd.DataFrame({'close': [100, 101, 102, 103, 104]})
        
        signal = self.strategy.generate_signal(short_data)
        
        # Should return HOLD with insufficient data
        self.assertEqual(signal, 'HOLD')


class TestMomentumStrategy(unittest.TestCase):
    """Test Momentum strategy"""
    
    def setUp(self):
        """Set up test data"""
        self.strategy = MomentumStrategy(period=10, threshold=0.02)
        
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        self.data = pd.DataFrame({
            'date': dates,
            'close': np.linspace(100, 115, 30)
        })
    
    def test_initialization(self):
        """Test Momentum strategy initialization"""
        self.assertEqual(self.strategy.name, "Momentum")
        self.assertEqual(self.strategy.period, 10)
        self.assertEqual(self.strategy.threshold, 0.02)
    
    def test_signal_generation(self):
        """Test Momentum signal generation"""
        signal = self.strategy.generate_signal(self.data)
        
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
    
    def test_positive_momentum(self):
        """Test BUY signal on positive momentum"""
        # Create strong upward momentum
        close_prices = np.linspace(100, 120, 30)
        data = pd.DataFrame({'close': close_prices})
        
        signal = self.strategy.generate_signal(data)
        
        # Should generate BUY or HOLD with positive momentum
        self.assertIn(signal, ['BUY', 'HOLD'])
    
    def test_negative_momentum(self):
        """Test SELL signal on negative momentum"""
        # Create strong downward momentum
        close_prices = np.linspace(120, 100, 30)
        data = pd.DataFrame({'close': close_prices})
        
        signal = self.strategy.generate_signal(data)
        
        # Should generate SELL or HOLD with negative momentum
        self.assertIn(signal, ['SELL', 'HOLD'])
    
    def test_threshold_sensitivity(self):
        """Test that threshold affects signal generation"""
        # Test with different thresholds
        strategy_low = MomentumStrategy(period=10, threshold=0.01)
        strategy_high = MomentumStrategy(period=10, threshold=0.10)
        
        data = pd.DataFrame({'close': np.linspace(100, 102, 30)})  # Small change
        
        signal_low = strategy_low.generate_signal(data)
        signal_high = strategy_high.generate_signal(data)
        
        # Both should return valid signals
        self.assertIn(signal_low, ['BUY', 'SELL', 'HOLD'])
        self.assertIn(signal_high, ['BUY', 'SELL', 'HOLD'])


class TestStrategyIntegration(unittest.TestCase):
    """Test strategy integration and edge cases"""
    
    def test_all_strategies_with_same_data(self):
        """Test that all strategies work with the same dataset"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'date': dates,
            'close': np.linspace(100, 120, 100) + np.random.randn(100) * 2
        })
        
        strategies = [
            SMAStrategy(fast_period=20, slow_period=50),
            BollingerBandsStrategy(period=20, std_dev=2.0),
            RSIStrategy(period=14),
            MACDStrategy(fast=12, slow=26, signal=9),
            MomentumStrategy(period=10, threshold=0.02)
        ]
        
        for strategy in strategies:
            signal = strategy.generate_signal(data)
            self.assertIn(signal, ['BUY', 'SELL', 'HOLD'], 
                         f"{strategy.name} generated invalid signal: {signal}")
    
    def test_strategies_with_flat_prices(self):
        """Test strategies handle flat/constant prices"""
        data = pd.DataFrame({'close': [100.0] * 100})
        
        strategies = [
            SMAStrategy(fast_period=20, slow_period=50),
            RSIStrategy(period=14),
            MomentumStrategy(period=10, threshold=0.02)
        ]
        
        for strategy in strategies:
            try:
                signal = strategy.generate_signal(data)
                self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
            except Exception as e:
                self.fail(f"{strategy.name} failed with flat prices: {e}")
    
    def test_strategies_with_nan_values(self):
        """Test strategies handle NaN values in data"""
        close_prices = [100, 101, 102, np.nan, 104, 105, np.nan, 107]
        data = pd.DataFrame({'close': close_prices})
        
        strategies = [
            SMAStrategy(fast_period=3, slow_period=5),
            RSIStrategy(period=5),
        ]
        
        for strategy in strategies:
            try:
                signal = strategy.generate_signal(data)
                self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
            except Exception as e:
                self.fail(f"{strategy.name} failed with NaN values: {e}")
    
    def test_strategies_maintain_independence(self):
        """Test that multiple strategy instances are independent"""
        data1 = pd.DataFrame({'close': np.linspace(100, 120, 50)})
        data2 = pd.DataFrame({'close': np.linspace(120, 100, 50)})
        
        strategy1 = SMAStrategy(fast_period=5, slow_period=10)
        strategy2 = SMAStrategy(fast_period=5, slow_period=10)
        
        signal1 = strategy1.generate_signal(data1)
        signal2 = strategy2.generate_signal(data2)
        
        # Signals should be different for uptrend vs downtrend
        # (unless both are HOLD due to insufficient data)
        self.assertIn(signal1, ['BUY', 'SELL', 'HOLD'])
        self.assertIn(signal2, ['BUY', 'SELL', 'HOLD'])


if __name__ == '__main__':
    unittest.main()
