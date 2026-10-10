#!/usr/bin/env python3
"""
Test suite for stock_screener module
"""

import os
import pickle
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set test environment before importing modules
os.environ["MIN_STOCK_PRICE"] = "5.0"
os.environ["MAX_STOCK_PRICE"] = "1000.0"
os.environ["MIN_DAILY_VOLUME"] = "500000"
os.environ["MAX_STOCK_VOLATILITY"] = "0.15"

# Check if yfinance and pandas are available
try:
    import yfinance

    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import pandas

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from stock_screener import (
    DELISTED_STOCKS,
    FALLBACK_STOCK_UNIVERSE,
    StockScreener,
    fetch_stock_universe_from_wikipedia,
    get_stock_universe,
    screen_for_trades,
)


class TestStockScreener(unittest.TestCase):
    """Test cases for StockScreener class"""

    def setUp(self):
        """Set up test fixtures"""
        self.screener = StockScreener()

    def test_screener_initialization(self):
        """Test that screener initializes correctly"""
        self.assertIsNotNone(self.screener)
        self.assertEqual(self.screener.cache, {})
        self.assertIsNone(self.screener.last_screen_time)
        self.assertEqual(self.screener.last_screened_stocks, [])

    def test_filter_stock_passes(self):
        """Test that valid stocks pass filtering"""
        stock_data = {
            "symbol": "AAPL",
            "price": 150.0,
            "volume": 70000000,
            "volatility": 0.05,
            "marketCap": 2000000000000,
        }

        passes, reason = self.screener.filter_stock(stock_data)
        self.assertTrue(passes)
        self.assertEqual(reason, "Passed all filters")

    def test_filter_stock_price_too_low(self):
        """Test that stocks below MIN_STOCK_PRICE are filtered out"""
        stock_data = {
            "symbol": "PENNY",
            "price": 2.0,  # Below $5 minimum
            "volume": 70000000,
            "volatility": 0.05,
            "marketCap": 100000000,
        }

        passes, reason = self.screener.filter_stock(stock_data)
        self.assertFalse(passes)
        self.assertIn("below minimum", reason)

    def test_filter_stock_price_too_high(self):
        """Test that stocks above MAX_STOCK_PRICE are filtered out"""
        stock_data = {
            "symbol": "EXPEN",
            "price": 1500.0,  # Above $1000 maximum
            "volume": 70000000,
            "volatility": 0.05,
            "marketCap": 2000000000000,
        }

        passes, reason = self.screener.filter_stock(stock_data)
        self.assertFalse(passes)
        self.assertIn("exceeds maximum", reason)

    def test_filter_stock_volume_too_low(self):
        """Test that stocks with low volume are filtered out"""
        stock_data = {
            "symbol": "LOWVOL",
            "price": 50.0,
            "volume": 100000,  # Below 500k minimum
            "volatility": 0.05,
            "marketCap": 1000000000,
        }

        passes, reason = self.screener.filter_stock(stock_data)
        self.assertFalse(passes)
        self.assertIn("below minimum", reason)

    def test_filter_stock_volatility_too_high(self):
        """Test that stocks with high volatility are filtered out"""
        stock_data = {
            "symbol": "VOLATILE",
            "price": 50.0,
            "volume": 70000000,
            "volatility": 0.25,  # Above 15% maximum
            "marketCap": 1000000000,
        }

        passes, reason = self.screener.filter_stock(stock_data)
        self.assertFalse(passes)
        self.assertIn("exceeds maximum", reason)

    def test_cache_functionality(self):
        """Test that caching works correctly"""
        stock_data = {
            "symbol": "TEST",
            "price": 100.0,
            "volume": 1000000,
            "volatility": 0.05,
            "marketCap": 1000000000,
        }

        # Cache data
        self.screener._cache_stock_data("TEST", stock_data)

        # Check cache is valid
        self.assertTrue(self.screener._is_cache_valid("TEST"))

        # Retrieve cached data
        cached = self.screener._get_cached_data("TEST")
        self.assertEqual(cached, stock_data)

    def test_get_popular_stocks(self):
        """Test that popular stocks are returned as fallback"""
        popular = self.screener.get_popular_stocks(count=5)

        self.assertEqual(len(popular), 5)
        self.assertIsInstance(popular, list)
        self.assertTrue(all(isinstance(s, str) for s in popular))

    @patch("stock_screener.YFINANCE_AVAILABLE", False)
    def test_screen_stocks_no_yfinance(self):
        """Test screening when yfinance is not available"""
        screener = StockScreener()

        # Should return empty list or fallback when yfinance unavailable
        result = screener.screen_stocks(
            candidate_symbols=["AAPL", "MSFT"], max_results=2
        )

        # Since yfinance is not available, fetch_stock_info returns None
        # So no stocks should pass screening
        self.assertEqual(len(result), 0)

    @unittest.skipIf(
        not YFINANCE_AVAILABLE or not PANDAS_AVAILABLE,
        "yfinance or pandas not available",
    )
    @patch("yfinance.Ticker")
    def test_fetch_stock_info_success(self, mock_ticker_class):
        """Test successful stock info fetch with yfinance"""
        # Mock ticker object
        mock_ticker = MagicMock()
        mock_ticker.fast_info.get.side_effect = lambda key, default=None: {
            "lastPrice": 150.0,
            "lastVolume": 70000000,
            "marketCap": 2000000000000,
        }.get(key, default)

        # Mock historical data
        import pandas as pd

        hist_data = pd.DataFrame(
            {
                "Close": [145, 147, 150, 149, 151],
                "Volume": [60000000, 65000000, 70000000, 68000000, 72000000],
            }
        )
        mock_ticker.history.return_value = hist_data

        mock_ticker_class.return_value = mock_ticker

        # Fetch stock info
        result = self.screener.fetch_stock_info("AAPL")

        self.assertIsNotNone(result)
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["price"], 150.0)
        self.assertGreater(result["volume"], 0)

    def test_convenience_function(self):
        """Test the convenience function screen_for_trades"""
        # This function should return a list of symbols
        # It may be empty if yfinance is not available or no stocks pass filters
        result = screen_for_trades(max_stocks=5)

        self.assertIsInstance(result, list)
        # Result should have <= 5 stocks
        self.assertLessEqual(len(result), 5)

    def test_delisted_stocks_excluded(self):
        """Test that known delisted stocks are excluded from universe"""
        from stock_screener import DELISTED_STOCKS, get_stock_universe

        # Get stock universe
        universe = get_stock_universe(use_cache=False, force_refresh=False)

        # Check that delisted stocks are not in the universe
        for delisted in DELISTED_STOCKS:
            self.assertNotIn(
                delisted,
                universe,
                f"Delisted stock {delisted} should not be in universe",
            )

        # Verify that the delisted list includes known delisted stocks
        self.assertIn("ATVI", DELISTED_STOCKS, "ATVI should be in delisted list")
        self.assertIn("PXD", DELISTED_STOCKS, "PXD should be in delisted list")

    def test_fallback_universe_excludes_delisted(self):
        """Test that fallback universe doesn't contain delisted stocks"""
        from stock_screener import DELISTED_STOCKS, FALLBACK_STOCK_UNIVERSE

        # Check that delisted stocks are not in the fallback universe
        for delisted in DELISTED_STOCKS:
            self.assertNotIn(
                delisted,
                FALLBACK_STOCK_UNIVERSE,
                f"Delisted stock {delisted} should not be in fallback universe",
            )


