#!/usr/bin/env python3
"""
Test suite for token encryption and security enhancements
Tests token encryption, HMAC integrity checks, and log masking
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from cryptography.fernet import Fernet

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set test environment
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'


class TestTokenEncryption(unittest.TestCase):
    """Test token encryption and decryption"""
    
    def setUp(self):
        """Set up test environment"""
        # Generate a test encryption key
        self.test_key = Fernet.generate_key()
        os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY'] = self.test_key.decode('utf-8')
        
        # Create temporary token file
        self.temp_fd, self.temp_token_path = tempfile.mkstemp(suffix='.json')
        os.close(self.temp_fd)
        
    def tearDown(self):
        """Clean up test environment"""
        if 'SCHWAB_TOKEN_ENCRYPTION_KEY' in os.environ:
            del os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY']
        if os.path.exists(self.temp_token_path):
            os.remove(self.temp_token_path)
    
    def test_encryption_key_retrieval(self):
        """Test that encryption key can be retrieved from environment"""
        from schwab_auth import _get_token_encryption_key
        
        key = _get_token_encryption_key()
        self.assertIsNotNone(key)
        self.assertEqual(key, self.test_key)
        print("✓ Encryption key retrieved successfully from environment")
    
    def test_encryption_key_from_file(self):
        """Test that encryption key can be retrieved from .token.key file"""
        from schwab_auth import _get_token_encryption_key
        
        # Remove environment variable
        del os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY']
        
        # Create .token.key file
        key_file = '.token.key'
        try:
            with open(key_file, 'wb') as f:
                f.write(self.test_key)
            
            key = _get_token_encryption_key()
            self.assertIsNotNone(key)
            self.assertEqual(key, self.test_key)
            print("✓ Encryption key retrieved successfully from .token.key file")
        finally:
            if os.path.exists(key_file):
                os.remove(key_file)
    
    def test_mask_sensitive_value(self):
        """Test that sensitive values are masked properly"""
        from schwab_auth import _mask_sensitive_value
        
        # Test with URL
        url = "https://127.0.0.1:8182/callback"
        masked = _mask_sensitive_value(url, show_chars=8)
        self.assertTrue(masked.startswith("*"))
        self.assertTrue(masked.endswith("callback"))  # Shows last 8 chars
        self.assertNotEqual(masked, url)
        print(f"✓ URL masked: {url} -> {masked}")
        
        # Test with short value
        short = "abc"
        masked_short = _mask_sensitive_value(short, show_chars=4)
        self.assertEqual(masked_short, "***")
        print(f"✓ Short value masked: {short} -> {masked_short}")
        
        # Test with empty value
        empty = ""
        masked_empty = _mask_sensitive_value(empty)
        self.assertEqual(masked_empty, "***")
        print("✓ Empty value masked correctly")
    
    @patch('schwab_auth.SCHWAB_PY_AVAILABLE', True)
    @patch('schwab_auth.auth')
    def test_token_save_encrypted(self, mock_auth):
        """Test that tokens are saved encrypted with HMAC"""
        from schwab_auth import SchwabAuthenticator
        
        # Create authenticator instance
        auth_obj = SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
            token_path=self.temp_token_path,
            encrypt_token=True
        )
        
        # Create test token data
        test_token = {
            "access_token": "change-me",
            "refresh_token": "change-me",
            "expires_at": 1234567890
        }
        
        # Save encrypted token
        auth_obj._save_encrypted_token(test_token)
        
        # Verify file exists and is encrypted
        self.assertTrue(os.path.exists(self.temp_token_path))
        
        with open(self.temp_token_path, 'r') as f:
            saved_data = json.load(f)
        
        # Verify it's encrypted format
        self.assertIn('encrypted', saved_data)
        self.assertTrue(saved_data['encrypted'])
        self.assertIn('hmac', saved_data)
        self.assertIn('data', saved_data)
        
        # Verify the data is not plain text
        self.assertNotIn('access_token', str(saved_data['data']))
        
        print("✓ Token saved in encrypted format with HMAC")
    
    @patch('schwab_auth.SCHWAB_PY_AVAILABLE', True)
    @patch('schwab_auth.auth')
    def test_token_load_encrypted(self, mock_auth):
        """Test that encrypted tokens can be loaded and decrypted"""
        from schwab_auth import SchwabAuthenticator
        
        # Create authenticator
        auth_obj = SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
            token_path=self.temp_token_path,
            encrypt_token=True
        )
        # Create and save test token
        test_token = {
            "access_token": "change-me",
            "refresh_token": "change-me",
            "expires_at": 1234567890
        }
        auth_obj._save_encrypted_token(test_token)
        
        # Load and decrypt token
        loaded_token = auth_obj._load_encrypted_token()
        
        # Verify token matches
        self.assertIsNotNone(loaded_token)
        self.assertEqual(loaded_token['access_token'], test_token['access_token'])
        self.assertEqual(loaded_token['refresh_token'], test_token['refresh_token'])
        self.assertEqual(loaded_token['expires_at'], test_token['expires_at'])
        
        print("✓ Encrypted token loaded and decrypted successfully")
    
    @patch('schwab_auth.SCHWAB_PY_AVAILABLE', True)
    @patch('schwab_auth.auth')
    def test_token_hmac_verification(self, mock_auth):
        """Test that HMAC verification detects tampering"""
        from schwab_auth import SchwabAuthenticator
        
        # Create authenticator
        auth_obj = SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
            token_path=self.temp_token_path,
            encrypt_token=True
        )
        
        # Create and save test token
        test_token = {
            "access_token": "change-me",
            "refresh_token": "change-me",
            "expires_at": 1234567890
        }
        auth_obj._save_encrypted_token(test_token)
        
        # Tamper with the HMAC to simulate tampering (without breaking Fernet decryption)
        with open(self.temp_token_path, 'r') as f:
            saved_data = json.load(f)
        
        # Change one character in the HMAC to simulate tampering
        # This will allow Fernet to decrypt but HMAC verification will fail
        original_hmac = saved_data['hmac']
        tampered_hmac = original_hmac[:-1] + ('a' if original_hmac[-1] != 'a' else 'b')
        saved_data['hmac'] = tampered_hmac
        
        with open(self.temp_token_path, 'w') as f:
            json.dump(saved_data, f)
        
        # Try to load tampered token - should raise ValueError
        with self.assertRaises(ValueError) as context:
            auth_obj._load_encrypted_token()
        
        # Our improved error message includes detailed recovery options
        error_msg = str(context.exception).lower()
        # Should mention token issues and tampering/integrity/corruption
        self.assertTrue(
            "token" in error_msg and 
            ("integrity" in error_msg or "decryption" in error_msg or "hmac" in error_msg)
        )
        print("✓ HMAC verification detected tampering")
    
    @patch('schwab_auth.SCHWAB_PY_AVAILABLE', True)
    @patch('schwab_auth.auth')
    def test_backward_compatibility_plain_token(self, mock_auth):
        """Test that plain (unencrypted) tokens can still be loaded"""
        from schwab_auth import SchwabAuthenticator
        
        # Create authenticator with encryption enabled
        auth_obj = SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
            token_path=self.temp_token_path,
            encrypt_token=True
        )
        # Create plain token file (old format)
        plain_token = {
            "access_token": "change-me",
            "refresh_token": "change-me",
            "expires_at": 9999999999
        }
        
        with open(self.temp_token_path, 'w') as f:
            json.dump(plain_token, f)
        
        # Load plain token
        loaded_token = auth_obj._load_encrypted_token()
        
        # Verify token was loaded correctly
        self.assertIsNotNone(loaded_token)
        self.assertEqual(loaded_token['access_token'], plain_token['access_token'])
        self.assertEqual(loaded_token['refresh_token'], plain_token['refresh_token'])
        
        print("✓ Backward compatibility: plain tokens can be loaded")
    
    @patch('schwab_auth.SCHWAB_PY_AVAILABLE', True)
    @patch('schwab_auth.auth')
    def test_encryption_disabled(self, mock_auth):
        """Test that encryption can be disabled"""
        from schwab_auth import SchwabAuthenticator
        
        # Create authenticator with encryption disabled
        auth_obj = SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
            token_path=self.temp_token_path,
            encrypt_token=False
        )
        # Verify encryption is disabled
        self.assertFalse(auth_obj.encrypt_token)
        
        # Create and save test token
        test_token = {
            "access_token": "change-me",
            "refresh_token": "change-me"
        }
        auth_obj._save_encrypted_token(test_token)
        
        # Verify token is saved as plain JSON
        with open(self.temp_token_path, 'r') as f:
            saved_data = json.load(f)
        
        # Should be plain JSON, not encrypted wrapper
        self.assertNotIn('encrypted', saved_data)
        self.assertEqual(saved_data['access_token'], test_token['access_token'])
        
        print("✓ Encryption can be disabled")


class TestLogMasking(unittest.TestCase):
    """Test that sensitive information is masked in logs"""
    
    @patch('schwab_auth.SCHWAB_PY_AVAILABLE', True)
    @patch('schwab_auth.auth')
    @patch('schwab_auth.logger')
    def test_callback_url_masked_in_logs(self, mock_logger, mock_auth):
        """Test that callback URL is masked in log statements"""
        from schwab_auth import SchwabAuthenticator
        
        sensitive_callback = "https://127.0.0.1:8182/oauth/callback"
        
        # Create authenticator
        auth_obj = SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url=sensitive_callback,
            token_path="test_token.json"
        )
        
        # Check that logger.info was called
        self.assertTrue(mock_logger.info.called)
        
        # Get all log calls
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        
        # Verify callback URL was masked in logs
        for call in log_calls:
            if 'callback' in call.lower():
                # The full callback URL should not appear in logs
                self.assertNotIn(sensitive_callback, call)
                print(f"✓ Callback URL masked in log: {call}")
                break
        else:
            print("✓ No callback URL found in logs (good)")


class TestIntegrationFlow(unittest.TestCase):
    """Integration tests for full encryption flow"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_key = Fernet.generate_key()
        os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY'] = self.test_key.decode('utf-8')
        
        self.temp_fd, self.temp_token_path = tempfile.mkstemp(suffix='.json')
        os.close(self.temp_fd)
        
    def tearDown(self):
        """Clean up test environment"""
        if 'SCHWAB_TOKEN_ENCRYPTION_KEY' in os.environ:
            del os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY']
        if os.path.exists(self.temp_token_path):
            os.remove(self.temp_token_path)
    
    @patch('schwab_auth.SCHWAB_PY_AVAILABLE', True)
    @patch('schwab_auth.auth')
    def test_full_encryption_flow(self, mock_auth):
        """Test complete flow: save encrypted -> load encrypted -> verify"""
        from schwab_auth import SchwabAuthenticator
        
        # Create authenticator
        auth_obj = SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
            token_path=self.temp_token_path,
            encrypt_token=True
        )
        # Original token
        original_token = {
            "access_token": "change-me",
            "refresh_token": "change-me",
            "expires_at": 1234567890,
            "token_type": "change-me",
            "scope": "read write"
        }
        
        # Save encrypted
        auth_obj._save_encrypted_token(original_token)
        print("✓ Step 1: Token saved encrypted")
        
        # Verify file is encrypted
        with open(self.temp_token_path, 'r') as f:
            file_content = json.load(f)
        
        self.assertTrue(file_content.get('encrypted', False))
        self.assertIn('hmac', file_content)
        print("✓ Step 2: Verified file is encrypted with HMAC")
        
        # Load and decrypt
        loaded_token = auth_obj._load_encrypted_token()
        print("✓ Step 3: Token loaded and decrypted")
        
        # Verify all fields match
        self.assertEqual(loaded_token, original_token)
        print("✓ Step 4: All token fields match original")
        
        # Test with different authenticator instance (simulating restart)
        auth_obj2 = SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
            token_path=self.temp_token_path,
            encrypt_token=True
        )
        loaded_token2 = auth_obj2._load_encrypted_token()
        self.assertEqual(loaded_token2, original_token)
        print("✓ Step 5: Token loads correctly after restart (new instance)")
        
        print("\n✓ Full encryption flow completed successfully")


def run_tests():
    """Run all test suites"""
    print("\n" + "="*70)
    print("TESTING TOKEN ENCRYPTION AND SECURITY ENHANCEMENTS")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestTokenEncryption))
    suite.addTests(loader.loadTestsFromTestCase(TestLogMasking))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationFlow))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    if result.wasSuccessful():
        print("✓ ALL TESTS PASSED!")
        print(f"  {result.testsRun} tests run, 0 failures")
    else:
        print("✗ SOME TESTS FAILED")
        print(f"  {result.testsRun} tests run")
        print(f"  {len(result.failures)} failures")
        print(f"  {len(result.errors)} errors")
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
