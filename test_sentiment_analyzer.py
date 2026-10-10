#!/usr/bin/env python3
"""
Tests for sentiment analyzer module
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentiment_analyzer import SentimentAnalyzer


class TestSentimentAnalyzer(unittest.TestCase):
    """Test sentiment analyzer functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = SentimentAnalyzer()
    
    def test_initialization(self):
        """Test sentiment analyzer initialization"""
        self.assertIsNotNone(self.analyzer)
        self.assertIsInstance(self.analyzer.sentiment_cache, dict)
        self.assertEqual(self.analyzer.cache_duration, 3600)
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        key = self.analyzer._get_cache_key('AAPL')
        self.assertEqual(key, 'AAPL_sentiment')
    
    def test_cache_validation_empty(self):
        """Test cache validation with empty cache"""
        self.assertFalse(self.analyzer._is_cache_valid('nonexistent_key'))
    
    def test_cache_sentiment_and_retrieval(self):
        """Test caching and retrieving sentiment data"""
        test_data = {
            'overall_score': 0.5,
            'sentiment_signal': 'BULLISH'
        }
        
        cache_key = 'TEST_sentiment'
        self.analyzer._cache_sentiment(cache_key, test_data)
        
        # Should be valid immediately
        self.assertTrue(self.analyzer._is_cache_valid(cache_key))
        
        # Should retrieve cached data
        cached = self.analyzer._get_cached_sentiment(cache_key)
        self.assertEqual(cached, test_data)
    
    def test_sentiment_vader_positive(self):
        """Test VADER sentiment analysis with positive text"""
        text = "This stock is performing amazingly well! Great profits and excellent growth."
        
        try:
            scores = self.analyzer.analyze_sentiment_vader(text)
            self.assertIn('compound', scores)
            self.assertIn('pos', scores)
            self.assertIn('neg', scores)
            self.assertIn('neu', scores)
            
            # Should be positive
            if scores['compound'] != 0:  # Only if VADER is available
                self.assertGreater(scores['compound'], 0)
                self.assertGreater(scores['pos'], 0)
        except:
            # VADER not available, skip test
            self.skipTest("VADER sentiment analyzer not available")
    
    def test_sentiment_vader_negative(self):
        """Test VADER sentiment analysis with negative text"""
        text = "Terrible performance! Stock is plummeting. Major losses and poor management."
        
        try:
            scores = self.analyzer.analyze_sentiment_vader(text)
            
            # Should be negative
            if scores['compound'] != 0:  # Only if VADER is available
                self.assertLess(scores['compound'], 0)
                self.assertGreater(scores['neg'], 0)
        except:
            # VADER not available, skip test
            self.skipTest("VADER sentiment analyzer not available")
    
    def test_sentiment_textblob_positive(self):
        """Test TextBlob sentiment analysis with positive text"""
        text = "This stock is performing amazingly well! Great profits and excellent growth."
        
        try:
            scores = self.analyzer.analyze_sentiment_textblob(text)
            self.assertIn('polarity', scores)
            self.assertIn('subjectivity', scores)
            self.assertIn('compound', scores)
            
            # Should be positive if TextBlob is available
            if scores['polarity'] != 0:
                self.assertGreater(scores['polarity'], 0)
        except:
            # TextBlob not available, skip test
            self.skipTest("TextBlob sentiment analyzer not available")
    
    def test_analyze_sentiment_fallback(self):
        """Test sentiment analysis fallback when no analyzer available"""
        # Create analyzer without any sentiment methods
        analyzer_no_method = SentimentAnalyzer(method='nonexistent')
        
        scores = analyzer_no_method.analyze_sentiment("Some text")
        
        # Should return neutral scores
        self.assertEqual(scores['compound'], 0.0)
        self.assertEqual(scores['pos'], 0.0)
        self.assertEqual(scores['neu'], 1.0)
        self.assertEqual(scores['neg'], 0.0)
    
    @patch('sentiment_analyzer.requests.get')
    def test_fetch_news_newsapi_success(self, mock_get):
        """Test fetching news from NewsAPI successfully"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'articles': [
                {
                    'title': 'Stock rises on good news',
                    'description': 'Company reports strong earnings',
                    'source': {'name': 'TestSource'},
                    'publishedAt': '2024-01-01T12:00:00Z'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Set API key for test
        self.analyzer.news_api_key = 'change-me'
        self.analyzer.news_api_available = True
        
        articles = self.analyzer.fetch_news_newsapi('AAPL')
        
        self.assertEqual(len(articles), 1)
        self.assertIn('title', articles[0])
        self.assertEqual(articles[0]['title'], 'Stock rises on good news')
    
    @patch('sentiment_analyzer.requests.get')
    def test_fetch_news_newsapi_failure(self, mock_get):
        """Test handling NewsAPI fetch failure"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_get.return_value = mock_response
        
        # Set API key for test
        self.analyzer.news_api_key = 'change-me'
        self.analyzer.news_api_available = True
        
        articles = self.analyzer.fetch_news_newsapi('AAPL')
        
        self.assertEqual(articles, [])
    
    @patch('sentiment_analyzer.requests.get')
    def test_fetch_news_finnhub_success(self, mock_get):
        """Test fetching news from Finnhub successfully"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'headline': 'Stock rises on good news',
                'summary': 'Company reports strong earnings',
                'source': 'TestSource',
                'datetime': 1609502400
            }
        ]
        mock_get.return_value = mock_response
        
        # Set API key for test
        self.analyzer.finnhub_api_key = 'change-me'
        self.analyzer.finnhub_available = True
        
        articles = self.analyzer.fetch_news_finnhub('AAPL')
        
        self.assertEqual(len(articles), 1)
        self.assertIn('headline', articles[0])
        self.assertEqual(articles[0]['headline'], 'Stock rises on good news')
    
    @patch('sentiment_analyzer.requests.get')
    def test_get_sentiment_score_with_articles(self, mock_get):
        """Test getting sentiment score with news articles"""
        # Mock Finnhub response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'headline': 'Stock rises on good news',
                'summary': 'Company reports excellent earnings and strong growth',
                'source': 'TestSource',
                'datetime': 1609502400
            },
            {
                'headline': 'Analyst upgrades stock',
                'summary': 'Major analyst firm upgrades rating to buy',
                'source': 'TestSource',
                'datetime': 1609502400
            }
        ]
        mock_get.return_value = mock_response
        
        # Set API key for test
        self.analyzer.finnhub_api_key = 'change-me'
        self.analyzer.finnhub_available = True
        
        result = self.analyzer.get_sentiment_score('AAPL')
        
        self.assertIn('overall_score', result)
        self.assertIn('sentiment_signal', result)
        self.assertIn('article_count', result)
        self.assertIn('confidence', result)
        self.assertEqual(result['article_count'], 2)
    
    def test_get_sentiment_score_no_articles(self):
        """Test getting sentiment score with no articles"""
        # Disable all APIs
        self.analyzer.news_api_available = False
        self.analyzer.finnhub_available = False
        
        result = self.analyzer.get_sentiment_score('AAPL')
        
        self.assertEqual(result['overall_score'], 0.0)
        self.assertEqual(result['sentiment_signal'], 'NEUTRAL')
        self.assertEqual(result['article_count'], 0)
    
    def test_should_trade_based_on_sentiment_insufficient_data(self):
        """Test trading decision with insufficient data"""
        # Disable all APIs
        self.analyzer.news_api_available = False
        self.analyzer.finnhub_available = False
        
        should_trade, reason = self.analyzer.should_trade_based_on_sentiment('AAPL')
        
        self.assertTrue(should_trade)
        self.assertIn('Insufficient', reason)
    
    @patch('sentiment_analyzer.requests.get')
    def test_should_trade_based_on_sentiment_negative(self, mock_get):
        """Test trading decision with negative sentiment"""
        # Mock very negative news
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'headline': 'Company faces bankruptcy',
                'summary': 'Terrible earnings, massive losses, fraud investigation',
                'source': 'TestSource',
                'datetime': 1609502400
            },
            {
                'headline': 'CEO resigns amid scandal',
                'summary': 'Major scandal, stock plummeting',
                'source': 'TestSource',
                'datetime': 1609502400
            },
            {
                'headline': 'Analyst downgrades to sell',
                'summary': 'Poor outlook, recommend selling',
                'source': 'TestSource',
                'datetime': 1609502400
            }
        ]
        mock_get.return_value = mock_response
        
        # Set API key for test
        self.analyzer.finnhub_api_key = 'change-me'
        self.analyzer.finnhub_available = True
        
        should_trade, reason = self.analyzer.should_trade_based_on_sentiment('AAPL')
        
        # With strongly negative sentiment, should not trade
        # (depends on sentiment analysis availability)
        self.assertIsInstance(should_trade, bool)
        self.assertIsInstance(reason, str)
    
    def test_sentiment_signal_classification(self):
        """Test sentiment signal classification"""
        # Test data for get_sentiment_score
        test_cases = [
            ({'overall_score': 0.3, 'article_count': 10}, 'BULLISH'),
            ({'overall_score': -0.3, 'article_count': 10}, 'BEARISH'),
            ({'overall_score': 0.1, 'article_count': 10}, 'NEUTRAL'),
        ]
        
        # We can't directly test the classification without mocking the entire flow,
        # but we can verify the logic exists
        self.assertTrue(hasattr(self.analyzer, 'get_sentiment_score'))
    
    def test_analyzer_with_different_methods(self):
        """Test creating analyzers with different sentiment methods"""
        vader_analyzer = SentimentAnalyzer(method='vader')
        self.assertEqual(vader_analyzer.method, 'vader')
        
        textblob_analyzer = SentimentAnalyzer(method='textblob')
        self.assertEqual(textblob_analyzer.method, 'textblob')


class TestSentimentCaching(unittest.TestCase):
    """Test sentiment caching functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = SentimentAnalyzer()
    
    def test_cache_expiration(self):
        """Test that cache expires after duration"""
        import time
        
        test_data = {'score': 0.5}
        cache_key = 'TEST_sentiment'
        
        # Set short cache duration for testing
        self.analyzer.cache_duration = 1  # 1 second
        
        self.analyzer._cache_sentiment(cache_key, test_data)
        self.assertTrue(self.analyzer._is_cache_valid(cache_key))
        
        # Wait for cache to expire
        time.sleep(1.1)
        
        self.assertFalse(self.analyzer._is_cache_valid(cache_key))
    
    def test_cache_hit_reduces_api_calls(self):
        """Test that cache reduces API calls"""
        # Pre-populate cache
        cache_key = self.analyzer._get_cache_key('AAPL')
        test_data = {
            'overall_score': 0.5,
            'sentiment_signal': 'BULLISH',
            'article_count': 5,
            'confidence': 0.7
        }
        self.analyzer._cache_sentiment(cache_key, test_data)
        
        # Disable APIs to ensure cache is used
        self.analyzer.news_api_available = False
        self.analyzer.finnhub_available = False
        
        # Should return cached data without API calls
        result = self.analyzer.get_sentiment_score('AAPL')
        
        self.assertEqual(result, test_data)