class TestStockScreenerIntegration(unittest.TestCase):
    """Integration tests for stock screener"""

    def test_screen_stocks_with_valid_candidates(self):
        """Test screening with a list of known valid stocks"""
        screener = StockScreener()

        # Use major stocks that should pass most filters
        candidates = ["AAPL", "MSFT", "GOOGL"]

        # This test may fail if yfinance is not available or API limits hit
        # So we'll make it lenient
        try:
            result = screener.screen_stocks(candidate_symbols=candidates, max_results=2)

            # Should return some results (may be 0-2 depending on API availability)
            self.assertIsInstance(result, list)
            self.assertLessEqual(len(result), 2)

            # All results should be strings
            for symbol in result:
                self.assertIsInstance(symbol, str)

        except Exception as e:
            # If screening fails (e.g., no yfinance, API errors), that's okay for this test
            self.skipTest(f"Screening failed (expected in some environments): {e}")

    def test_screener_respects_max_results(self):
        """Test that screener respects max_results parameter"""
        screener = StockScreener()

        # Request max 3 results
        result = screener.screen_stocks(max_results=3)

        # Should return <= 3 results
        self.assertLessEqual(len(result), 3)


class TestDynamicStockUniverse(unittest.TestCase):
    """Test cases for dynamic stock universe functionality"""

    def test_fallback_universe_not_empty(self):
        """Test that fallback universe has stocks"""
        self.assertGreater(len(FALLBACK_STOCK_UNIVERSE), 0)
        self.assertGreater(
            len(FALLBACK_STOCK_UNIVERSE), 50
        )  # Should have at least 50 stocks

    def test_fallback_universe_valid_symbols(self):
        """Test that fallback universe contains valid ticker symbols"""
        for symbol in FALLBACK_STOCK_UNIVERSE[:10]:  # Check first 10
            self.assertIsInstance(symbol, str)
            self.assertTrue(symbol.isupper())  # Tickers should be uppercase
            self.assertGreater(len(symbol), 0)
            self.assertLessEqual(len(symbol), 5)  # Tickers are typically 1-5 characters

    @unittest.skipIf(not PANDAS_AVAILABLE, "pandas not available")
    @patch("stock_screener.PANDAS_AVAILABLE", True)
    @patch("pandas.read_html")
    def test_fetch_from_wikipedia_success(self, mock_read_html):
        """Test successful fetch from Wikipedia"""
        import pandas as pd

        # Mock DataFrame with stock symbols
        mock_df = pd.DataFrame(
            {
                "Symbol": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
                "Company": ["Apple", "Microsoft", "Alphabet", "Amazon", "Tesla"],
            }
        )
        mock_read_html.return_value = [mock_df]

        universe = fetch_stock_universe_from_wikipedia()

        # Should have symbols from the mock data
        self.assertGreater(len(universe), 0)
        self.assertIsInstance(universe, set)

    @patch("stock_screener.PANDAS_AVAILABLE", False)
    def test_fetch_from_wikipedia_no_pandas(self):
        """Test fetch when pandas is not available"""
        universe = fetch_stock_universe_from_wikipedia()

        # Should return empty set when pandas not available
        self.assertEqual(len(universe), 0)
        self.assertIsInstance(universe, set)

    @patch("stock_screener.fetch_stock_universe_from_wikipedia")
    def test_get_stock_universe_uses_fallback(self, mock_fetch):
        """Test that get_stock_universe uses fallback when Wikipedia fails"""
        # Mock Wikipedia fetch to return empty set
        mock_fetch.return_value = set()

        universe = get_stock_universe(use_cache=False)

        # Should use fallback
        self.assertGreater(len(universe), 0)
        self.assertIsInstance(universe, list)

    @patch("stock_screener.fetch_stock_universe_from_wikipedia")
    def test_get_stock_universe_success(self, mock_fetch):
        """Test successful universe building from Wikipedia"""
        # Mock Wikipedia fetch to return large set
        mock_symbols = set([f"SYM{i}" for i in range(200)])
        mock_fetch.return_value = mock_symbols

        universe = get_stock_universe(use_cache=False)

        # Should have many symbols
        self.assertGreater(len(universe), 100)
        self.assertIsInstance(universe, list)

    def test_screener_with_custom_universe(self):
        """Test screener initialization with custom universe"""
        custom_universe = ["AAPL", "MSFT", "GOOGL"]
        screener = StockScreener(stock_universe=custom_universe)

        self.assertEqual(len(screener.stock_universe), 3)
        self.assertEqual(screener.stock_universe, custom_universe)

    def test_screener_universe_not_empty(self):
        """Test that screener always has a universe"""
        screener = StockScreener()

        self.assertIsNotNone(screener.stock_universe)
        self.assertGreater(len(screener.stock_universe), 0)
        self.assertIsInstance(screener.stock_universe, list)

    def test_screener_refresh_universe(self):
        """Test that screener can refresh its universe"""
        screener = StockScreener()
        original_size = len(screener.stock_universe)

        # Refresh should work without errors
        new_size = screener.refresh_universe(force=False)

        self.assertIsInstance(new_size, int)
        self.assertGreater(new_size, 0)
        self.assertEqual(new_size, len(screener.stock_universe))


