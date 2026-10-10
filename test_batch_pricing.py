import os
import unittest
from unittest.mock import patch, MagicMock

# Ensure simulation-safe envs
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')
os.environ.setdefault('SCHWAB_SANDBOX_MODE', 'true')
os.environ.setdefault('MARKET_DATA_PROVIDER', 'YAHOOQUERY')

class TestBatchPricing(unittest.TestCase):
    def setUp(self):
        # Import here to respect env setup
        from data_fetcher import DataFetcher
        self.fetcher = DataFetcher()
        self.symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']

    def test_fetch_batch_prices_returns_prices_and_volume(self):
        result = self.fetcher.fetch_batch_prices(self.symbols)
        self.assertIsInstance(result, dict)
        # Assert basic structure for a couple symbols
        for sym in self.symbols:
            self.assertIn(sym, result)
            pv = result[sym]
            # Allow tuple/list of (price, volume)
            self.assertIsInstance(pv, (tuple, list))
            self.assertGreaterEqual(len(pv), 2)
            price, volume = pv[0], pv[1]
            self.assertIsInstance(price, (int, float))
            self.assertTrue(price > 0)
            # Volume may be 0 for some providers but should be int
            self.assertIsInstance(volume, (int, float))

    def test_integration_search_stocks_uses_prefetch(self):
        from main import TradingBot
        bot = TradingBot(total_capital=100000.0)
        # Disable screener filtering to only apply .env checks
        res = bot.search_stocks(symbols=self.symbols, use_screener=False, max_stocks=5)
        self.assertIsInstance(res, list)
        self.assertGreater(len(res), 0)
        for item in res:
            self.assertIn('symbol', item)
            self.assertIn('price', item)
            self.assertIn('volume', item)
            self.assertIsInstance(item['price'], (int, float))
            self.assertTrue(item['price'] > 0)

if __name__ == '__main__':
    unittest.main()
