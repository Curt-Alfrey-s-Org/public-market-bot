#!/usr/bin/env python3
"""
Test suite for improved token decryption error handling
Tests that helpful error messages are provided when token decryption fails
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


class TestTokenDecryptionErrorHandling(unittest.TestCase):
    """Test improved error messages for token decryption failures"""
    
    def setUp(self):
        """Set up test environment"""
        # Generate test encryption keys
        self.test_key_1 = Fernet.generate_key()
        self.test_key_2 = Fernet.generate_key()  # Different key for testing mismatches
        
        # Create temporary token file
        self.temp_fd, self.temp_token_path = tempfile.mkstemp(suffix='.json')
        os.close(self.temp_fd)
        
        # Store original env vars to restore later
        self.original_env = {}
        for key in ['SCHWAB_TOKEN_ENCRYPTION_KEY', 'MP5_ENCRYPTION_KEY']:
            self.original_env[key] = os.environ.get(key)
        
    def tearDown(self):
        """Clean up test environment"""
        # Restore original env vars
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]
        
        # Clean up temp files
        if os.path.exists(self.temp_token_path):
            os.remove(self.temp_token_path)
        
        # Clean up any generated key files
        for key_file in ['.token.key', '.env.key']:
            if os.path.exists(key_file):
                try:
                    os.remove(key_file)
                except Exception:
                    pass
    
    @patch('schwab_auth.SCHWAB_PY_AVAILABLE', True)
    @patch('schwab_auth.auth')
    def test_helpful_error_when_encryption_key_missing(self, mock_auth):
        """Test that helpful error is shown when encryption key is missing"""
        from schwab_auth import SchwabAuthenticator
        
        # Remove all encryption key sources
        for key in ['SCHWAB_TOKEN_ENCRYPTION_KEY', 'MP5_ENCRYPTION_KEY']:
            if key in os.environ:
                del os.environ[key]
        
        # Create authenticator
        auth_obj = SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
            token_path=self.temp_token_path,
            encrypt_token=True
        )
        
        # Create an encrypted token with key 1
        os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY'] = self.test_key_1.decode('utf-8')
        test_token = {
            "access_token": "change-me",
            "refresh_token": "change-me",
            "expires_at": 1234567890
        }
        auth_obj._save_encrypted_token(test_token)
        
        # Remove encryption key - but note that _get_token_encryption_key will auto-generate
        # a key if none exists, so we need to test with a wrong key scenario instead
        del os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY']
        
        # Try to load - decryption will fail because auto-generated key won't match
        with self.assertRaises(ValueError) as cm:
            auth_obj._load_encrypted_token()
        
        error_msg = str(cm.exception)
        
        # Verify error message contains helpful guidance
        # Due to auto-key generation, we'll get HMAC mismatch or decryption failure
        self.assertTrue(
            "Token decryption failed" in error_msg or "Token integrity check failed" in error_msg,
            f"Expected token error message, got: {error_msg[:100]}"
        )
        self.assertIn("SCHWAB_TOKEN_ENCRYPTION_KEY", error_msg)
        self.assertIn("MP5_ENCRYPTION_KEY", error_msg)
        self.assertIn("Delete", error_msg)
        self.assertIn("re-authenticate", error_msg)
        self.assertIn("simulation mode", error_msg)
        
        print("✓ Helpful error message shown when encryption key is missing/wrong")
        print(f"  Error message preview: {error_msg[:150]}...")
    
    @patch('schwab_auth.SCHWAB_PY_AVAILABLE', True)
    @patch('schwab_auth.auth')
    def test_helpful_error_when_wrong_encryption_key(self, mock_auth):
        """Test that helpful error is shown when wrong encryption key is used"""
        from schwab_auth import SchwabAuthenticator
        
        # Create authenticator
        auth_obj = SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
            token_path=self.temp_token_path,
            encrypt_token=True
        )
        
        # Create encrypted token with key 1
        os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY'] = self.test_key_1.decode('utf-8')
        test_token = {
            "access_token": "change-me",
            "refresh_token": "change-me",
            "expires_at": 1234567890
        }
        auth_obj._save_encrypted_token(test_token)
        
        # Change to different key (simulating key mismatch)
        os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY'] = self.test_key_2.decode('utf-8')
        
        # Try to load - should get helpful error
        with self.assertRaises(ValueError) as cm:
            auth_obj._load_encrypted_token()
        
        error_msg = str(cm.exception)
        
        # Verify error message contains helpful guidance
        # With wrong key, HMAC check will fail first OR decryption will fail
        self.assertIn("Token", error_msg)
        self.assertIn("encryption key", error_msg.lower())
        self.assertIn("Delete", error_msg)
        self.assertIn("re-authenticate", error_msg)
        self.assertIn("simulation mode", error_msg)
        
        print("✓ Helpful error message shown when wrong encryption key is used")
        print(f"  Error message preview: {error_msg[:150]}...")
    
    @patch('schwab_auth.SCHWAB_PY_AVAILABLE', True)
    @patch('schwab_auth.auth')
    def test_helpful_error_when_token_corrupted(self, mock_auth):
        """Test that helpful error is shown when token file is corrupted"""
        from schwab_auth import SchwabAuthenticator
        
        os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY'] = self.test_key_1.decode('utf-8')
        
        # Create authenticator
        auth_obj = SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
            token_path=self.temp_token_path,
            encrypt_token=True
        )
        
        # Create encrypted token
        test_token = {
            "access_token": "change-me",
            "refresh_token": "change-me",
            "expires_at": 1234567890
        }
        auth_obj._save_encrypted_token(test_token)
        
        # Corrupt the encrypted data (but keep valid JSON structure)
        with open(self.temp_token_path, 'r') as f:
            token_data = json.load(f)
        
        # Corrupt the encrypted data by changing characters
        token_data['data'] = token_data['data'][:-10] + "CORRUPTED!"
        
        with open(self.temp_token_path, 'w') as f:
            json.dump(token_data, f)
        
        # Try to load - should get helpful error
        with self.assertRaises(ValueError) as cm:
            auth_obj._load_encrypted_token()
        
        error_msg = str(cm.exception)
        
        # Verify error message contains helpful guidance
        self.assertIn("Token", error_msg)
        # Check case-insensitive for "delete" or "Delete"
        self.assertTrue("delete" in error_msg.lower())
        self.assertTrue("authenticate" in error_msg.lower())
        
        print("✓ Helpful error message shown when token is corrupted")
        print(f"  Error message preview: {error_msg[:150]}...")
    
    @patch('schwab_auth.SCHWAB_PY_AVAILABLE', True)
    @patch('schwab_auth.auth')
    def test_helpful_error_in_get_client(self, mock_auth):
        """Test that get_client provides helpful error when decryption fails"""
        from schwab_auth import SchwabAuthenticator
        
        # Create authenticator
        auth_obj = SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
            token_path=self.temp_token_path,
            encrypt_token=True
        )
        
        # Create encrypted token with key 1
        os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY'] = self.test_key_1.decode('utf-8')
        test_token = {
            "access_token": "change-me",
            "refresh_token": "change-me",
            "expires_at": 1234567890
        }
        auth_obj._save_encrypted_token(test_token)
        
        # Change to wrong key
        os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY'] = self.test_key_2.decode('utf-8')
        
        # Try to get client in non-interactive mode - should get helpful error
        with self.assertRaises(ValueError) as cm:
            auth_obj.get_client(interactive=False)
        
        error_msg = str(cm.exception)
        
        # Verify error message contains recovery options
        self.assertIn("Token decryption failed", error_msg)
        self.assertIn("Recovery Options", error_msg)
        self.assertIn("Delete the token", error_msg)
        self.assertIn("simulation mode", error_msg)
        self.assertIn("SCHWAB_ENCRYPT_TOKEN=false", error_msg)
        
        print("✓ get_client provides helpful error when token decryption fails")
        print(f"  Error message preview: {error_msg[:200]}...")
    
    @patch('schwab_auth.SCHWAB_PY_AVAILABLE', True)
    @patch('schwab_auth.auth')
    def test_error_message_includes_token_path(self, mock_auth):
        """Test that error messages include the token file path for easy cleanup"""
        from schwab_auth import SchwabAuthenticator
        
        os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY'] = self.test_key_1.decode('utf-8')
        
        # Create authenticator with custom token path (cross-platform)
        custom_token_path = os.path.join(tempfile.gettempdir(), "test_token_custom.json")
        auth_obj = SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
            token_path=custom_token_path,
            encrypt_token=True
        )
        
        # Create encrypted token
        test_token = {
            "access_token": "change-me",
            "refresh_token": "change-me",
            "expires_at": 1234567890
        }
        auth_obj._save_encrypted_token(test_token)
        
        # Change to wrong key
        os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY'] = self.test_key_2.decode('utf-8')
        
        try:
            # Try to load - should fail
            with self.assertRaises(ValueError) as cm:
                auth_obj._load_encrypted_token()
            
            error_msg = str(cm.exception)
            
            # Verify error message includes the custom token path
            self.assertIn(custom_token_path, error_msg)
            
            print("✓ Error messages include token file path for easy cleanup")
            print(f"  Token path in error: {custom_token_path}")
        finally:
            # Clean up
            if os.path.exists(custom_token_path):
                os.remove(custom_token_path)


if __name__ == '__main__':
    print("Testing Token Decryption Error Handling")
    print("=" * 60)
    unittest.main(verbosity=2)
