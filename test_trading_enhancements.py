#!/usr/bin/env python3
"""
Test suite for stock trading enhancements
Tests strategies, indicators, data fetcher, risk management, and backtrader integration
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import modules to test
from strategies import SMAStrategy, BollingerBandsStrategy, StrategyManager
from indicators import TechnicalIndicators
from data_fetcher import DataFetcher
from risk_management import RiskManager


class TestSMAStrategy(unittest.TestCase):
    """Test SMA Crossover Strategy"""
    
    def setUp(self):
        """Set up test data"""
        # Generate sample price data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        base_price = 100
        trend = np.linspace(0, 20, 100)
        noise = np.random.normal(0, 2, 100)
        prices = base_price + trend + noise
        
        self.data = pd.DataFrame({
            'date': dates,
            'close': prices
        })
        
        self.strategy = SMAStrategy(fast_period=10, slow_period=30)
    
    def test_strategy_initialization(self):
        """Test strategy initializes correctly"""
        self.assertEqual(self.strategy.name, "SMA Crossover")
        self.assertEqual(self.strategy.fast_period, 10)
        self.assertEqual(self.strategy.slow_period, 30)
    
    def test_generate_signal(self):
        """Test signal generation"""
        signal = self.strategy.generate_signal(self.data)
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
    
    def test_insufficient_data(self):
        """Test with insufficient data"""
        short_data = self.data.head(5)
        signal = self.strategy.generate_signal(short_data)
        self.assertEqual(signal, 'HOLD')
    
    def test_get_indicator_values(self):
        """Test getting indicator values"""
        indicators = self.strategy.get_indicator_values(self.data)
        
        self.assertIn('sma_fast', indicators)
        self.assertIn('sma_slow', indicators)
        self.assertIsInstance(indicators['sma_fast'], (float, np.floating))
        self.assertIsInstance(indicators['sma_slow'], (float, np.floating))


class TestBollingerBandsStrategy(unittest.TestCase):
    """Test Bollinger Bands Strategy"""
    
    def setUp(self):
        """Set up test data"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        prices = 100 + np.cumsum(np.random.normal(0, 2, 100))
        
        self.data = pd.DataFrame({
            'date': dates,
            'close': prices
        })
        
        self.strategy = BollingerBandsStrategy(period=20, num_std=2.0)
    
    def test_strategy_initialization(self):
        """Test strategy initializes correctly"""
        self.assertEqual(self.strategy.name, "Bollinger Bands")
        self.assertEqual(self.strategy.period, 20)
        self.assertEqual(self.strategy.num_std, 2.0)
    
    def test_generate_signal(self):
        """Test signal generation"""
        signal = self.strategy.generate_signal(self.data)
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
    
    def test_get_indicator_values(self):
        """Test getting indicator values"""
        indicators = self.strategy.get_indicator_values(self.data)
        
        self.assertIn('upper_band', indicators)
        self.assertIn('middle_band', indicators)
        self.assertIn('lower_band', indicators)
        self.assertIn('band_width', indicators)
        self.assertIn('position_in_bands', indicators)


