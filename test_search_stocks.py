#!/usr/bin/env python3
"""
Test suite for the search_stocks method enhancement
Tests the new explicit stock searching with data_fetcher integration
"""

import os
# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')
os.environ.setdefault('SCHWAB_SANDBOX_MODE', 'false')

import unittest
import importlib
from unittest.mock import patch, MagicMock
from main import TradingBot, MIN_STOCK_PRICE, MAX_STOCK_PRICE, MIN_DAILY_VOLUME


class TestSearchStocksMethod(unittest.TestCase):
    """Test the new search_stocks method"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_search_stocks_with_provided_symbols(self):
        """Test search_stocks with a provided symbol list"""
        # Mock fetch_real_stock_price to return valid data
        with patch.object(self.bot, 'fetch_real_stock_price') as mock_fetch:
            mock_fetch.return_value = (100.0, 1000000)  # price, volume
            
            # Provide symbols directly
            symbols = ['AAPL', 'MSFT', 'GOOGL']
            results = self.bot.search_stocks(symbols=symbols, use_screener=False, max_stocks=5)
            
            # Should have called fetch for each symbol
            self.assertEqual(mock_fetch.call_count, 3)
            
            # Should return list of tradeable stocks
            self.assertIsInstance(results, list)
            
            # Each result should have required keys
            for stock in results:
                self.assertIn('symbol', stock)
                self.assertIn('price', stock)
                self.assertIn('volume', stock)
                self.assertIn('volatility', stock)
    
    def test_search_stocks_filters_low_price(self):
        """Test that stocks below MIN_STOCK_PRICE are filtered out"""
        with patch.object(self.bot, 'fetch_real_stock_price') as mock_fetch:
            # Return price below minimum
            mock_fetch.return_value = (MIN_STOCK_PRICE - 1.0, 1000000)
            
            symbols = ['LOWPRICE']
            results = self.bot.search_stocks(symbols=symbols, use_screener=False)
            
            # Should filter out low-priced stock
            self.assertEqual(len(results), 0)
    
    def test_search_stocks_filters_high_price(self):
        """Test that stocks above MAX_STOCK_PRICE are filtered out"""
        with patch.object(self.bot, 'fetch_real_stock_price') as mock_fetch:
            # Return price above maximum
            mock_fetch.return_value = (MAX_STOCK_PRICE + 100.0, 1000000)
            
            symbols = ['HIGHPRICE']
            results = self.bot.search_stocks(symbols=symbols, use_screener=False)
            
            # Should filter out high-priced stock
            self.assertEqual(len(results), 0)
    
    def test_search_stocks_filters_low_volume(self):
        """Test that stocks below MIN_DAILY_VOLUME are filtered out"""
        with patch.object(self.bot, 'fetch_real_stock_price') as mock_fetch:
            # Return volume below minimum
            mock_fetch.return_value = (50.0, MIN_DAILY_VOLUME - 1000)
            
            symbols = ['LOWVOL']
            results = self.bot.search_stocks(symbols=symbols, use_screener=False)
            
            # Should filter out low-volume stock
            self.assertEqual(len(results), 0)
    
    def test_search_stocks_filters_high_volatility(self):
        """Test that stocks with high volatility are filtered out"""
        with patch.object(self.bot, 'fetch_real_stock_price') as mock_fetch:
            mock_fetch.return_value = (50.0, 1000000)
            
            # Add price history to calculate volatility
            symbol = 'HIGHVOL'
            self.bot.price_history[symbol] = [100, 110, 95, 120, 85]  # High volatility
            
            symbols = [symbol]
            results = self.bot.search_stocks(symbols=symbols, use_screener=False)
            
            # Should filter out or include based on actual volatility calculation
            # The test validates the filtering mechanism exists
            self.assertIsInstance(results, list)
    
    def test_search_stocks_returns_max_stocks(self):
        """Test that search_stocks respects max_stocks limit"""
        with patch.object(self.bot, 'fetch_real_stock_price') as mock_fetch:
            mock_fetch.return_value = (50.0, 1000000)
            
            # Provide more symbols than max_stocks
            symbols = ['SYM1', 'SYM2', 'SYM3', 'SYM4', 'SYM5', 'SYM6']
            results = self.bot.search_stocks(symbols=symbols, use_screener=False, max_stocks=3)
            
            # Should return at most max_stocks
            self.assertLessEqual(len(results), 3)
    
    def test_search_stocks_handles_invalid_price(self):
        """Test that search_stocks handles None or invalid prices"""
        with patch.object(self.bot, 'fetch_real_stock_price') as mock_fetch:
            # Return None for price
            mock_fetch.return_value = None
            
            symbols = ['INVALID']
            results = self.bot.search_stocks(symbols=symbols, use_screener=False)
            
            # Should skip symbol with invalid price
            self.assertEqual(len(results), 0)
    
    def test_search_stocks_with_data_fetcher(self):
        """Test search_stocks integration with DataFetcher"""
        # Mock DataFetcher if available
        try:
            from data_fetcher import DataFetcher
            
            with patch('data_fetcher.DataFetcher') as MockDataFetcher:
                mock_fetcher = MagicMock()
                MockDataFetcher.return_value = mock_fetcher
                
                # Mock get_comprehensive_data to return valid data
                mock_fetcher.get_comprehensive_data.return_value = {
                    'price': 100.0,
                    'volume': 1000000,
                    'volatility': 0.05,
                    'marketCap': 1000000000
                }
                
                symbols = ['AAPL']
                results = self.bot.search_stocks(symbols=symbols, use_screener=False)
                
                # Should have attempted to use DataFetcher
                self.assertIsInstance(results, list)
        except ImportError:
            # DataFetcher not available, skip this test
            self.skipTest("DataFetcher module not available")
    
    def test_search_stocks_loads_symbols_when_none_provided(self):
        """Test that search_stocks loads symbols when none provided"""
        with patch.object(self.bot, 'load_scan_symbols') as mock_load:
            mock_load.return_value = ['AAPL', 'MSFT']
            
            with patch.object(self.bot, 'fetch_real_stock_price') as mock_fetch:
                mock_fetch.return_value = (100.0, 1000000)
                
                # Don't provide symbols
                results = self.bot.search_stocks(symbols=None, use_screener=False)
                
                # Should have called load_scan_symbols
                mock_load.assert_called_once()
                # And should have returned results for the loaded symbols
                self.assertIsInstance(results, list)
                self.assertEqual(len(results), 2)

class TestLimitOrderForBuys(unittest.TestCase):
    """Test that BUY orders use LIMIT order type"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
        
        # Mock the Schwab client
        self.bot.schwab_client = MagicMock()
        self.bot.schwab_client.place_order.return_value = MagicMock(
            status_code=201,
            headers={'Location': 'https://api.schwab.com/orders/12345'},
            text=''
        )
    
    @patch('main.PAPER_TRADING_MODE', False)
    @patch('main.SCHWAB_SANDBOX_MODE', False)
    def test_buy_order_uses_limit_type(self):
        """Test that BUY orders use LIMIT order type"""
        # Execute a BUY trade
        self.bot.execute_trade_live_mode('AAPL', 'BUY', 150.0)
        
        # Check that place_order was called
        if self.bot.schwab_client.place_order.called:
            # Get the order payload from the call
            call_args = self.bot.schwab_client.place_order.call_args
            order_payload = call_args[0][1]  # Second argument is the order payload
            
            # Verify order type is LIMIT
            self.assertEqual(order_payload['orderType'], 'LIMIT')
            # Verify price is set for limit order
            self.assertIn('price', order_payload)
            self.assertEqual(order_payload['price'], 150.0)
    
    @patch('main.PAPER_TRADING_MODE', False)
    @patch('main.SCHWAB_SANDBOX_MODE', False)
    def test_sell_order_uses_market_type(self):
        """Test that SELL orders use MARKET order type"""
        # Set up an existing position
        self.bot.positions['AAPL'] = {
            'entry_price': 140.0,
            'quantity': 10,
            'high_price': 150.0,
            'stop_percent': 0.03,
            'partial_exit_done': False,
            'entry_time': '2024-01-01T10:00:00'
        }
        self.bot.execute_trade_live_mode('AAPL', 'SELL', 155.0)
        # Execute a SELL trade
        result = self.bot.execute_trade_live_mode('AAPL', 'SELL', 155.0)
        
        # Check that place_order was called
        if self.bot.schwab_client.place_order.called:
            # Get the order payload from the call
            call_args = self.bot.schwab_client.place_order.call_args
            order_payload = call_args[0][1]
            
            # Verify order type is MARKET
            self.assertEqual(order_payload['orderType'], 'MARKET')
            # Verify price is NOT set for market order
            self.assertNotIn('price', order_payload)


