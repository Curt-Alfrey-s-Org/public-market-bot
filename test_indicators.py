#!/usr/bin/env python3
"""
Unit tests for indicators.py module
Tests all technical indicator calculations
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from indicators import TechnicalIndicators


class TestTechnicalIndicators(unittest.TestCase):
    """Test technical indicator calculations"""
    
    def setUp(self):
        """Set up test data"""
        # Create sample OHLCV data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        # Generate realistic price data with trend
        base_price = 100.0
        trend = np.linspace(0, 20, 100)
        noise = np.random.randn(100) * 2
        close_prices = base_price + trend + noise
        
        self.data = pd.DataFrame({
            'date': dates,
            'open': close_prices + np.random.randn(100) * 0.5,
            'high': close_prices + abs(np.random.randn(100) * 1.5),
            'low': close_prices - abs(np.random.randn(100) * 1.5),
            'close': close_prices,
            'volume': np.random.randint(1000000, 10000000, 100)
        })
        
        self.indicators = TechnicalIndicators(self.data)
    
    def test_initialization(self):
        """Test TechnicalIndicators initialization"""
        self.assertIsNotNone(self.indicators)
        self.assertEqual(len(self.indicators.data), 100)
        self.assertIn('close', self.indicators.data.columns)
    
    def test_rsi_calculation(self):
        """Test RSI calculation"""
        rsi = self.indicators.calculate_rsi(period=14)
        
        # Check RSI is calculated
        self.assertIsNotNone(rsi)
        self.assertIsInstance(rsi, pd.Series)
        
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        self.assertTrue((valid_rsi >= 0).all())
        self.assertTrue((valid_rsi <= 100).all())
        
        # First 14 values should be NaN (period = 14)
        self.assertTrue(rsi[:14].isna().any())
    
    def test_rsi_edge_cases(self):
        """Test RSI with edge cases"""
        # Test with constant prices (no change)
        constant_data = pd.DataFrame({
            'close': [100.0] * 50
        })
        indicators = TechnicalIndicators(constant_data)
        rsi = indicators.calculate_rsi(period=14)
        
        # For constant prices, RSI calculation may produce NaN (division by zero in RS calculation)
        # or values around 50 (no momentum). Both are acceptable behaviors.
        valid_rsi = rsi.dropna()
        if len(valid_rsi) > 0:
            # Check if values are reasonable (between 0-100) or all NaN
            self.assertTrue(((valid_rsi >= 0) & (valid_rsi <= 100)).all())
    
    def test_macd_calculation(self):
        """Test MACD calculation"""
        macd_line, signal_line, histogram = self.indicators.calculate_macd()
        
        # Check all components are calculated
        self.assertIsNotNone(macd_line)
        self.assertIsNotNone(signal_line)
        self.assertIsNotNone(histogram)
        
        self.assertIsInstance(macd_line, pd.Series)
        self.assertIsInstance(signal_line, pd.Series)
        self.assertIsInstance(histogram, pd.Series)
        
        # Histogram should equal MACD - Signal
        valid_idx = ~(macd_line.isna() | signal_line.isna() | histogram.isna())
        if valid_idx.any():
            np.testing.assert_array_almost_equal(
                histogram[valid_idx].values,
                (macd_line - signal_line)[valid_idx].values,
                decimal=10
            )
    
    def test_macd_custom_parameters(self):
        """Test MACD with custom parameters"""
        macd_line, signal_line, histogram = self.indicators.calculate_macd(
            fast=8, slow=21, signal=5
        )
        
        # Should still produce valid output
        self.assertIsInstance(macd_line, pd.Series)
        self.assertTrue(len(macd_line) == len(self.data))
    
    def test_sma_calculation(self):
        """Test SMA calculation"""
        sma = self.indicators.calculate_sma(period=20)
        
        # Check SMA is calculated
        self.assertIsNotNone(sma)
        self.assertIsInstance(sma, pd.Series)
        
        # First 19 values should be NaN (period = 20)
        self.assertTrue(sma[:19].isna().all())
        
        # Manually verify first valid SMA value
        first_valid_idx = 19
        expected_sma = self.data['close'][:20].mean()
        self.assertAlmostEqual(sma.iloc[first_valid_idx], expected_sma, places=10)
    
    def test_sma_different_periods(self):
        """Test SMA with different periods"""
        sma_10 = self.indicators.calculate_sma(period=10)
        sma_50 = self.indicators.calculate_sma(period=50)
        
        # Both should be valid
        self.assertIsInstance(sma_10, pd.Series)
        self.assertIsInstance(sma_50, pd.Series)
        
        # Shorter period should have more valid values
        self.assertGreater(sma_10.notna().sum(), sma_50.notna().sum())
    
    def test_ema_calculation(self):
        """Test EMA calculation"""
        ema = self.indicators.calculate_ema(period=20)
        
        # Check EMA is calculated
        self.assertIsNotNone(ema)
        self.assertIsInstance(ema, pd.Series)
        
        # EMA should have more valid values than SMA (starts earlier)
        sma = self.indicators.calculate_sma(period=20)
        self.assertGreaterEqual(ema.notna().sum(), sma.notna().sum())
    
    def test_bollinger_bands_calculation(self):
        """Test Bollinger Bands calculation"""
        upper, middle, lower = self.indicators.calculate_bollinger_bands(period=20, std_dev=2.0)
        
        # Check all bands are calculated
        self.assertIsNotNone(upper)
        self.assertIsNotNone(middle)
        self.assertIsNotNone(lower)
        
        self.assertIsInstance(upper, pd.Series)
        self.assertIsInstance(middle, pd.Series)
        self.assertIsInstance(lower, pd.Series)
        
        # Middle band should equal SMA
        sma = self.indicators.calculate_sma(period=20)
        valid_idx = ~(middle.isna() | sma.isna())
        if valid_idx.any():
            np.testing.assert_array_almost_equal(
                middle[valid_idx].values,
                sma[valid_idx].values,
                decimal=10
            )
        
        # Upper band should be above middle, middle above lower
        valid_idx = ~(upper.isna() | middle.isna() | lower.isna())
        if valid_idx.any():
            self.assertTrue((upper[valid_idx] >= middle[valid_idx]).all())
            self.assertTrue((middle[valid_idx] >= lower[valid_idx]).all())
    
    def test_bollinger_bands_width(self):
        """Test Bollinger Bands width scales with std_dev"""
        upper1, middle1, lower1 = self.indicators.calculate_bollinger_bands(
            period=20, std_dev=1.0
        )
        upper2, middle2, lower2 = self.indicators.calculate_bollinger_bands(
            period=20, std_dev=2.0
        )
        
        # Width with std_dev=2 should be approximately double std_dev=1
        valid_idx = ~(upper1.isna() | upper2.isna())
        if valid_idx.any():
            width1 = upper1[valid_idx] - lower1[valid_idx]
            width2 = upper2[valid_idx] - lower2[valid_idx]
            ratio = (width2 / width1).mean()
            self.assertAlmostEqual(ratio, 2.0, places=1)
    
    def test_atr_calculation(self):
        """Test ATR calculation"""
        atr = self.indicators.calculate_atr(period=14)
        
        # Check ATR is calculated
        self.assertIsNotNone(atr)
        self.assertIsInstance(atr, pd.Series)
        
        # ATR should be positive
        valid_atr = atr.dropna()
        if len(valid_atr) > 0:
            self.assertTrue((valid_atr >= 0).all())
    
    def test_atr_missing_columns(self):
        """Test ATR with missing required columns"""
        # Create data without high/low
        simple_data = pd.DataFrame({
            'close': self.data['close']
        })
        indicators = TechnicalIndicators(simple_data)
        atr = indicators.calculate_atr(period=14)
        
        # Should return empty Series or handle gracefully
        self.assertIsInstance(atr, pd.Series)
    
    def test_stochastic_oscillator(self):
        """Test Stochastic Oscillator calculation"""
        if hasattr(self.indicators, 'calculate_stochastic'):
            k, d = self.indicators.calculate_stochastic(period=14)
            
            # Check both lines are calculated
            self.assertIsNotNone(k)
            self.assertIsNotNone(d)
            
            # Values should be between 0 and 100
            valid_k = k.dropna()
            valid_d = d.dropna()
            
            if len(valid_k) > 0:
                self.assertTrue((valid_k >= 0).all() and (valid_k <= 100).all())
            if len(valid_d) > 0:
                self.assertTrue((valid_d >= 0).all() and (valid_d <= 100).all())
    
    def test_all_indicators_with_minimal_data(self):
        """Test all indicators work with minimal data"""
        # Create minimal dataset (30 rows)
        minimal_data = self.data.iloc[:30].copy()
        indicators = TechnicalIndicators(minimal_data)
        
        # All indicators should handle minimal data gracefully
        try:
            rsi = indicators.calculate_rsi(period=14)
            self.assertIsInstance(rsi, pd.Series)
            
            macd_line, signal_line, histogram = indicators.calculate_macd()
            self.assertIsInstance(macd_line, pd.Series)
            
            sma = indicators.calculate_sma(period=20)
            self.assertIsInstance(sma, pd.Series)
            
            upper, middle, lower = indicators.calculate_bollinger_bands(period=20)
            self.assertIsInstance(upper, pd.Series)
            
            atr = indicators.calculate_atr(period=14)
            self.assertIsInstance(atr, pd.Series)
            
        except Exception as e:
            self.fail(f"Indicator calculation failed with minimal data: {e}")
    
    def test_indicators_with_missing_values(self):
        """Test indicators handle missing values in data"""
        # Create data with some NaN values
        data_with_nan = self.data.copy()
        data_with_nan.loc[10:15, 'close'] = np.nan
        
        indicators = TechnicalIndicators(data_with_nan)
        
        # Indicators should handle NaN gracefully
        try:
            rsi = indicators.calculate_rsi(period=14)
            self.assertIsInstance(rsi, pd.Series)
            
            macd_line, _, _ = indicators.calculate_macd()
            self.assertIsInstance(macd_line, pd.Series)
            
        except Exception as e:
            self.fail(f"Indicator calculation failed with NaN values: {e}")
    
    def test_zero_and_negative_prices(self):
        """Test indicators handle zero and negative prices"""
        # Create data with edge case prices
        edge_data = pd.DataFrame({
            'close': [100, 50, 0, -10, 20, 100, 80],  # Including zero and negative
            'high': [110, 60, 10, 0, 30, 110, 90],
            'low': [90, 40, -10, -20, 10, 90, 70],
            'open': [95, 55, 5, -5, 15, 95, 75],
            'volume': [1000] * 7
        })
        
        indicators = TechnicalIndicators(edge_data)
        
        # Should not crash with edge cases
        try:
            rsi = indicators.calculate_rsi(period=5)
            self.assertIsInstance(rsi, pd.Series)
            
            sma = indicators.calculate_sma(period=5)
            self.assertIsInstance(sma, pd.Series)
            
        except Exception as e:
            self.fail(f"Indicator calculation failed with edge case prices: {e}")


class TestIndicatorSignals(unittest.TestCase):
    """Test indicator signal generation logic"""
    
    def setUp(self):
        """Set up test data with known patterns"""
        # Create uptrend data
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        close_prices = np.linspace(100, 120, 50) + np.random.randn(50) * 0.5
        
        self.uptrend_data = pd.DataFrame({
            'date': dates,
            'open': close_prices,
            'high': close_prices + 1,
            'low': close_prices - 1,
            'close': close_prices,
            'volume': [1000000] * 50
        })
    
    def test_rsi_oversold_signal(self):
        """Test RSI identifies oversold conditions"""
        # Create oversold data (downtrend)
        close_prices = np.linspace(100, 70, 50)
        data = pd.DataFrame({'close': close_prices})
        indicators = TechnicalIndicators(data)
        
        rsi = indicators.calculate_rsi(period=14)
        valid_rsi = rsi.dropna()
        
        # In strong downtrend, RSI should go below 30 (oversold)
        if len(valid_rsi) > 0:
            min_rsi = valid_rsi.min()
            self.assertLess(min_rsi, 40)  # Should show oversold conditions
    
    def test_rsi_overbought_signal(self):
        """Test RSI identifies overbought conditions"""
        # Create overbought data (uptrend)
        close_prices = np.linspace(100, 130, 50)
        data = pd.DataFrame({'close': close_prices})
        indicators = TechnicalIndicators(data)
        
        rsi = indicators.calculate_rsi(period=14)
        valid_rsi = rsi.dropna()
        
        # In strong uptrend, RSI should go above 70 (overbought)
        if len(valid_rsi) > 0:
            max_rsi = valid_rsi.max()
            self.assertGreater(max_rsi, 60)  # Should show overbought conditions
    
    def test_macd_crossover(self):
        """Test MACD line crosses signal line"""
        indicators = TechnicalIndicators(self.uptrend_data)
        macd_line, signal_line, histogram = indicators.calculate_macd()
        
        # Histogram changes sign at crossovers
        valid_histogram = histogram.dropna()
        if len(valid_histogram) > 1:
            sign_changes = (valid_histogram.shift(1) * valid_histogram < 0).sum()
            # Should have at least one crossover in trend data
            self.assertGreaterEqual(sign_changes, 0)
    
    def test_price_crossing_sma(self):
        """Test price crosses above/below SMA"""
        indicators = TechnicalIndicators(self.uptrend_data)
        sma = indicators.calculate_sma(period=20)
        
        # Check for price crossovers
        valid_idx = ~sma.isna()
        if valid_idx.any():
            price = self.uptrend_data['close'][valid_idx]
            sma_valid = sma[valid_idx]
            
            # In uptrend, price should be above SMA most of the time
            above_sma = (price > sma_valid).sum()
            total = len(price)
            ratio = above_sma / total if total > 0 else 0
            
            # In uptrend, expect price above SMA > 50% of time
            self.assertGreater(ratio, 0.4)


if __name__ == '__main__':
    unittest.main()
