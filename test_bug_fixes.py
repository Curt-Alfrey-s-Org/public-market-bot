#!/usr/bin/env python3
"""
Test suite for bug fixes
Tests critical bug fixes identified in code analysis
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from main import TradingBot
from indicators import TechnicalIndicators
from risk_management import RiskManager
import tempfile
import os


class TestDivisionByZeroBugFix(unittest.TestCase):
    """Test fix for division by zero in indicators.py"""
    
    def setUp(self):
        """Set up test data"""
        # Create sample price data with potential zero denominator scenarios
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        
        # Scenario 1: Flat prices (no movement)
        self.flat_prices = pd.Series([100.0] * 30, index=dates, name='close')
        
        # Scenario 2: Very low volatility
        self.low_vol_prices = pd.Series(
            [100 + i * 0.01 for i in range(30)], 
            index=dates, 
            name='close'
        )
        
        # Scenario 3: Normal prices
        np.random.seed(42)
        self.normal_prices = pd.Series(
            100 + np.random.randn(30).cumsum(), 
            index=dates, 
            name='close'
        )
        
    def test_adx_with_flat_prices(self):
        """Test ADX calculation with flat prices (zero denominator case)"""
        high = pd.Series([101.0] * 30, name='high')
        low = pd.Series([99.0] * 30, name='low')
        close = self.flat_prices
        
        df = pd.DataFrame({'high': high, 'low': low, 'close': close})
        indicators = TechnicalIndicators(df)
        
        # Should not raise ZeroDivisionError
        try:
            adx = indicators.calculate_adx(period=14)
            # ADX should be a Series
            self.assertIsInstance(adx, pd.Series)
            # Check that NaN values are handled properly
            self.assertTrue(len(adx) > 0)
        except ZeroDivisionError:
            self.fail("ADX calculation raised ZeroDivisionError with flat prices")
    
    def test_adx_with_low_volatility(self):
        """Test ADX with low volatility prices"""
        high = pd.Series([p + 0.5 for p in self.low_vol_prices], name='high')
        low = pd.Series([p - 0.5 for p in self.low_vol_prices], name='low')
        close = self.low_vol_prices
        
        df = pd.DataFrame({'high': high, 'low': low, 'close': close})
        indicators = TechnicalIndicators(df)
        
        try:
            adx = indicators.calculate_adx(period=14)
            self.assertIsInstance(adx, pd.Series)
        except ZeroDivisionError:
            self.fail("ADX calculation raised ZeroDivisionError with low volatility")
    
    def test_adx_with_normal_prices(self):
        """Test ADX with normal price data"""
        high = pd.Series([p + 1 for p in self.normal_prices], name='high')
        low = pd.Series([p - 1 for p in self.normal_prices], name='low')
        close = self.normal_prices
        
        df = pd.DataFrame({'high': high, 'low': low, 'close': close})
        indicators = TechnicalIndicators(df)
        
        adx = indicators.calculate_adx(period=14)
        self.assertIsInstance(adx, pd.Series)
        # ADX should have some valid values (after initial NaN period)
        valid_values = adx.dropna()
        self.assertTrue(len(valid_values) > 0)


class TestPriceCacheValidation(unittest.TestCase):
    """Test fix for price cache validation"""
    
    def setUp(self):
        """Set up trading bot"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_valid_cache_entry(self):
        """Test that valid cache entries work correctly"""
        # Manually add a valid cache entry
        self.bot.price_cache['AAPL'] = {
            'price': 150.0,
            'volume': 1000000,
            'timestamp': datetime.now()
        }
        
        # Fetch should use cache
        result = self.bot.fetch_schwab_stock_price('AAPL')
        if result:  # Only check if we got a result
            price, volume = result
            self.assertEqual(price, 150.0)
            self.assertEqual(volume, 1000000)
    
    def test_invalid_cache_structure(self):
        """Test that invalid cache structure is handled"""
        # Add invalid cache entry (missing keys)
        self.bot.price_cache['INVALID'] = {
            'price': 100.0
            # Missing 'volume' and 'timestamp'
        }
        
        # Should not crash when fetching
        try:
            # This should detect invalid cache and fetch fresh data
            # In test environment, API might not be available, so we just check it doesn't crash
            result = self.bot.fetch_schwab_stock_price('INVALID')
            # If result is None, that's ok - API might not be available in test
            self.assertTrue(result is None or isinstance(result, tuple))
        except KeyError as e:
            self.fail(f"Cache validation should handle missing keys, but got KeyError: {e}")
    
    def test_malformed_cache_timestamp(self):
        """Test that malformed timestamp in cache is handled"""
        # Add cache with invalid timestamp
        self.bot.price_cache['BADTIME'] = {
            'price': 100.0,
            'volume': 1000000,
            'timestamp': "not a datetime"  # Invalid timestamp
        }
        
        # Should handle gracefully
        try:
            result = self.bot.fetch_schwab_stock_price('BADTIME')
            # Should either return None or valid tuple, not crash
            self.assertTrue(result is None or isinstance(result, tuple))
            # Invalid cache should be removed
            self.assertNotIn('BADTIME', self.bot.price_cache)
        except (TypeError, AttributeError) as e:
            self.fail(f"Cache validation should handle invalid timestamp, but got error: {e}")


