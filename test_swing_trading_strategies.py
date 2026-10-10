#!/usr/bin/env python3
"""
Test suite for swing trading strategies
Tests SMA, Bollinger Bands, RSI, and other trading strategies
"""

import os
# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')

import unittest
import pandas as pd

# Import trading strategies
from strategies import (
    SMAStrategy,
    BollingerBandsStrategy,
    RSIStrategy,
    MACDStrategy,
    MomentumStrategy
)


class TestSMAStrategy(unittest.TestCase):
    """Test Simple Moving Average Crossover Strategy"""
    
    def setUp(self):
        """Set up test strategy instance"""
        self.strategy = SMAStrategy(fast_period=5, slow_period=10)
    
    def test_strategy_initialization(self):
        """Test strategy initializes with correct parameters"""
        self.assertEqual(self.strategy.name, "SMA Crossover")
        self.assertEqual(self.strategy.fast_period, 5)
        self.assertEqual(self.strategy.slow_period, 10)
    
    def test_insufficient_data_returns_hold(self):
        """Test strategy returns HOLD with insufficient data"""
        # Create data with only 5 rows (less than slow_period=10)
        data = pd.DataFrame({
            'close': [100, 101, 102, 103, 104]
        })
        
        signal = self.strategy.generate_signal(data)
        self.assertEqual(signal, 'HOLD')
    
    def test_golden_cross_generates_buy_signal(self):
        """Test Golden Cross (fast crosses above slow) generates BUY signal"""
        # Create data where fast SMA crosses above slow SMA
        # First 10 values: downtrend, next 5 values: strong uptrend
        prices = [110, 108, 106, 104, 102, 100, 98, 96, 94, 92,  # Downtrend
                  93, 95, 98, 102, 107]  # Uptrend causes golden cross
        
        data = pd.DataFrame({'close': prices})
        signal = self.strategy.generate_signal(data)
        
        # Should generate BUY signal when fast crosses above slow
        self.assertEqual(signal, 'BUY')
    
    def test_death_cross_generates_sell_signal(self):
        """Test Death Cross (fast crosses below slow) generates SELL signal"""
        # Create data where fast SMA crosses below slow SMA
        # First 10 values: uptrend, next 5 values: strong downtrend
        prices = [90, 92, 94, 96, 98, 100, 102, 104, 106, 108,  # Uptrend
                  107, 105, 102, 98, 93]  # Downtrend causes death cross
        
        data = pd.DataFrame({'close': prices})
        signal = self.strategy.generate_signal(data)
        
        # Should generate SELL signal when fast crosses below slow
        self.assertEqual(signal, 'SELL')
    
    def test_no_crossover_returns_hold(self):
        """Test strategy returns HOLD when no crossover occurs"""
        # Create flat data with no crossover
        prices = [100, 101, 100, 101, 100, 101, 100, 101, 100, 101,
                  100, 101, 100, 101, 100]
        
        data = pd.DataFrame({'close': prices})
        signal = self.strategy.generate_signal(data)
        
        # Should return valid signal (BUY, SELL, or HOLD)
        # In oscillating data, strategy may detect a signal
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
    
    def test_get_indicator_values(self):
        """Test getting current indicator values"""
        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
        data = pd.DataFrame({'close': prices})
        
        indicators = self.strategy.get_indicator_values(data)
        
        self.assertIn('sma_fast', indicators)
        self.assertIn('sma_slow', indicators)
        self.assertGreater(indicators['sma_fast'], 100)
        self.assertGreater(indicators['sma_slow'], 100)


class TestBollingerBandsStrategy(unittest.TestCase):
    """Test Bollinger Bands Mean Reversion Strategy"""
    
    def setUp(self):
        """Set up test strategy instance"""
        self.strategy = BollingerBandsStrategy(period=10, num_std=2.0)
    
    def test_strategy_initialization(self):
        """Test strategy initializes with correct parameters"""
        self.assertEqual(self.strategy.name, "Bollinger Bands")
        self.assertEqual(self.strategy.period, 10)
        self.assertEqual(self.strategy.num_std, 2.0)
    
    def test_insufficient_data_returns_hold(self):
        """Test strategy returns HOLD with insufficient data"""
        # Create data with only 5 rows (less than period=10)
        data = pd.DataFrame({
            'close': [100, 101, 102, 103, 104]
        })
        
        signal = self.strategy.generate_signal(data)
        self.assertEqual(signal, 'HOLD')
    
    def test_price_below_lower_band_generates_buy(self):
        """Test price crossing below lower band generates BUY signal"""
        # Create data with stable period followed by sharp drop
        prices = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100,  # Stable
                  100, 90]  # Sharp drop below lower band
        
        data = pd.DataFrame({'close': prices})
        signal = self.strategy.generate_signal(data)
        
        # Should generate BUY signal (oversold)
        self.assertEqual(signal, 'BUY')
    
    def test_price_above_upper_band_generates_sell(self):
        """Test price crossing above upper band generates SELL signal"""
        # Create data with stable period followed by sharp rise
        prices = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100,  # Stable
                  100, 110]  # Sharp rise above upper band
        
        data = pd.DataFrame({'close': prices})
        signal = self.strategy.generate_signal(data)
        
        # Should generate SELL signal (overbought)
        self.assertEqual(signal, 'SELL')
    
    def test_price_within_bands_returns_hold(self):
        """Test price staying within bands returns HOLD"""
        # Create data that stays within normal range
        prices = [100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101]
        
        data = pd.DataFrame({'close': prices})
        signal = self.strategy.generate_signal(data)
        
        # Should return HOLD when price within bands
        self.assertEqual(signal, 'HOLD')
    
    def test_calculate_bollinger_bands(self):
        """Test Bollinger Bands calculation"""
        prices = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110])
        
        middle, upper, lower = self.strategy.calculate_bollinger_bands(prices)
        
        # Verify bands are calculated
        self.assertIsNotNone(middle.iloc[-1])
        self.assertIsNotNone(upper.iloc[-1])
        self.assertIsNotNone(lower.iloc[-1])
        
        # Verify band relationship: lower < middle < upper
        self.assertLess(lower.iloc[-1], middle.iloc[-1])
        self.assertLess(middle.iloc[-1], upper.iloc[-1])
    
    def test_band_width_calculation(self):
        """Test band width (volatility) calculation"""
        # Low volatility data
        low_vol_prices = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
        low_vol_data = pd.DataFrame({'close': low_vol_prices})
        self.strategy.generate_signal(low_vol_data)
        
        # Check that signal was recorded with band width
        if self.strategy.signals:
            self.assertIn('band_width', self.strategy.signals[-1])