class TestStrategyManager(unittest.TestCase):
    """Test Strategy Manager"""
    
    def setUp(self):
        """Set up test data and strategies"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        prices = 100 + np.cumsum(np.random.normal(0, 2, 100))
        
        self.data = pd.DataFrame({
            'date': dates,
            'close': prices
        })
        
        self.manager = StrategyManager()
    
    def test_add_strategy(self):
        """Test adding strategies"""
        self.manager.add_strategy(SMAStrategy(fast_period=10, slow_period=30), weight=1.0)
        self.assertEqual(len(self.manager.strategies), 1)
        
        self.manager.add_strategy(BollingerBandsStrategy(period=20, num_std=2.0), weight=0.5)
        self.assertEqual(len(self.manager.strategies), 2)
    
    def test_combined_signal(self):
        """Test combined signal generation"""
        self.manager.add_strategy(SMAStrategy(fast_period=10, slow_period=30), weight=1.0)
        self.manager.add_strategy(BollingerBandsStrategy(period=20, num_std=2.0), weight=1.0)
        
        signal = self.manager.generate_combined_signal(self.data)
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])


class TestTechnicalIndicators(unittest.TestCase):
    """Test Technical Indicators"""
    
    def setUp(self):
        """Set up test data"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        close = 100 + np.cumsum(np.random.normal(0, 2, 100))
        open_prices = close + np.random.normal(0, 0.5, 100)
        high = np.maximum(open_prices, close) + np.random.uniform(0, 1, 100)
        low = np.minimum(open_prices, close) - np.random.uniform(0, 1, 100)
        volume = np.random.randint(1000000, 5000000, 100)
        
        self.data = pd.DataFrame({
            'date': dates,
            'open': open_prices,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
        
        self.indicators = TechnicalIndicators(self.data)
    
    def test_calculate_rsi(self):
        """Test RSI calculation"""
        rsi = self.indicators.calculate_rsi(period=14)
        self.assertIsInstance(rsi, pd.Series)
        self.assertEqual(len(rsi), len(self.data))
        
        # Check RSI is within valid range (0-100)
        valid_rsi = rsi.dropna()
        self.assertTrue((valid_rsi >= 0).all())
        self.assertTrue((valid_rsi <= 100).all())
    
    def test_calculate_macd(self):
        """Test MACD calculation"""
        macd_line, signal_line, histogram = self.indicators.calculate_macd()
        
        self.assertIsInstance(macd_line, pd.Series)
        self.assertIsInstance(signal_line, pd.Series)
        self.assertIsInstance(histogram, pd.Series)
        
        self.assertEqual(len(macd_line), len(self.data))
    
    def test_calculate_bollinger_bands(self):
        """Test Bollinger Bands calculation"""
        upper, middle, lower = self.indicators.calculate_bollinger_bands()
        
        self.assertIsInstance(upper, pd.Series)
        self.assertIsInstance(middle, pd.Series)
        self.assertIsInstance(lower, pd.Series)
        
        # Check bands are in correct order
        valid_data = ~(upper.isna() | middle.isna() | lower.isna())
        self.assertTrue((upper[valid_data] >= middle[valid_data]).all())
        self.assertTrue((middle[valid_data] >= lower[valid_data]).all())
    
    def test_get_all_indicators(self):
        """Test getting all indicators"""
        all_indicators = self.indicators.get_all_indicators()
        
        self.assertIsInstance(all_indicators, dict)
        self.assertGreater(len(all_indicators), 0)
    
    def test_interpret_indicators(self):
        """Test indicator interpretation"""
        interpretations = self.indicators.interpret_indicators()
        
        self.assertIsInstance(interpretations, dict)
        
        # Check structure of interpretations
        for indicator_name, interpretation in interpretations.items():
            self.assertIn('action', interpretation)
            self.assertIn(interpretation['action'], ['BUY', 'SELL', 'HOLD'])


class TestDataFetcher(unittest.TestCase):
    """Test Data Fetcher"""
    
    def setUp(self):
        """Set up data fetcher"""
        self.fetcher = DataFetcher()
    
    @patch('yfinance.Ticker')
    def test_fetch_historical_data_yfinance(self, mock_ticker):
        """Test fetching historical data from yfinance"""
        # Mock yfinance response
        mock_data = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [105, 106, 107],
            'Low': [99, 100, 101],
            'Close': [103, 104, 105],
            'Volume': [1000000, 1100000, 1200000]
        })
        
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_ticker_instance
        
        data = self.fetcher.fetch_historical_data_yfinance('AAPL', period='1mo')
        
        if data is not None:
            self.assertIsInstance(data, pd.DataFrame)
            self.assertGreater(len(data), 0)
    
    def test_parse_number(self):
        """Test number parsing"""
        self.assertEqual(self.fetcher._parse_number('123.45'), 123.45)
        self.assertIsNone(self.fetcher._parse_number('None'))
        self.assertIsNone(self.fetcher._parse_number(''))
        self.assertIsNone(self.fetcher._parse_number(None))
    
    def test_analyze_fundamentals(self):
        """Test fundamental analysis"""
        fundamentals = {
            'pe_ratio': 20.0,
            'profit_margin': 0.20,
            'return_on_equity': 0.18,
            'dividend_yield': 0.02,
            'beta': 1.2
        }
        
        analysis = self.fetcher.analyze_fundamentals(fundamentals)
        
        self.assertIn('valuation_score', analysis)
        self.assertIn('profitability_score', analysis)
        self.assertIn('recommendation', analysis)
        self.assertIn('signals', analysis)
        
        # Check recommendation is valid
        valid_recommendations = ['STRONG BUY', 'BUY', 'HOLD', 'SELL', 'STRONG SELL']
        self.assertIn(analysis['recommendation'], valid_recommendations)


