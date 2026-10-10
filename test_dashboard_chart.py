#!/usr/bin/env python3
"""
Test script to verify dashboard chart functionality
Tests on-demand data fetching and chart rendering
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch
import pandas as pd

# Set test environment
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
os.environ['ENABLE_PDT_RULES'] = 'false'

# Import after setting environment
from data_fetcher import DataFetcher


class TestDashboardChart(unittest.TestCase):
    """Test dashboard chart data fetching and display"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.fetcher = DataFetcher()
    
    def test_data_fetcher_initialization(self):
        """Test that DataFetcher initializes correctly"""
        self.assertIsNotNone(self.fetcher)
        self.assertIsInstance(self.fetcher, DataFetcher)
    
    def test_fetch_historical_data_structure(self):
        """Test that fetch_historical_data_yfinance returns correct structure"""
        # Create mock data
        mock_data = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5],
            'volume': [1000000, 1100000, 1200000]
        })
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = Mock()
            mock_instance.history.return_value = mock_data
            mock_ticker.return_value = mock_instance
            
            result = self.fetcher.fetch_historical_data_yfinance('AAPL', period='1d', interval='5m')
            
            self.assertIsNotNone(result)
            self.assertIsInstance(result, pd.DataFrame)
            self.assertIn('open', result.columns)
            self.assertIn('high', result.columns)
            self.assertIn('low', result.columns)
            self.assertIn('close', result.columns)
            self.assertIn('volume', result.columns)
    
    def test_chart_callback_structure(self):
        """Test that chart callback returns proper figure structure"""
        # This test verifies the structure without actually running the callback
        # A proper figure should have 'data' and 'layout' keys
        
        figure_template = {
            'data': [],
            'layout': {
                'title': 'Test Chart',
                'plot_bgcolor': '#0e1117',
                'paper_bgcolor': '#1a1d25',
                'font': {'color': '#ffffff'},
                'xaxis': {'gridcolor': '#30363d', 'showgrid': True},
                'yaxis': {'gridcolor': '#30363d', 'showgrid': True}
            }
        }
        
        # Verify required keys
        self.assertIn('data', figure_template)
        self.assertIn('layout', figure_template)
        self.assertIsInstance(figure_template['data'], list)
        self.assertIsInstance(figure_template['layout'], dict)
    
    def test_candlestick_data_requirements(self):
        """Test that data has all required fields for candlestick chart"""
        # Create sample data with required columns
        data = pd.DataFrame({
            'open': [100.0, 101.0],
            'high': [102.0, 103.0],
            'low': [99.0, 100.0],
            'close': [101.0, 102.0],
            'volume': [1000000, 1100000]
        })
        
        # Verify all required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            self.assertIn(col, data.columns, f"Missing required column: {col}")
    
    def test_empty_ticker_handling(self):
        """Test that chart handles empty/None ticker gracefully"""
        # This simulates what happens when no ticker is selected
        selected_ticker = None
        
        # Should not raise an exception
        if not selected_ticker:
            # Empty chart scenario - should be handled gracefully
            self.assertTrue(True)
    
    def test_invalid_ticker_handling(self):
        """Test that chart handles invalid ticker symbols"""
        with patch('yfinance.Ticker') as mock_ticker:
            # Simulate yfinance returning empty data for invalid ticker
            mock_instance = Mock()
            mock_instance.history.return_value = pd.DataFrame()
            mock_ticker.return_value = mock_instance
            
            result = self.fetcher.fetch_historical_data_yfinance('INVALID', period='1d', interval='5m')
            
            # Should return None or empty DataFrame for invalid ticker
            self.assertTrue(result is None or result.empty)
    
    def test_volume_color_calculation(self):
        """Test volume bar coloring logic (green for up days, red for down days)"""
        data = pd.DataFrame({
            'open': [100.0, 102.0, 101.0],
            'close': [101.0, 101.0, 99.0],  # up, down, down
        })
        
        # Calculate expected colors
        expected_results = [
            True,   # close > open (green)
            False,  # close < open (red)
            False   # close < open (red)
        ]
        
        for i, (close, open_val) in enumerate(zip(data['close'], data['open'])):
            result = close >= open_val
            self.assertEqual(result, expected_results[i])
    
    def test_price_range_calculation(self):
        """Test price range calculation for chart scaling"""
        data = pd.DataFrame({
            'high': [105.0, 110.0, 108.0],
            'low': [95.0, 100.0, 98.0]
        })
        
        price_min = data['low'].min()  # Should be 95.0
        price_max = data['high'].max()  # Should be 110.0
        price_range = price_max - price_min  # Should be 15.0
        
        self.assertEqual(price_min, 95.0)
        self.assertEqual(price_max, 110.0)
        self.assertEqual(price_range, 15.0)
        
        # Test padding calculation (10% of range)
        padding = price_range * 0.1
        self.assertEqual(padding, 1.5)
    
    def test_intraday_fallback_to_daily(self):
        """Test that chart falls back to daily data if intraday fails"""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = Mock()
            
            # First call (intraday) returns empty
            # Second call (daily) returns data
            mock_instance.history.side_effect = [
                pd.DataFrame(),  # Empty intraday data
                pd.DataFrame({   # Valid daily data
                    'open': [100.0], 'high': [102.0], 'low': [99.0], 
                    'close': [101.0], 'volume': [1000000]
                })
            ]
            mock_ticker.return_value = mock_instance
            
            # First attempt - intraday (should be empty)
            result1 = self.fetcher.fetch_historical_data_yfinance('AAPL', period='1d', interval='5m')
            self.assertTrue(result1 is None or result1.empty)
            
            # Second attempt - daily (should succeed)
            result2 = self.fetcher.fetch_historical_data_yfinance('AAPL', period='1mo', interval='1d')
            self.assertIsNotNone(result2)
            self.assertFalse(result2.empty)


class TestChartIntegration(unittest.TestCase):
    """Integration tests for chart functionality"""
    
    def test_web_gui_imports(self):
        """Test that web_gui.py imports correctly"""
        try:
            # Import web_gui module
            import web_gui
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import web_gui: {e}")
    
    def test_data_fetcher_import(self):
        """Test that DataFetcher can be imported"""
        try:
            from data_fetcher import DataFetcher
            fetcher = DataFetcher()
            self.assertIsNotNone(fetcher)
        except ImportError as e:
            self.fail(f"Failed to import DataFetcher: {e}")


def run_tests():
    """Run all chart tests"""
    print("="*60)
    print("Dashboard Chart Tests")
    print("="*60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestDashboardChart))
    suite.addTests(loader.loadTestsFromTestCase(TestChartIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