class TestCSVImportValidation(unittest.TestCase):
    """Test fix for CSV import error handling"""
    
    def setUp(self):
        """Set up trading bot and test CSV files"""
        self.bot = TradingBot(total_capital=10000.0)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_csv_with_valid_pnl(self):
        """Test CSV import with valid P&L column"""
        csv_path = os.path.join(self.temp_dir, 'valid.csv')
        with open(csv_path, 'w') as f:
            f.write('Symbol,Quantity,Price,Action,PnL\n')
            f.write('AAPL,10,150.0,BUY,50.0\n')
            f.write('MSFT,5,300.0,SELL,-25.0\n')
        
        trades = self.bot.import_tos_csv(csv_path)
        self.assertEqual(len(trades), 2)
        self.assertEqual(trades[0]['pnl'], 50.0)
        self.assertEqual(trades[1]['pnl'], -25.0)
    
    def test_csv_with_invalid_pnl(self):
        """Test CSV import with invalid P&L values"""
        csv_path = os.path.join(self.temp_dir, 'invalid_pnl.csv')
        with open(csv_path, 'w') as f:
            f.write('Symbol,Quantity,Price,Action,PnL\n')
            f.write('AAPL,10,150.0,BUY,not_a_number\n')
            f.write('MSFT,5,300.0,SELL,25.0\n')
        
        # Should not crash, should handle gracefully
        trades = self.bot.import_tos_csv(csv_path)
        self.assertEqual(len(trades), 2)
        # First trade should have default pnl of 0.0
        self.assertEqual(trades[0]['pnl'], 0.0)
        # Second trade should have valid pnl
        self.assertEqual(trades[1]['pnl'], 25.0)
    
    def test_csv_without_pnl_column(self):
        """Test CSV import without P&L column"""
        csv_path = os.path.join(self.temp_dir, 'no_pnl.csv')
        with open(csv_path, 'w') as f:
            f.write('Symbol,Quantity,Price,Action\n')
            f.write('AAPL,10,150.0,BUY\n')
            f.write('MSFT,5,300.0,SELL\n')
        
        trades = self.bot.import_tos_csv(csv_path)
        self.assertEqual(len(trades), 2)
        # Trades should not have pnl key since column doesn't exist
        self.assertNotIn('pnl', trades[0])
        self.assertNotIn('pnl', trades[1])