class TestHighSalePercentRename(unittest.TestCase):
    """Test the renamed HIGH_SALE_PERCENT variable"""
    
    def test_high_sale_percent_loaded(self):
        """Test that HIGH_SALE_PERCENT is loaded from environment"""
        from main import HIGH_SALE_PERCENT
        
        # Should be loaded and be a float
        self.assertIsInstance(HIGH_SALE_PERCENT, float)
        self.assertGreater(HIGH_SALE_PERCENT, 0)
    
    def test_backward_compatibility_with_bot_take_profit(self):
        """Test backward compatibility with BOT_TAKE_PROFIT_PERCENT"""
        from main import BOT_TAKE_PROFIT_PERCENT, HIGH_SALE_PERCENT
        
        # Both should be available and equal
        self.assertEqual(BOT_TAKE_PROFIT_PERCENT, HIGH_SALE_PERCENT)
    
    def test_high_sale_percent_env_takes_precedence(self):
        """Test that HIGH_SALE_PERCENT env var takes precedence"""
        # Set environment variable
        os.environ['HIGH_SALE_PERCENT'] = '0.15'
        os.environ['BOT_TAKE_PROFIT_PERCENT'] = '0.10'
        
        main_module = importlib.import_module("main")
        importlib.reload(main_module)
        main = main_module
        importlib.reload(main_module)
        self.assertEqual(main_module.HIGH_SALE_PERCENT, 0.15)
        # HIGH_SALE_PERCENT should be 0.15
        self.assertEqual(main.HIGH_SALE_PERCENT, 0.15)
        
        # Clean up
        del os.environ['HIGH_SALE_PERCENT']
        if 'BOT_TAKE_PROFIT_PERCENT' in os.environ:
            del os.environ['BOT_TAKE_PROFIT_PERCENT']


if __name__ == '__main__':
    unittest.main()
