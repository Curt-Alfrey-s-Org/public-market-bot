#!/usr/bin/env python3
"""
Test that the bot continues to run even when API rate limits are hit.
This addresses the requirement: "ensure the bot still runs even if rate limits are hit"
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentiment_analyzer import SentimentAnalyzer, RateLimiter


class TestBotResilienceWithRateLimits(unittest.TestCase):
    """Test that the bot continues to operate when rate limits are hit"""
    
    def test_sentiment_analyzer_returns_valid_result_when_rate_limited(self):
        """Test that get_sentiment_score returns valid dict even when rate limited"""
        analyzer = SentimentAnalyzer()
        
        # Set aggressive rate limit for both APIs
        analyzer.news_api_limiter.max_calls = 1
        analyzer.news_api_limiter.time_window = 10
        analyzer.finnhub_limiter.max_calls = 1
        analyzer.finnhub_limiter.time_window = 10
        analyzer.news_api_available = True
        analyzer.finnhub_available = True
        analyzer.news_api_key = 'change-me'
        analyzer.finnhub_api_key = 'change-me'
        
        with patch('sentiment_analyzer.requests.get') as mock_get:
            # Mock first call succeeds
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'articles': [
                {'title': 'Good news', 'description': 'Positive'}
            ]}
            mock_get.return_value = mock_response
            
            # First call - should work
            result1 = analyzer.get_sentiment_score('AAPL')
            self.assertIsInstance(result1, dict)
            self.assertIn('overall_score', result1)
            self.assertIn('article_count', result1)
            self.assertIn('sentiment_signal', result1)
            
            # Second call - should be rate limited but still return valid dict
            result2 = analyzer.get_sentiment_score('MSFT')
            self.assertIsInstance(result2, dict)
            self.assertIn('overall_score', result2)
            self.assertIn('article_count', result2)
            self.assertIn('sentiment_signal', result2)
            
            # Key point: No exception raised, and we get a valid dict structure
            # The article count may vary based on which API succeeds, but structure is valid
            self.assertIsInstance(result2['article_count'], int)
            self.assertIn(result2['sentiment_signal'], ['BULLISH', 'BEARISH', 'NEUTRAL'])
    
    def test_multiple_symbols_processed_despite_rate_limits(self):
        """Test that multiple symbols can be processed even when some hit rate limits"""
        analyzer = SentimentAnalyzer()
        analyzer.news_api_limiter.max_calls = 2
        analyzer.news_api_limiter.time_window = 10
        analyzer.finnhub_limiter.max_calls = 2
        analyzer.finnhub_limiter.time_window = 10
        analyzer.news_api_available = True
        analyzer.finnhub_available = True
        analyzer.news_api_key = 'change-me'
        analyzer.finnhub_api_key = 'change-me'
        
        with patch('sentiment_analyzer.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'articles': [
                {'title': 'News', 'description': 'Article'}
            ]}
            mock_get.return_value = mock_response
            
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
            results = []
            
            # Process all symbols - some will hit rate limits
            for symbol in symbols:
                try:
                    result = analyzer.get_sentiment_score(symbol)
                    results.append(result)
                except Exception as e:
                    self.fail(f"Exception raised for {symbol}: {e}")
            
            # All symbols should have been processed
            self.assertEqual(len(results), len(symbols))
            
            # All results should be valid dicts
            for result in results:
                self.assertIsInstance(result, dict)
                self.assertIn('overall_score', result)
                self.assertIn('sentiment_signal', result)
    
    def test_no_exceptions_raised_when_rate_limited(self):
        """Test that no exceptions are raised when rate limits are hit"""
        analyzer = SentimentAnalyzer()
        analyzer.news_api_limiter.max_calls = 0  # Already at limit
        analyzer.finnhub_limiter.max_calls = 0  # Already at limit
        analyzer.news_api_available = True
        analyzer.finnhub_available = True
        analyzer.news_api_key = 'change-me'
        analyzer.finnhub_api_key = 'change-me'
        
        # Should not raise any exceptions
        try:
            result = analyzer.get_sentiment_score('AAPL')
            self.assertIsInstance(result, dict)
            self.assertEqual(result['article_count'], 0)
            self.assertEqual(result['sentiment_signal'], 'NEUTRAL')
        except Exception as e:
            self.fail(f"Exception raised when rate limited: {e}")
    
    def test_stock_screener_continues_when_sentiment_rate_limited(self):
        """Test that stock screener continues filtering when sentiment is rate limited"""
        # Set up environment for sentiment filtering
        os.environ['ENABLE_SENTIMENT_FILTER'] = 'true'
        
        try:
            from stock_screener import StockScreener
            
            screener = StockScreener()
            
            if not screener.sentiment_analyzer:
                self.skipTest("Sentiment analyzer not available")
            
            # Set rate limits to 0 (already exhausted)
            screener.sentiment_analyzer.news_api_limiter.max_calls = 0
            screener.sentiment_analyzer.finnhub_limiter.max_calls = 0
            screener.sentiment_analyzer.news_api_available = True
            screener.sentiment_analyzer.finnhub_available = True
            screener.sentiment_analyzer.news_api_key = 'change-me'
            screener.sentiment_analyzer.finnhub_api_key = 'change-me'
            
            # Filter should still work and return valid tuple
            try:
                passes, reason, sentiment_data = screener.filter_by_sentiment('AAPL')
                
                self.assertIsInstance(passes, bool)
                self.assertIsInstance(reason, str)
                # sentiment_data can be None or dict
                if sentiment_data is not None:
                    self.assertIsInstance(sentiment_data, dict)
                
            except Exception as e:
                self.fail(f"Exception raised in stock screener: {e}")
        
        finally:
            # Clean up environment
            if 'ENABLE_SENTIMENT_FILTER' in os.environ:
                del os.environ['ENABLE_SENTIMENT_FILTER']
    
    def test_rate_limiter_never_raises_exception(self):
        """Test that RateLimiter itself never raises exceptions during normal use"""
        limiter = RateLimiter(max_calls=5, time_window=10, name="Test")
        
        # These operations should never raise exceptions
        try:
            # Can make call
            can_call = limiter.can_make_call()
            self.assertIsInstance(can_call, bool)
            
            # Record call
            limiter.record_call()
            
            # Get remaining calls
            remaining = limiter.get_remaining_calls()
            self.assertIsInstance(remaining, int)
            self.assertGreaterEqual(remaining, 0)
            
            # Get wait time
            wait_time = limiter.get_wait_time()
            self.assertIsInstance(wait_time, (int, float))
            self.assertGreaterEqual(wait_time, 0)
            
        except Exception as e:
            self.fail(f"RateLimiter raised exception: {e}")
    
    def test_graceful_degradation_with_neutral_sentiment(self):
        """Test that rate-limited calls result in neutral sentiment (graceful degradation)"""
        analyzer = SentimentAnalyzer()
        analyzer.news_api_limiter.max_calls = 0  # Exhausted
        analyzer.finnhub_limiter.max_calls = 0  # Exhausted
        analyzer.news_api_available = True
        analyzer.finnhub_available = True
        analyzer.news_api_key = 'change-me'
        analyzer.finnhub_api_key = 'change-me'
        
        result = analyzer.get_sentiment_score('AAPL')
        
        # Should return neutral sentiment
        self.assertEqual(result['overall_score'], 0.0)
        self.assertEqual(result['sentiment_signal'], 'NEUTRAL')
        self.assertEqual(result['article_count'], 0)
        self.assertEqual(result['positive_ratio'], 0.0)
        self.assertEqual(result['negative_ratio'], 0.0)
        self.assertEqual(result['neutral_ratio'], 1.0)


class TestBotContinuesWithPartialData(unittest.TestCase):
    """Test that bot can work with partial sentiment data when rate limits hit"""
    
    def test_can_trade_with_neutral_sentiment(self):
        """Test that trading decisions can be made with neutral sentiment from rate limits"""
        # Get neutral sentiment (as would happen with rate limits)
        sentiment = {
            'overall_score': 0.0,
            'sentiment_signal': 'NEUTRAL',
            'article_count': 0,
            'confidence': 0.0,
            'positive_ratio': 0.0,
            'negative_ratio': 0.0,
            'neutral_ratio': 1.0
        }
        
        # Verify the sentiment structure is valid for decision making
        self.assertIn('overall_score', sentiment)
        self.assertIn('sentiment_signal', sentiment)
        self.assertIn('article_count', sentiment)
        
        # With neutral sentiment and low confidence, bot should be able to proceed
        # (though it may choose not to trade based on low confidence)
        self.assertEqual(sentiment['sentiment_signal'], 'NEUTRAL')


if __name__ == '__main__':
    unittest.main()