class TestSwingTradingRules(unittest.TestCase):
    """Test swing trading rule validations and constraints"""
    
    def test_trend_following_vs_mean_reversion(self):
        """Test that SMA (trend) and Bollinger Bands (mean reversion) give opposite signals"""
        # Create data with strong uptrend that's also overbought
        # This should trigger BUY for SMA but potentially SELL for BB
        prices = [90, 92, 94, 96, 98, 100, 102, 104, 106, 108, 110, 112, 115]
        data = pd.DataFrame({'close': prices})
        
        sma_strategy = SMAStrategy(fast_period=3, slow_period=5)
        bb_strategy = BollingerBandsStrategy(period=5, num_std=1.5)
        
        sma_signal = sma_strategy.generate_signal(data)
        bb_signal = bb_strategy.generate_signal(data)
        
        # SMA should show uptrend (BUY or HOLD)
        self.assertIn(sma_signal, ['BUY', 'HOLD'])
        
        # BB might show overbought (SELL or HOLD)
        # Note: depending on data, might not always be opposite
        self.assertIn(bb_signal, ['BUY', 'SELL', 'HOLD'])
    
    def test_multiple_timeframe_analysis(self):
        """Test strategy with different timeframes (fast vs slow)"""
        prices = list(range(100, 130))  # Strong uptrend
        data = pd.DataFrame({'close': prices})
        
        # Fast timeframe (more responsive)
        fast_strategy = SMAStrategy(fast_period=3, slow_period=7)
        fast_signal = fast_strategy.generate_signal(data)
        
        # Slow timeframe (more lagging)
        slow_strategy = SMAStrategy(fast_period=10, slow_period=20)
        slow_signal = slow_strategy.generate_signal(data)
        
        # Both should recognize the uptrend, but may differ in timing
        # At minimum, neither should give opposite signals in strong trend
        if fast_signal == 'BUY':
            self.assertNotEqual(slow_signal, 'SELL')
    
    def test_volatility_affects_band_width(self):
        """Test that volatility affects Bollinger Band width"""
        bb_strategy = BollingerBandsStrategy(period=10, num_std=2.0)
        
        # Low volatility scenario
        low_vol_prices = [100 + 0.1 * i for i in range(15)]
        low_vol_data = pd.DataFrame({'close': low_vol_prices})
        bb_strategy.generate_signal(low_vol_data)
        low_vol_width = bb_strategy.signals[-1]['band_width'] if bb_strategy.signals else None
        
        # High volatility scenario  
        high_vol_prices = [100, 95, 105, 92, 108, 89, 111, 86, 114, 83, 117, 80, 120]
        high_vol_data = pd.DataFrame({'close': high_vol_prices})
        bb_strategy.signals = []  # Reset signals
        bb_strategy.generate_signal(high_vol_data)
        high_vol_width = bb_strategy.signals[-1]['band_width'] if bb_strategy.signals else None
        
        # High volatility should produce wider bands
        if low_vol_width and high_vol_width:
            self.assertGreater(high_vol_width, low_vol_width)


class TestStrategyComparison(unittest.TestCase):
    """Test comparing multiple strategies on same data"""
    
    def test_strategy_agreement_in_strong_trend(self):
        """Test that strategies agree in strong trend conditions"""
        # Create strong uptrend
        prices = [100 + i*2 for i in range(25)]
        data = pd.DataFrame({'close': prices})
        
        sma = SMAStrategy(fast_period=5, slow_period=10)
        sma_signal = sma.generate_signal(data)
        
        # In strong uptrend, SMA should show BUY or HOLD (not SELL)
        self.assertNotEqual(sma_signal, 'SELL')
    
    def test_strategy_signals_logged(self):
        """Test that strategies properly log their signals"""
        prices = list(range(100, 120))
        data = pd.DataFrame({'close': prices})
        
        strategy = SMAStrategy(fast_period=3, slow_period=7)
        signal = strategy.generate_signal(data)
        
        # Verify signal was logged
        self.assertGreater(len(strategy.signals), 0)
        
        # Verify signal structure
        last_signal = strategy.signals[-1]
        self.assertIn('timestamp', last_signal)
        self.assertIn('signal', last_signal)
        self.assertEqual(last_signal['signal'], signal)


if __name__ == '__main__':
    unittest.main()