class TestStockScreenerPerformance(unittest.TestCase):
    """Test cases for screener performance"""

    def test_screener_limits_checks(self):
        """Test that screener limits number of stocks checked for performance"""
        # Create screener with large universe
        large_universe = [f"SYM{i}" for i in range(1000)]
        screener = StockScreener(stock_universe=large_universe)

        # Mock fetch_stock_info to always return None (fast)
        with patch.object(screener, "fetch_stock_info", return_value=None):
            # Screen should complete quickly even with large universe
            import time

            start = time.time()
            results = screener.screen_stocks(max_results=10, use_cache=False)
            elapsed = time.time() - start

            # Should complete in reasonable time (< 5 seconds even with mocking)
            self.assertLess(elapsed, 5.0)

    def test_screener_caching_works(self):
        """Test that screener caching improves performance"""
        screener = StockScreener()

        # First call - no cache
        results1 = screener.screen_stocks(max_results=5, use_cache=False)

        # Set cached results
        screener.last_screened_stocks = ["AAPL", "MSFT", "GOOGL"]
        from datetime import datetime

        screener.last_screen_time = datetime.now()

        # Second call - should use cache
        results2 = screener.screen_stocks(max_results=5, use_cache=True)

        # Should return cached results
        self.assertEqual(results2, ["AAPL", "MSFT", "GOOGL"])


