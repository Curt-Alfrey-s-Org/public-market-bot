#!/usr/bin/env python3
"""
Test to verify debug log fixes for sentiment analyzer
Verifies that:
1. API 401 errors are logged at DEBUG level instead of ERROR
2. "No news articles found" is logged at DEBUG level instead of WARNING
"""

import unittest
from unittest.mock import Mock, patch
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentiment_analyzer import SentimentAnalyzer


class TestDebugLogFixes(unittest.TestCase):
    """Test that log levels are appropriate for different scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Explicitly pass API keys so SentimentAnalyzer reliably exercises HTTP paths
        self.analyzer = SentimentAnalyzer(
            news_api_key='change-me',
            finnhub_api_key='change-me',
        )
    
    @patch('sentiment_analyzer.requests.get')
    def test_401_error_logs_at_debug_newsapi(self, mock_get):
        """Test that NewsAPI 401 errors are logged at DEBUG level, not ERROR"""
        # Mock a 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = '{"status":"error","code":"apiKeyInvalid","message":"Your API key is invalid"}'
        mock_get.return_value = mock_response
        
        # Capture logs and verify 401 is logged at DEBUG level
        with self.assertLogs('sentiment_analyzer', level='DEBUG') as log_context:
            result = self.analyzer.fetch_news_newsapi('AAPL')
            
            # Should return empty list
            self.assertEqual(result, [])
            
            # Check log records for 401 error
            debug_401_logs = [rec for rec in log_context.records 
                            if rec.levelname == 'DEBUG' and '401' in rec.getMessage()]
            error_401_logs = [rec for rec in log_context.records 
                            if rec.levelname == 'ERROR' and '401' in rec.getMessage()]
            
            # Should have DEBUG log for 401, not ERROR
            self.assertGreater(len(debug_401_logs), 0, 
                             "Expected DEBUG log for 401 error")
            self.assertEqual(len(error_401_logs), 0, 
                           "Should not have ERROR log for 401 error")
    
    @patch('sentiment_analyzer.requests.get')
    def test_401_error_logs_at_debug_finnhub(self, mock_get):
        """Test that Finnhub 401 errors are logged at DEBUG level, not ERROR"""
        # Mock a 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = '{"error":"Invalid API key"}'
        mock_get.return_value = mock_response
        
        # Capture logs and verify 401 is logged at DEBUG level
        with self.assertLogs('sentiment_analyzer', level='DEBUG') as log_context:
            result = self.analyzer.fetch_news_finnhub('AAPL')
            
            # Should return empty list
            self.assertEqual(result, [])
            
            # Check log records for 401 error
            debug_401_logs = [rec for rec in log_context.records 
                            if rec.levelname == 'DEBUG' and '401' in rec.getMessage()]
            error_401_logs = [rec for rec in log_context.records 
                            if rec.levelname == 'ERROR' and '401' in rec.getMessage()]
            
            # Should have DEBUG log for 401, not ERROR
            self.assertGreater(len(debug_401_logs), 0, 
                             "Expected DEBUG log for 401 error")
            self.assertEqual(len(error_401_logs), 0, 
                           "Should not have ERROR log for 401 error")
    
    @patch('sentiment_analyzer.requests.get')
    def test_non_401_errors_still_log_at_error_level(self, mock_get):
        """Test that non-401 errors are still logged at ERROR level"""
        # Mock a 500 response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = '{"error":"Internal server error"}'
        mock_get.return_value = mock_response
        
        # Capture logs and verify 500 is logged at ERROR level
        with self.assertLogs('sentiment_analyzer', level='DEBUG') as log_context:
            result = self.analyzer.fetch_news_newsapi('AAPL')
            
            # Should return empty list
            self.assertEqual(result, [])
            
            # Check log records for 500 error
            error_500_logs = [rec for rec in log_context.records 
                            if rec.levelname == 'ERROR' and '500' in rec.getMessage()]
            
            # Should have ERROR log for 500
            self.assertGreater(len(error_500_logs), 0, 
                             "Expected ERROR log for 500 error")
    
    @patch('sentiment_analyzer.requests.get')
    def test_no_news_logs_at_debug_level(self, mock_get):
        """Test that 'No news articles found' is logged at DEBUG level, not WARNING"""
        # Mock a successful but empty response (for both NewsAPI and Finnhub)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []  # Finnhub returns list directly
        mock_get.return_value = mock_response
        
        # Capture logs and verify "No news" is logged at DEBUG level
        with self.assertLogs('sentiment_analyzer', level='DEBUG') as log_context:
            result = self.analyzer.get_sentiment_score('AAPL')
            
            # Should return neutral sentiment
            self.assertEqual(result['sentiment_signal'], 'NEUTRAL')
            self.assertEqual(result['article_count'], 0)
            self.assertEqual(result['overall_score'], 0.0)
            
            # Check log records for "No news articles found"
            no_news_logs = [rec for rec in log_context.records 
                          if 'No news articles found' in rec.getMessage()]
            
            # Should have at least one log for "no news"
            self.assertGreater(len(no_news_logs), 0, 
                             "Expected log message for 'No news articles found'")
            
            # All "no news" logs should be at DEBUG level, not WARNING
            for log_rec in no_news_logs:
                self.assertEqual(log_rec.levelname, 'DEBUG', 
                               f"Expected DEBUG level for 'No news articles found', "
                               f"got {log_rec.levelname}")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)