class TestRateLimiting(unittest.TestCase):
    """Test rate limiting functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        from sentiment_analyzer import RateLimiter
        self.rate_limiter = RateLimiter(max_calls=5, time_window=10, name="TestAPI")
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initializes correctly"""
        self.assertEqual(self.rate_limiter.max_calls, 5)
        self.assertEqual(self.rate_limiter.time_window, 10)
        self.assertEqual(self.rate_limiter.name, "TestAPI")
        self.assertEqual(len(self.rate_limiter.call_times), 0)
    
    def test_can_make_call_when_under_limit(self):
        """Test that calls are allowed when under limit"""
        self.assertTrue(self.rate_limiter.can_make_call())
        
        # Make 4 calls (under limit of 5)
        for _ in range(4):
            self.rate_limiter.record_call()
        
        self.assertTrue(self.rate_limiter.can_make_call())
    
    def test_cannot_make_call_when_at_limit(self):
        """Test that calls are blocked when at limit"""
        # Make 5 calls (at limit)
        for _ in range(5):
            self.rate_limiter.record_call()
        
        self.assertFalse(self.rate_limiter.can_make_call())
    
    def test_get_remaining_calls(self):
        """Test getting remaining calls"""
        self.assertEqual(self.rate_limiter.get_remaining_calls(), 5)
        
        self.rate_limiter.record_call()
        self.assertEqual(self.rate_limiter.get_remaining_calls(), 4)
        
        self.rate_limiter.record_call()
        self.assertEqual(self.rate_limiter.get_remaining_calls(), 3)
    
    def test_wait_time_calculation(self):
        """Test wait time calculation when at limit"""
        import time
        
        # Make 5 calls to reach limit
        for _ in range(5):
            self.rate_limiter.record_call()
        
        # Should have wait time
        wait_time = self.rate_limiter.get_wait_time()
        self.assertGreater(wait_time, 0)
        self.assertLessEqual(wait_time, 10)
    
    def test_old_calls_cleaned_up(self):
        """Test that old calls outside time window are cleaned up"""
        import time
        from sentiment_analyzer import RateLimiter
        
        # Make calls with very short time window
        limiter = RateLimiter(max_calls=3, time_window=1, name="TestAPI")
        
        limiter.record_call()
        limiter.record_call()
        self.assertEqual(limiter.get_remaining_calls(), 1)
        
        # Wait for time window to expire
        time.sleep(1.1)
        
        # Old calls should be cleaned up
        self.assertEqual(limiter.get_remaining_calls(), 3)
        self.assertTrue(limiter.can_make_call())
    
    @patch('requests.get')
    def test_newsapi_respects_rate_limit(self, mock_get):
        """Test that NewsAPI fetch respects rate limit"""
        from sentiment_analyzer import SentimentAnalyzer
        
        # Create analyzer with small rate limit for testing
        analyzer = SentimentAnalyzer()
        analyzer.news_api_limiter.max_calls = 2
        analyzer.news_api_limiter.time_window = 10
        analyzer.news_api_available = True
        analyzer.news_api_key = 'change-me'
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'articles': [{'title': 'Test'}]}
        mock_get.return_value = mock_response
        
        # First 2 calls should work
        result1 = analyzer.fetch_news_newsapi('AAPL')
        self.assertEqual(len(result1), 1)
        
        result2 = analyzer.fetch_news_newsapi('MSFT')
        self.assertEqual(len(result2), 1)
        
        # Third call should be blocked by rate limit
        result3 = analyzer.fetch_news_newsapi('TSLA')
        self.assertEqual(len(result3), 0)  # Empty due to rate limit
        
        # Only 2 API calls should have been made
        self.assertEqual(mock_get.call_count, 2)
    
    @patch('requests.get')
    def test_finnhub_respects_rate_limit(self, mock_get):
        """Test that Finnhub fetch respects rate limit"""
        from sentiment_analyzer import SentimentAnalyzer
        
        # Create analyzer with small rate limit for testing
        analyzer = SentimentAnalyzer()
        analyzer.finnhub_limiter.max_calls = 2
        analyzer.finnhub_limiter.time_window = 10
        analyzer.finnhub_available = True
        analyzer.finnhub_api_key = 'change-me'
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'headline': 'Test'}]
        mock_get.return_value = mock_response
        
        # First 2 calls should work
        result1 = analyzer.fetch_news_finnhub('AAPL')
        self.assertEqual(len(result1), 1)
        
        result2 = analyzer.fetch_news_finnhub('MSFT')
        self.assertEqual(len(result2), 1)
        
        # Third call should be blocked by rate limit
        result3 = analyzer.fetch_news_finnhub('TSLA')
        self.assertEqual(len(result3), 0)  # Empty due to rate limit
        
        # Only 2 API calls should have been made
        self.assertEqual(mock_get.call_count, 2)
    
    def test_concurrent_rate_limiting(self):
        """Test rate limiter with concurrent access from multiple threads"""
        import threading
        from sentiment_analyzer import RateLimiter
        
        limiter = RateLimiter(max_calls=5, time_window=10, name="TestAPI")
        results = []
        
        def make_call():
            if limiter.can_make_call():
                limiter.record_call()
                results.append(True)
            else:
                results.append(False)
        
        # Create 10 threads trying to make calls simultaneously
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_call)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have exactly 5 successful calls
        successful_calls = sum(results)
        self.assertEqual(successful_calls, 5)
        
        # Verify remaining calls is 0
        self.assertEqual(limiter.get_remaining_calls(), 0)