if __name__ == "__main__":
    unittest.main()
#!/usr/bin/env python3
"""
Test suite for stock_screener enhancements with sentiment and ML integration
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set test environment before importing modules
os.environ["MIN_STOCK_PRICE"] = "5.0"
os.environ["MAX_STOCK_PRICE"] = "1000.0"
os.environ["MIN_DAILY_VOLUME"] = "500000"
os.environ["MAX_STOCK_VOLATILITY"] = "0.15"
os.environ["ENABLE_SENTIMENT_FILTER"] = "true"
os.environ["ENABLE_ML_FILTER"] = "true"
os.environ["ENABLE_PORTFOLIO_OPTIMIZATION"] = "true"
os.environ["MIN_SENTIMENT_SCORE"] = "0.0"
os.environ["MIN_ML_CONFIDENCE"] = "0.6"
os.environ["MIN_ML_WIN_PROBABILITY"] = "0.55"
os.environ["MIN_DIVERSIFICATION_SCORE"] = "0.3"

# Check if yfinance and pandas are available
try:
    import yfinance

    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import pandas

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from stock_screener import StockScreener


class TestStockScreenerSentimentIntegration(unittest.TestCase):
    """Test cases for sentiment analysis integration"""

    def setUp(self):
        """Set up test fixtures"""
        # Create screener without sentiment analyzer to test gracefully
        self.screener = StockScreener(stock_universe=["AAPL", "MSFT", "GOOGL"])

    def test_screener_initialization_with_sentiment(self):
        """Test that screener initializes with sentiment support"""
        # Screener should handle missing sentiment analyzer gracefully
        self.assertIsNotNone(self.screener)
        # Sentiment analyzer might not be available in test environment
        # which is OK - screener should still work

    @patch("stock_screener.SENTIMENT_AVAILABLE", True)
    @patch("stock_screener.SentimentAnalyzer")
    def test_sentiment_filter_positive(self, mock_sentiment_class):
        """Test sentiment filter with positive sentiment"""
        # Mock sentiment analyzer
        mock_analyzer = MagicMock()
        mock_analyzer.get_sentiment_score.return_value = {
            "overall_score": 0.5,
            "sentiment_signal": "BULLISH",
            "article_count": 10,
            "confidence": 0.8,
        }
        mock_sentiment_class.return_value = mock_analyzer

        # Create screener with mocked sentiment
        screener = StockScreener(stock_universe=["AAPL"], enable_sentiment=True)
        screener.sentiment_analyzer = mock_analyzer

        # Test filter
        passes, reason, sentiment_data = screener.filter_by_sentiment("AAPL")

        self.assertTrue(passes)
        self.assertIn("Sentiment OK", reason)
        self.assertIsNotNone(sentiment_data)
        self.assertEqual(sentiment_data["sentiment_signal"], "BULLISH")

    @patch("stock_screener.SENTIMENT_AVAILABLE", True)
    @patch("stock_screener.SentimentAnalyzer")
    def test_sentiment_filter_negative(self, mock_sentiment_class):
        """Test sentiment filter with negative sentiment"""
        # Mock sentiment analyzer
        mock_analyzer = MagicMock()
        mock_analyzer.get_sentiment_score.return_value = {
            "overall_score": -0.5,
            "sentiment_signal": "BEARISH",
            "article_count": 10,
            "confidence": 0.8,
        }
        mock_sentiment_class.return_value = mock_analyzer

        # Create screener with mocked sentiment
        screener = StockScreener(stock_universe=["XYZ"], enable_sentiment=True)
        screener.sentiment_analyzer = mock_analyzer

        # Test filter
        passes, reason, sentiment_data = screener.filter_by_sentiment("XYZ")

        self.assertFalse(passes)
        self.assertIn("Negative sentiment", reason)
        self.assertIsNotNone(sentiment_data)

    def test_sentiment_filter_disabled(self):
        """Test sentiment filter when disabled"""
        screener = StockScreener(stock_universe=["AAPL"], enable_sentiment=False)

        # Test filter
        passes, reason, sentiment_data = screener.filter_by_sentiment("AAPL")

        self.assertTrue(passes)
        self.assertIn("not enabled", reason)
        self.assertIsNone(sentiment_data)

    def test_sentiment_filter_insufficient_data(self):
        """Test sentiment filter with insufficient news data"""
        mock_analyzer = MagicMock()
        mock_analyzer.get_sentiment_score.return_value = {
            "overall_score": 0.5,
            "sentiment_signal": "NEUTRAL",
            "article_count": 1,  # Less than 3
            "confidence": 0.2,
        }

        screener = StockScreener(stock_universe=["AAPL"])
        screener.sentiment_analyzer = mock_analyzer

        # Test filter
        passes, reason, sentiment_data = screener.filter_by_sentiment("AAPL")

        self.assertTrue(passes)
        self.assertIn("Insufficient news data", reason)


class TestStockScreenerMLIntegration(unittest.TestCase):
    """Test cases for ML signal filter integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.screener = StockScreener(stock_universe=["AAPL", "MSFT", "GOOGL"])

    @patch("stock_screener.ML_FILTER_AVAILABLE", True)
    def test_ml_filter_high_quality(self):
        """Test ML filter with high quality signal"""
        # Mock ML filter
        mock_filter = MagicMock()
        mock_filter.is_trained = True
        mock_filter.should_filter_signal.return_value = (
            False,  # Don't filter (high quality)
            {"confidence": 0.8, "win_probability": 0.7},
        )

        # Create screener with mocked ML
        screener = StockScreener(stock_universe=["AAPL"], enable_ml=True)
        screener.ml_filter = mock_filter

        stock_data = {"price": 150.0, "volume": 70000000, "volatility": 0.05}

        # Test filter
        passes, reason, ml_scores = screener.filter_by_ml_quality(
            "AAPL", stock_data, indicators={}
        )

        self.assertTrue(passes)
        self.assertIn("Good ML quality", reason)
        self.assertIsNotNone(ml_scores)
        self.assertEqual(ml_scores["confidence"], 0.8)

    @patch("stock_screener.ML_FILTER_AVAILABLE", True)
    def test_ml_filter_low_quality(self):
        """Test ML filter with low quality signal"""
        # Mock ML filter
        mock_filter = MagicMock()
        mock_filter.is_trained = True
        mock_filter.should_filter_signal.return_value = (
            True,  # Filter out (low quality)
            {"confidence": 0.4, "win_probability": 0.4},
        )

        # Create screener with mocked ML
        screener = StockScreener(stock_universe=["XYZ"], enable_ml=True)
        screener.ml_filter = mock_filter

        stock_data = {"price": 50.0, "volume": 1000000, "volatility": 0.1}

        # Test filter
        passes, reason, ml_scores = screener.filter_by_ml_quality(
            "XYZ", stock_data, indicators={}
        )

        self.assertFalse(passes)
        self.assertIn("Low ML quality", reason)
        self.assertIsNotNone(ml_scores)

    def test_ml_filter_disabled(self):
        """Test ML filter when disabled"""
        screener = StockScreener(stock_universe=["AAPL"], enable_ml=False)

        stock_data = {"price": 150.0, "volume": 70000000, "volatility": 0.05}

        # Test filter
        passes, reason, ml_scores = screener.filter_by_ml_quality(
            "AAPL", stock_data, indicators={}
        )

        self.assertTrue(passes)
        self.assertIn("not enabled", reason)
        self.assertIsNone(ml_scores)


