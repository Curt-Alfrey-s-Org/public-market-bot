#!/usr/bin/env python3
"""
Test script to verify environment variable decryption works correctly
"""

import unittest
import os
import sys
from cryptography.fernet import Fernet

# Test environment setup
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'


class TestEnvironmentDecryption(unittest.TestCase):
    """Test that encrypted environment variables can be decrypted correctly"""
    
    def setUp(self):
        """Set up test encryption key"""
        # Generate a test encryption key
        self.test_key = Fernet.generate_key()
        os.environ['MP5_ENCRYPTION_KEY'] = self.test_key.decode('utf-8')
        
        # Store original env values
        self.original_news_key = os.environ.get('NEWS_API_KEY')
        self.original_schwab_key = os.environ.get('SCHWAB_API_KEY')
    
    def tearDown(self):
        """Restore original environment"""
        if 'MP5_ENCRYPTION_KEY' in os.environ:
            del os.environ['MP5_ENCRYPTION_KEY']
        
        if self.original_news_key:
            os.environ['NEWS_API_KEY'] = self.original_news_key
        elif 'NEWS_API_KEY' in os.environ:
            del os.environ['NEWS_API_KEY']
        
        if self.original_schwab_key:
            os.environ['SCHWAB_API_KEY'] = self.original_schwab_key
        elif 'SCHWAB_API_KEY' in os.environ:
            del os.environ['SCHWAB_API_KEY']
    
    def test_decrypt_plain_value(self):
        """Test that plain (non-encrypted) values are returned as-is"""
        from main import get_decrypted_env
        
        # Set a plain value
        test_value = "news_test_key_12345"
        os.environ['NEWS_API_KEY'] = test_value
        
        # Should return the value unchanged
        result = get_decrypted_env('NEWS_API_KEY', '')
        self.assertEqual(result, test_value)
    
    def test_decrypt_encrypted_value(self):
        """Test that encrypted values are decrypted correctly"""
        from main import get_decrypted_env
        
        # Create an encrypted value
        fernet = Fernet(self.test_key)
        plain_value = "news_test_key_12345"
        encrypted_bytes = fernet.encrypt(plain_value.encode('utf-8'))
        encrypted_value = "enc:" + encrypted_bytes.decode('utf-8')
        
        # Set the encrypted value in environment
        os.environ['NEWS_API_KEY'] = encrypted_value
        
        # Should decrypt and return the original value
        result = get_decrypted_env('NEWS_API_KEY', '')
        self.assertEqual(result, plain_value)
    
    def test_decrypt_empty_value(self):
        """Test that empty values are handled correctly"""
        from main import get_decrypted_env
        
        os.environ['NEWS_API_KEY'] = ''
        result = get_decrypted_env('NEWS_API_KEY', 'default')
        self.assertEqual(result, '')
    
    def test_decrypt_missing_key(self):
        """Test that missing keys return the default value"""
        from main import get_decrypted_env
        
        if 'NEWS_API_KEY' in os.environ:
            del os.environ['NEWS_API_KEY']
        
        result = get_decrypted_env('NEWS_API_KEY', 'default_value')
        self.assertEqual(result, 'default_value')
    
    def test_decrypt_schwab_credentials(self):
        """Test that Schwab credentials can be decrypted"""
        from main import get_decrypted_env
        
        # Create encrypted credentials
        fernet = Fernet(self.test_key)
        plain_api_key = "change-me"
        plain_secret = "change-me"
        
        encrypted_api_key = "change-me" + fernet.encrypt(plain_api_key.encode('utf-8')).decode('utf-8')
        encrypted_secret = "change-me" + fernet.encrypt(plain_secret.encode('utf-8')).decode('utf-8')
        
        os.environ['SCHWAB_API_KEY'] = encrypted_api_key
        os.environ['SCHWAB_APP_SECRET'] = encrypted_secret
        
        # Should decrypt both values
        api_key = get_decrypted_env('SCHWAB_API_KEY', '')
        secret = get_decrypted_env('SCHWAB_APP_SECRET', '')
        
        self.assertEqual(api_key, plain_api_key)
        self.assertEqual(secret, plain_secret)
    
    def test_ml_param_optimizer_decryption(self):
        """Test that ml_param_optimizer decryption functions work"""
        from ml_param_optimizer import get_decrypted_env
        
        # Create an encrypted value
        fernet = Fernet(self.test_key)
        plain_value = "news_test_key_67890"
        encrypted_bytes = fernet.encrypt(plain_value.encode('utf-8'))
        encrypted_value = "enc:" + encrypted_bytes.decode('utf-8')
        
        os.environ['NEWS_API_KEY'] = encrypted_value
        
        # Should decrypt correctly in ml_param_optimizer module too
        result = get_decrypted_env('NEWS_API_KEY', '')
        self.assertEqual(result, plain_value)
    
    def test_schwab_auth_decryption(self):
        """Test that schwab_auth decryption functions work"""
        from schwab_auth import get_decrypted_env
        
        # Create encrypted credentials
        fernet = Fernet(self.test_key)
        plain_api_key = "change-me"
        encrypted_api_key = "change-me" + fernet.encrypt(plain_api_key.encode('utf-8')).decode('utf-8')
        
        os.environ['SCHWAB_API_KEY'] = encrypted_api_key
        
        # Should decrypt correctly in schwab_auth module
        result = get_decrypted_env('SCHWAB_API_KEY', '')
        self.assertEqual(result, plain_api_key)
    
    def test_sentiment_analyzer_decryption(self):
        """Test that sentiment_analyzer decryption functions work"""
        from sentiment_analyzer import get_decrypted_env
        
        # Create encrypted API keys
        fernet = Fernet(self.test_key)
        plain_news_key = "news_api_test_key"
        plain_finnhub_key = "finnhub_test_key"
        
        encrypted_news = "enc:" + fernet.encrypt(plain_news_key.encode('utf-8')).decode('utf-8')
        encrypted_finnhub = "enc:" + fernet.encrypt(plain_finnhub_key.encode('utf-8')).decode('utf-8')
        
        os.environ['NEWS_API_KEY'] = encrypted_news
        os.environ['FINNHUB_API_KEY'] = encrypted_finnhub
        
        # Should decrypt correctly
        news_key = get_decrypted_env('NEWS_API_KEY', '')
        finnhub_key = get_decrypted_env('FINNHUB_API_KEY', '')
        
        self.assertEqual(news_key, plain_news_key)
        self.assertEqual(finnhub_key, plain_finnhub_key)
    
    def test_data_fetcher_decryption(self):
        """Test that data_fetcher decryption functions work"""
        from data_fetcher import get_decrypted_env
        
        # Create encrypted API key
        fernet = Fernet(self.test_key)
        plain_av_key = "alphavantage_test_key"
        encrypted_av = "enc:" + fernet.encrypt(plain_av_key.encode('utf-8')).decode('utf-8')
        
        os.environ['ALPHA_VANTAGE_API_KEY'] = encrypted_av
        
        # Should decrypt correctly
        av_key = get_decrypted_env('ALPHA_VANTAGE_API_KEY', '')
        self.assertEqual(av_key, plain_av_key)


def run_tests():
    """Run the test suite"""
    print("=" * 70)
    print("ENVIRONMENT VARIABLE DECRYPTION TEST")
    print("=" * 70)
    print()
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEnvironmentDecryption)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✓ All decryption tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