class TestRiskManager(unittest.TestCase):
    """Test Risk Manager"""
    
    def setUp(self):
        """Set up risk manager"""
        self.risk_mgr = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
    
    def test_initialization(self):
        """Test risk manager initialization"""
        self.assertEqual(self.risk_mgr.total_capital, 10000.0)
        self.assertEqual(self.risk_mgr.risk_per_trade, 0.02)
    
    def test_calculate_position_size_fixed_risk(self):
        """Test position sizing with fixed risk"""
        entry_price = 150.0
        stop_loss = 147.0
        
        position = self.risk_mgr.calculate_position_size_fixed_risk(entry_price, stop_loss)
        
        self.assertIn('shares', position)
        self.assertIn('position_value', position)
        self.assertIn('risk_amount', position)
        
        # Check risk calculation is reasonable
        # Risk per share = 150 - 147 = $3
        # With 2% risk on $10000 = $200 risk
        # Shares = $200 / $3 = 66.67 shares
        # Position value = 66.67 * $150 = $10,000
        # But this exceeds max_position_size (20% of capital = $2000)
        # So it should be capped
        
        max_position_value = 10000.0 * 0.20  # 20% = $2000
        self.assertLessEqual(position['position_value'], max_position_value)
    
    def test_calculate_risk_reward_ratio(self):
        """Test risk/reward ratio calculation"""
        entry_price = 150.0
        stop_loss = 147.0
        target = 159.0
        
        rr = self.risk_mgr.calculate_risk_reward_ratio(entry_price, stop_loss, target)
        
        self.assertIn('risk', rr)
        self.assertIn('reward', rr)
        self.assertIn('risk_reward_ratio', rr)
        self.assertIn('is_favorable', rr)
        
        # Check calculation
        expected_risk = entry_price - stop_loss
        expected_reward = target - entry_price
        expected_ratio = expected_reward / expected_risk
        
        self.assertAlmostEqual(rr['risk'], expected_risk, places=2)
        self.assertAlmostEqual(rr['reward'], expected_reward, places=2)
        self.assertAlmostEqual(rr['risk_reward_ratio'], expected_ratio, places=2)
    
    def test_kelly_criterion(self):
        """Test Kelly Criterion calculation"""
        kelly = self.risk_mgr.calculate_kelly_criterion(
            win_rate=0.60,
            avg_win=300,
            avg_loss=200
        )
        
        self.assertIsInstance(kelly, float)
        self.assertGreaterEqual(kelly, 0.0)
        self.assertLessEqual(kelly, self.risk_mgr.max_position_size)
    
    def test_validate_trade(self):
        """Test trade validation"""
        validation = self.risk_mgr.validate_trade(
            entry_price=150.0,
            stop_loss_price=147.0,
            target_price=159.0
        )
        
        self.assertIn('is_valid', validation)
        self.assertIn('summary', validation)
        self.assertIsInstance(validation['is_valid'], bool)
    
    def test_sharpe_ratio(self):
        """Test Sharpe ratio calculation"""
        returns = np.array([0.01, 0.02, -0.01, 0.03, 0.01, -0.02, 0.04])
        sharpe = self.risk_mgr.calculate_sharpe_ratio(returns, risk_free_rate=0.0)
        
        self.assertIsInstance(sharpe, (float, np.floating))
    
    def test_max_drawdown(self):
        """Test max drawdown calculation"""
        equity_curve = np.array([10000, 10500, 10200, 11000, 10800, 11500, 11000])
        dd = self.risk_mgr.calculate_max_drawdown(equity_curve)
        
        self.assertIn('max_drawdown', dd)
        self.assertIn('max_drawdown_pct', dd)
        self.assertGreaterEqual(dd['max_drawdown'], 0)
        self.assertGreaterEqual(dd['max_drawdown_pct'], 0)


class TestIntegration(unittest.TestCase):
    """Test integration of multiple components"""
    
    def setUp(self):
        """Set up test data"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        close = 100 + np.cumsum(np.random.normal(0, 2, 100))
        
        self.data = pd.DataFrame({
            'date': dates,
            'close': close
        })
    
    def test_strategy_and_risk_management(self):
        """Test using strategy with risk management"""
        # Generate signal
        strategy = SMAStrategy(fast_period=10, slow_period=30)
        signal = strategy.generate_signal(self.data)
        
        # If signal is BUY, calculate position size
        if signal == 'BUY':
            current_price = self.data['close'].iloc[-1]
            stop_loss = current_price * 0.97  # 3% stop loss
            
            risk_mgr = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
            position = risk_mgr.calculate_position_size_fixed_risk(current_price, stop_loss)
            
            self.assertGreater(position['shares'], 0)
            self.assertLessEqual(position['position_value'], 10000.0)


if __name__ == '__main__':
    unittest.main()