class TestStockScreenerPortfolioIntegration(unittest.TestCase):
    """Test cases for portfolio optimization integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.screener = StockScreener(stock_universe=["AAPL", "MSFT", "GOOGL"])

    @patch("stock_screener.PORTFOLIO_OPTIMIZER_AVAILABLE", True)
    @patch("stock_screener.PORTFOLIO_OPTIMIZER_AVAILABLE", True)
    def test_diversification_calculation(self):
        """Test portfolio diversification calculation"""
        # Mock portfolio optimizer
        mock_optimizer = MagicMock()
        mock_optimizer.calculate_diversification_score.return_value = 0.75

        # Create screener with mocked optimizer
        screener = StockScreener(
            stock_universe=["AAPL", "MSFT", "GOOGL"], enable_portfolio_opt=True
        )
        screener.portfolio_optimizer = mock_optimizer

        # Test diversification
        score, reason = screener.calculate_portfolio_diversification(
            ["AAPL", "MSFT", "GOOGL"]
        )

        self.assertEqual(score, 0.75)
        self.assertIn("Good diversification", reason)

    @patch("stock_screener.PORTFOLIO_OPTIMIZER_AVAILABLE", True)
    def test_low_diversification(self):
        """Test detection of low diversification"""
        # Mock portfolio optimizer
        mock_optimizer = MagicMock()
        mock_optimizer.calculate_diversification_score.return_value = 0.2

        # Create screener with mocked optimizer
        screener = StockScreener(
            stock_universe=["AAPL", "MSFT"], enable_portfolio_opt=True
        )
        screener.portfolio_optimizer = mock_optimizer

        # Test diversification
        score, reason = screener.calculate_portfolio_diversification(["AAPL", "MSFT"])

        self.assertEqual(score, 0.2)
        self.assertIn("Low diversification", reason)

    def test_diversification_disabled(self):
        """Test diversification when optimizer disabled"""
        screener = StockScreener(
            stock_universe=["AAPL", "MSFT"], enable_portfolio_opt=False
        )

        # Test diversification
        score, reason = screener.calculate_portfolio_diversification(["AAPL", "MSFT"])

        self.assertEqual(score, 1.0)  # Default when disabled
        self.assertIn("not enabled", reason)


class TestStockScreenerAdvancedScreening(unittest.TestCase):
    """Test cases for advanced screening with all filters"""

    @unittest.skipIf(
        not YFINANCE_AVAILABLE or not PANDAS_AVAILABLE,
        "yfinance or pandas not available",
    )
    @patch("stock_screener.YFINANCE_AVAILABLE", True)
    @patch("yfinance.Ticker")
    def test_screen_stocks_with_advanced_filters(self, mock_ticker_class):
        """Test screening with advanced filters enabled"""
        # Mock ticker object
        mock_ticker = MagicMock()
        mock_ticker.fast_info.get.side_effect = lambda key: {
            "lastPrice": 150.0,
            "lastVolume": 70000000,
            "marketCap": 2000000000000,
        }.get(key)

        # Mock historical data
        import pandas as pd

        hist_data = pd.DataFrame(
            {
                "Close": [145, 147, 150, 149, 151],
                "Volume": [60000000, 65000000, 70000000, 68000000, 72000000],
            }
        )
        mock_ticker.history.return_value = hist_data
        mock_ticker_class.return_value = mock_ticker

        # Create screener
        screener = StockScreener(stock_universe=["AAPL", "MSFT"])

        # Test screening
        result = screener.screen_stocks(
            candidate_symbols=["AAPL"],
            max_results=5,
            use_cache=False,
            use_advanced_filters=True,
        )

        # Should return results (may be empty if filters too strict)
        self.assertIsInstance(result, list)

    @unittest.skipIf(
        not YFINANCE_AVAILABLE or not PANDAS_AVAILABLE,
        "yfinance or pandas not available",
    )
    @patch("stock_screener.YFINANCE_AVAILABLE", True)
    @patch("yfinance.Ticker")
    def test_screen_stocks_without_advanced_filters(self, mock_ticker_class):
        """Test screening without advanced filters"""
        # Mock ticker object
        mock_ticker = MagicMock()
        mock_ticker.fast_info.get.side_effect = lambda key: {
            "lastPrice": 150.0,
            "lastVolume": 70000000,
            "marketCap": 2000000000000,
        }.get(key)

        # Mock historical data
        import pandas as pd

        hist_data = pd.DataFrame(
            {
                "Close": [145, 147, 150, 149, 151],
                "Volume": [60000000, 65000000, 70000000, 68000000, 72000000],
            }
        )
        mock_ticker.history.return_value = hist_data
        mock_ticker_class.return_value = mock_ticker

        # Create screener
        screener = StockScreener(stock_universe=["AAPL"])

        # Test screening
        result = screener.screen_stocks(
            candidate_symbols=["AAPL"],
            max_results=5,
            use_cache=False,
            use_advanced_filters=False,
        )

        # Should return results based on basic filters only
        self.assertIsInstance(result, list)


class TestStockScreenerSwingCandidates(unittest.TestCase):
    """Test cases for swing trade candidate selection"""

    @unittest.skipIf(
        not YFINANCE_AVAILABLE or not PANDAS_AVAILABLE,
        "yfinance or pandas not available",
    )
    @patch("stock_screener.YFINANCE_AVAILABLE", True)
    @patch("yfinance.Ticker")
    def test_get_swing_trade_candidates(self, mock_ticker_class):
        """Test comprehensive swing trade candidate selection"""
        # Mock ticker object
        mock_ticker = MagicMock()
        mock_ticker.fast_info.get.side_effect = lambda key: {
            "lastPrice": 150.0,
            "lastVolume": 70000000,
            "marketCap": 2000000000000,
        }.get(key)

        # Mock historical data
        import pandas as pd

        hist_data = pd.DataFrame(
            {
                "Close": [145, 147, 150, 149, 151],
                "Volume": [60000000, 65000000, 70000000, 68000000, 72000000],
            }
        )
        mock_ticker.history.return_value = hist_data
        mock_ticker_class.return_value = mock_ticker

        # Create screener
        screener = StockScreener(stock_universe=["AAPL", "MSFT", "GOOGL"])

        # Test swing candidate selection
        result = screener.get_swing_trade_candidates(
            max_results=3,
            sentiment_weight=0.3,
            ml_weight=0.4,
            diversification_weight=0.3,
        )

        # Should return list of dictionaries with scoring
        self.assertIsInstance(result, list)

        # Check structure if results returned
        if result:
            for candidate in result:
                self.assertIn("symbol", candidate)
                self.assertIn("composite_score", candidate)
                self.assertIn("sentiment_score", candidate)
                self.assertIn("ml_confidence", candidate)
                self.assertIn("ml_win_probability", candidate)

    def test_swing_candidates_empty_universe(self):
        """Test swing candidates with empty universe"""
        screener = StockScreener(stock_universe=[])

        # Should handle empty universe gracefully
        result = screener.get_swing_trade_candidates(max_results=5)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)


class TestStockScreenerBackwardCompatibility(unittest.TestCase):
    """Test cases to ensure backward compatibility"""

    def test_old_initialization_still_works(self):
        """Test that old initialization method still works"""
        # Old way without advanced features
        screener = StockScreener(stock_universe=["AAPL", "MSFT"])

        self.assertIsNotNone(screener)
        self.assertEqual(len(screener.stock_universe), 2)

    def test_basic_screening_unchanged(self):
        """Test that basic screening still works as before"""
        screener = StockScreener(stock_universe=["AAPL"])

        stock_data = {
            "symbol": "AAPL",
            "price": 150.0,
            "volume": 70000000,
            "volatility": 0.05,
            "marketCap": 2000000000000,
        }

        # Test basic filter
        passes, reason = screener.filter_stock(stock_data)

        self.assertTrue(passes)
        self.assertEqual(reason, "Passed all filters")

    def test_get_screened_or_fallback_unchanged(self):
        """Test that get_screened_or_fallback still works"""
        screener = StockScreener(stock_universe=["AAPL", "MSFT"])

        # Should work without errors
        result = screener.get_screened_or_fallback(max_results=5)

        self.assertIsInstance(result, list)


if __name__ == "__main__":
    unittest.main()
#!/usr/bin/env python3
"""
Test that stock screener provides helpful warnings when filters are too restrictive
and uses fallback mechanism when no stocks pass filtering.
"""

import os
import sys
import logging
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

# Set environment variables before importing modules
os.environ['MIN_STOCK_PRICE'] = '1'
os.environ['MAX_STOCK_PRICE'] = '10'
os.environ['MIN_DAILY_VOLUME'] = '500000'
os.environ['ENABLE_STOCK_SCREENER'] = 'true'
os.environ['ENABLE_ML_FILTER'] = 'false'
os.environ['ENABLE_SENTIMENT_FILTER'] = 'false'

from stock_screener import StockScreener, get_top_performers_watchlist


class TestStockScreenerFilterWarnings(unittest.TestCase):
    """Test stock screener behavior with restrictive filters"""

    def setUp(self):
        """Set up test fixtures"""
        # Set up logging to capture warnings
        self.log_stream = StringIO()
        self.log_handler = logging.StreamHandler(self.log_stream)
        self.log_handler.setLevel(logging.WARNING)
        
        # Get the stock_screener logger
        self.logger = logging.getLogger('stock_screener')
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.WARNING)

    def tearDown(self):
        """Clean up after tests"""
        self.logger.removeHandler(self.log_handler)

    def test_restrictive_price_filter_shows_warning(self):
        """Test that restrictive MAX_STOCK_PRICE shows helpful warning"""
        # Create screener with a small universe for faster testing
        test_universe = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        screener = StockScreener(stock_universe=test_universe)
        
        # Screen stocks with restrictive filters
        results = screener.screen_stocks(max_results=10, prioritize=False)
        
        # Get log output
        log_output = self.log_stream.getvalue()
        
        # Should have warnings about no stocks passing
        self.assertIn('NO STOCKS PASSED SCREENING FILTERS', log_output)
        
        # Should have specific recommendation about MAX_STOCK_PRICE
        self.assertIn('MAX_STOCK_PRICE', log_output)
        self.assertIn('may be too low', log_output)
        self.assertIn('Recommendation', log_output)

    def test_fallback_mechanism_in_get_swing_trade_candidates(self):
        """Test that get_swing_trade_candidates uses fallback when screening fails"""
        # Create screener with small universe
        test_universe = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        screener = StockScreener(stock_universe=test_universe)
        
        # Get candidates (should fallback to popular stocks)
        candidates = screener.get_swing_trade_candidates(max_results=5)
        
        # Should return some candidates using fallback mechanism
        # (May be empty if yfinance isn't working, but should not raise exception)
        self.assertIsInstance(candidates, list)
        
        # Check log output
        log_output = self.log_stream.getvalue()
        
        # Should mention fallback mechanism
        if len(candidates) > 0:
            self.assertIn('fallback', log_output.lower())

    @patch('stock_screener.YFINANCE_AVAILABLE', False)
    def test_graceful_handling_without_yfinance(self):
        """Test that screener handles missing yfinance gracefully"""
        test_universe = ['AAPL', 'MSFT']
        screener = StockScreener(stock_universe=test_universe)
        
        # Should not raise exception
        results = screener.screen_stocks(max_results=5)
        
        # Results should be empty or use fallback
        self.assertIsInstance(results, list)

    def test_get_top_performers_with_restrictive_filters(self):
        """Test get_top_performers_watchlist with restrictive filters"""
        # This should use the fallback mechanism and return some stocks
        # instead of an empty list
        try:
            performers = get_top_performers_watchlist(max_stocks=10)
            
            # Should return a list (may be empty if yfinance fails, but should not crash)
            self.assertIsInstance(performers, list)
            
            # If we got performers, they should have the expected structure
            if len(performers) > 0:
                self.assertIn('symbol', performers[0])
                
        except Exception as e:
            # Should not raise exception, but if it does, fail the test
            self.fail(f"get_top_performers_watchlist raised exception: {e}")


class TestStockScreenerRecommendations(unittest.TestCase):
    """Test that screener provides actionable recommendations"""

    def test_recommendation_messages_for_common_issues(self):
        """Test that common filtering issues get helpful recommendations"""
        # Capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.WARNING)
        
        logger = logging.getLogger('stock_screener')
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        
        try:
            # Test with very restrictive price range
            test_universe = ['AAPL', 'MSFT', 'GOOGL']
            screener = StockScreener(stock_universe=test_universe)
            results = screener.screen_stocks(max_results=5, prioritize=False)
            
            log_output = log_stream.getvalue()
            
            # Should provide specific recommendations
            if 'NO STOCKS PASSED SCREENING FILTERS' in log_output:
                # Should mention adjustment recommendations
                self.assertIn('Suggested action', log_output)
                self.assertIn('MIN_STOCK_PRICE', log_output)
                self.assertIn('MAX_STOCK_PRICE', log_output)
                
        finally:
            logger.removeHandler(handler)


if __name__ == '__main__':
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(name)s - %(message)s'
    )
    
    # Run tests
    unittest.main()