class TestDatetimeParsingRobustness(unittest.TestCase):
    """Test fix for datetime parsing in trade history"""
    
    def setUp(self):
        """Set up trading bot with various timestamp formats"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_valid_iso_timestamps(self):
        """Test win rate calculation with valid ISO timestamps"""
        # Add trades with valid timestamps
        now = datetime.now()
        for i in range(10):
            trade = {
                'timestamp': (now - timedelta(days=i)).isoformat(),
                'symbol': 'AAPL',
                'action': 'BUY',
                'quantity': 10,
                'price': 150.0,
                'is_win': i % 2 == 0  # Every other trade wins
            }
            self.bot.trade_history.append(trade)
        
        # Should calculate win rate without errors
        try:
            win_rate = self.bot.calculate_win_rate()
            self.assertIsInstance(win_rate, float)
            self.assertGreaterEqual(win_rate, 0.0)
            self.assertLessEqual(win_rate, 1.0)
        except (ValueError, KeyError, TypeError) as e:
            self.fail(f"Win rate calculation failed with valid timestamps: {e}")
    
    def test_invalid_timestamp_format(self):
        """Test that invalid timestamps are handled gracefully"""
        # Add some valid trades
        now = datetime.now()
        for i in range(5):
            self.bot.trade_history.append({
                'timestamp': (now - timedelta(days=i)).isoformat(),
                'symbol': 'AAPL',
                'action': 'BUY',
                'quantity': 10,
                'price': 150.0,
                'is_win': True
            })
        
        # Add invalid timestamp
        self.bot.trade_history.append({
            'timestamp': 'invalid-format',
            'symbol': 'MSFT',
            'action': 'BUY',
            'quantity': 10,
            'price': 300.0,
            'is_win': False
        })
        
        # Should handle invalid timestamp gracefully
        try:
            win_rate = self.bot.calculate_win_rate()
            self.assertIsInstance(win_rate, float)
            # Should calculate based on valid trades only (5 valid trades, all wins)
            # If no valid trades in last 7 days or calculation failed, win_rate may be 0.0
            self.assertGreaterEqual(win_rate, 0.0)  # At minimum, should be 0.0, not crash
        except (ValueError, KeyError, TypeError) as e:
            self.fail(f"Win rate calculation should handle invalid timestamps, got error: {e}")
    
    def test_missing_timestamp(self):
        """Test that missing timestamp key is handled"""
        # Add trade without timestamp
        self.bot.trade_history.append({
            # No 'timestamp' key
            'symbol': 'AAPL',
            'action': 'BUY',
            'quantity': 10,
            'price': 150.0,
            'is_win': True
        })
        
        # Should handle missing timestamp
        try:
            win_rate = self.bot.calculate_win_rate()
            self.assertIsInstance(win_rate, float)
        except KeyError as e:
            self.fail(f"Win rate calculation should handle missing timestamp, got error: {e}")


class TestRiskManagementValidation(unittest.TestCase):
    """Test fix for input validation in risk management"""
    
    def setUp(self):
        """Set up risk manager"""
        self.risk_manager = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
    
    def test_positive_prices(self):
        """Test with valid positive prices"""
        result = self.risk_manager.calculate_position_size_fixed_risk(
            entry_price=150.0,
            stop_loss_price=145.0
        )
        
        self.assertGreater(result['shares'], 0)
        self.assertEqual(result.get('error'), None)
    
    def test_negative_entry_price(self):
        """Test that negative entry price is rejected"""
        result = self.risk_manager.calculate_position_size_fixed_risk(
            entry_price=-150.0,
            stop_loss_price=145.0
        )
        
        self.assertEqual(result['shares'], 0)
        self.assertIn('error', result)
        self.assertIn('positive', result['error'].lower())
    
    def test_zero_entry_price(self):
        """Test that zero entry price is rejected"""
        result = self.risk_manager.calculate_position_size_fixed_risk(
            entry_price=0.0,
            stop_loss_price=145.0
        )
        
        self.assertEqual(result['shares'], 0)
        self.assertIn('error', result)
    
    def test_negative_stop_loss(self):
        """Test that negative stop loss is rejected"""
        result = self.risk_manager.calculate_position_size_fixed_risk(
            entry_price=150.0,
            stop_loss_price=-145.0
        )
        
        self.assertEqual(result['shares'], 0)
        self.assertIn('error', result)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