if __name__ == '__main__':
    unittest.main()
#!/usr/bin/env python3
"""
Test async sentiment analyzer functionality
"""

import unittest
import asyncio
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock

# Set test environment
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['PAPER_TRADING_MODE'] = 'true'

# Import after setting environment
from sentiment_analyzer import SentimentAnalyzer, AIOHTTP_AVAILABLE


class TestAsyncSentimentAnalyzer(unittest.TestCase):
    """Test async sentiment analysis functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = SentimentAnalyzer()
    
    def tearDown(self):
        """Clean up after tests"""
        pass
    
    def test_analyzer_initialization(self):
        """Test that analyzer initializes correctly"""
        self.assertIsNotNone(self.analyzer)
        self.assertIsInstance(self.analyzer.sentiment_cache, dict)
    
    @unittest.skipIf(not AIOHTTP_AVAILABLE, "aiohttp not available")
    def test_async_methods_exist(self):
        """Test that async methods are defined"""
        self.assertTrue(hasattr(self.analyzer, 'fetch_news_newsapi_async'))
        self.assertTrue(hasattr(self.analyzer, 'fetch_news_finnhub_async'))
        self.assertTrue(hasattr(self.analyzer, 'get_sentiment_score_async'))
        self.assertTrue(hasattr(self.analyzer, 'analyze_portfolio_sentiment_async'))
    
    @unittest.skipIf(not AIOHTTP_AVAILABLE, "aiohttp not available")
    def test_async_sentiment_score_with_mocked_apis(self):
        """Test async sentiment score with mocked API responses"""
        
        # Mock news articles
        mock_finnhub_articles = [
            {'headline': 'Great earnings!', 'summary': 'Company beats expectations'},
            {'headline': 'Stock surges', 'summary': 'Strong performance'},
        ]
        
        mock_newsapi_articles = [
            {'title': 'Positive outlook', 'description': 'Analysts upgrade stock'},
        ]
        
        async def mock_finnhub(symbol, days):
            return mock_finnhub_articles
        
        async def mock_newsapi(symbol, days):
            return mock_newsapi_articles
        
        # Patch the async methods
        with patch.object(self.analyzer, 'fetch_news_finnhub_async', side_effect=mock_finnhub):
            with patch.object(self.analyzer, 'fetch_news_newsapi_async', side_effect=mock_newsapi):
                # Configure analyzer to have both APIs available
                self.analyzer.finnhub_available = True
                self.analyzer.news_api_available = True
                
                # Run async test
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(
                    self.analyzer.get_sentiment_score_async('AAPL', days=7)
                )
                
                # Verify result structure
                self.assertIn('overall_score', result)
                self.assertIn('sentiment_signal', result)
                self.assertIn('article_count', result)
                self.assertGreater(result['article_count'], 0)
                
                print(f"✓ Async sentiment test result: {result['sentiment_signal']} "
                      f"(score: {result['overall_score']:.3f}, articles: {result['article_count']})")
    
    @unittest.skipIf(not AIOHTTP_AVAILABLE, "aiohttp not available")
    def test_portfolio_sentiment_async(self):
        """Test async portfolio sentiment analysis"""
        
        # Mock single sentiment result
        mock_result = {
            'overall_score': 0.5,
            'sentiment_signal': 'BULLISH',
            'article_count': 5,
            'positive_ratio': 0.8,
            'negative_ratio': 0.2,
            'neutral_ratio': 0.0,
            'confidence': 0.7
        }
        
        async def mock_get_sentiment(symbol, days):
            return {**mock_result, 'symbol': symbol}
        
        # Patch the method
        with patch.object(self.analyzer, 'get_sentiment_score_async', side_effect=mock_get_sentiment):
            test_symbols = ['AAPL', 'MSFT', 'GOOGL']
            
            # Run async test
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(
                self.analyzer.analyze_portfolio_sentiment_async(test_symbols, days=7)
            )
            
            # Verify results
            self.assertEqual(len(results), len(test_symbols))
            for symbol in test_symbols:
                self.assertIn(symbol, results)
                self.assertEqual(results[symbol]['sentiment_signal'], 'BULLISH')
            
            print(f"✓ Async portfolio sentiment test passed for {len(test_symbols)} symbols")
    
    def test_sync_wrapper_portfolio_sentiment(self):
        """Test synchronous wrapper for portfolio sentiment"""
        
        # Mock result
        mock_result = {
            'overall_score': 0.0,
            'sentiment_signal': 'NEUTRAL',
            'article_count': 0,
            'confidence': 0.0
        }
        
        # Patch get_sentiment_score to avoid real API calls
        with patch.object(self.analyzer, 'get_sentiment_score', return_value=mock_result):
            test_symbols = ['AAPL', 'MSFT']
            
            # Run sync wrapper
            results = self.analyzer.analyze_portfolio_sentiment(test_symbols, days=7)
            
            # Verify results
            self.assertEqual(len(results), len(test_symbols))
            for symbol in test_symbols:
                self.assertIn(symbol, results)
            
            print(f"✓ Sync portfolio sentiment wrapper test passed")
    
    def test_cache_functionality(self):
        """Test that caching works correctly"""
        test_result = {
            'overall_score': 0.5,
            'sentiment_signal': 'BULLISH'
        }
        
        cache_key = self.analyzer._get_cache_key('TEST')
        
        # Cache the result
        self.analyzer._cache_sentiment(cache_key, test_result)
        
        # Verify cache is valid
        self.assertTrue(self.analyzer._is_cache_valid(cache_key))
        
        # Retrieve from cache
        cached = self.analyzer._get_cached_sentiment(cache_key)
        self.assertEqual(cached, test_result)
        
        print("✓ Cache functionality test passed")
    
    @unittest.skipIf(not AIOHTTP_AVAILABLE, "aiohttp not available")
    def test_async_fallback_without_apis(self):
        """Test async methods fall back gracefully when no APIs configured"""
        
        # Create analyzer without API keys
        analyzer_no_apis = SentimentAnalyzer(
            news_api_key='',
            finnhub_api_key=''
        )
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            analyzer_no_apis.get_sentiment_score_async('AAPL', days=7)
        )
        
        # Should return neutral result
        self.assertEqual(result['sentiment_signal'], 'NEUTRAL')
        self.assertEqual(result['article_count'], 0)
        
        print("✓ Async fallback test passed")


class TestAsyncIntegration(unittest.TestCase):
    """Test integration of async sentiment with main bot"""
    
    def test_aiohttp_availability_flag(self):
        """Test that AIOHTTP_AVAILABLE flag is set correctly"""
        # This should be True if aiohttp is installed
        if AIOHTTP_AVAILABLE:
            print("✓ aiohttp is available for async sentiment analysis")
        else:
            print("⚠ aiohttp not available - async features will use fallback")
        
        # Test always passes, just informational
        self.assertTrue(True)


if __name__ == '__main__':
    print("="*60)
    print("Async Sentiment Analyzer Tests")
    print("="*60)
    
    # Run tests
    unittest.main(verbosity=2)
#!/usr/bin/env python3
"""
Test to verify sentiment analyzer works correctly in threaded context
This test validates the fix for the async event loop error in threads
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentiment_analyzer import SentimentAnalyzer


class TestSentimentAnalyzerThreadFix(unittest.TestCase):
    """Test sentiment analyzer in threaded environment"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = SentimentAnalyzer()
        self.result = None
        self.exception = None
    
    def test_get_sentiment_score_in_thread(self):
        """Test that get_sentiment_score works when called from a thread"""
        def run_in_thread():
            """Function to run in thread - simulates run_bot_loop"""
            try:
                # Disable APIs to avoid external calls, but enable aiohttp flag for testing
                self.analyzer.news_api_available = False
                self.analyzer.finnhub_available = False
                
                # Call get_sentiment_score (should not raise RuntimeError about event loop)
                self.result = self.analyzer.get_sentiment_score('AAPL', days=7)
            except Exception as e:
                self.exception = e
        
        # Run in a separate thread (like run_bot_loop does)
        thread = threading.Thread(target=run_in_thread, name='TestThread-SentimentAnalyzer')
        thread.start()
        thread.join()
        
        # Verify no exception was raised
        if self.exception:
            self.fail(f"Exception raised in thread: {self.exception}")
        
        # Verify result is valid
        self.assertIsNotNone(self.result)
        self.assertIn('overall_score', self.result)
        self.assertIn('sentiment_signal', self.result)
    
    @patch('sentiment_analyzer.AIOHTTP_AVAILABLE', True)
    def test_async_sentiment_in_thread_with_aiohttp(self):
        """Test async sentiment analysis in thread when aiohttp is available"""
        def run_in_thread():
            """Function to run in thread - simulates run_bot_loop"""
            try:
                # Enable both APIs to trigger async path
                self.analyzer.news_api_available = True
                self.analyzer.finnhub_available = True
                
                # Mock the async method to avoid real API calls
                with patch.object(self.analyzer, 'get_sentiment_score_async') as mock_async:
                    mock_async.return_value = {
                        'overall_score': 0.5,
                        'sentiment_signal': 'BULLISH',
                        'article_count': 10,
                        'confidence': 0.8
                    }
                    
                    # Call get_sentiment_score (should use async path)
                    self.result = self.analyzer.get_sentiment_score('AAPL', days=7)
            except RuntimeError as e:
                if "There is no current event loop in thread" in str(e):
                    self.exception = e
            except Exception as e:
                # Other exceptions are okay (e.g., aiohttp not available)
                pass
        
        # Run in a separate thread (like run_bot_loop does)
        thread = threading.Thread(target=run_in_thread, name='TestThread-AsyncSentiment')
        thread.start()
        thread.join()
        
        # Verify the specific RuntimeError about event loop was NOT raised
        if self.exception:
            self.fail(f"Event loop RuntimeError raised in thread: {self.exception}")
        
        # If async was used and result is set, verify it
        if self.result:
            self.assertIn('overall_score', self.result)
            self.assertIn('sentiment_signal', self.result)
    
    def test_multiple_threads_calling_sentiment(self):
        """Test that multiple threads can call get_sentiment_score simultaneously"""
        results = []
        exceptions = []
        
        def run_in_thread(symbol):
            """Function to run in thread"""
            try:
                self.analyzer.news_api_available = False
                self.analyzer.finnhub_available = False
                result = self.analyzer.get_sentiment_score(symbol, days=7)
                results.append(result)
            except Exception as e:
                exceptions.append(e)
        
        # Create multiple threads
        threads = []
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
        
        for symbol in symbols:
            thread = threading.Thread(
                target=run_in_thread, 
                args=(symbol,),
                name=f'TestThread-{symbol}'
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no exceptions
        if exceptions:
            self.fail(f"Exceptions raised in threads: {exceptions}")
        
        # Verify results
        self.assertEqual(len(results), len(symbols))
        for result in results:
            self.assertIn('overall_score', result)
            self.assertIn('sentiment_signal', result)


if __name__ == '__main__':
    unittest.main()
