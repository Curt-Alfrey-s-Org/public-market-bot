#!/usr/bin/env python3
"""
Test suite for HMAC integrity checks in schwab_auth.py
Tests the new HMAC validation layer for encrypted environment variables
"""

import os
import sys
import unittest
import logging
import logging.handlers
from unittest.mock import patch
from cryptography.fernet import Fernet

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set test environment
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'


class TestHMACIntegrity(unittest.TestCase):
    """Test HMAC integrity checking in _decrypt_sensitive_value"""
    
    def setUp(self):
        """Set up test environment"""
        # Generate a test encryption key
        self.test_key = Fernet.generate_key()
        os.environ['MP5_ENCRYPTION_KEY'] = self.test_key.decode('utf-8')
        
        # Set up logging to capture warnings
        self.log_handler = logging.handlers.MemoryHandler(capacity=1000)
        logger = logging.getLogger('schwab_auth')
        logger.addHandler(self.log_handler)
        logger.setLevel(logging.DEBUG)
        
    def tearDown(self):
        """Clean up test environment"""
        if 'MP5_ENCRYPTION_KEY' in os.environ:
            del os.environ['MP5_ENCRYPTION_KEY']
        
        # Clean up logger
        logger = logging.getLogger('schwab_auth')
        logger.removeHandler(self.log_handler)
    
    def test_plain_value_passthrough(self):
        """Test that plain (non-encrypted) values pass through unchanged"""
        from schwab_auth import _decrypt_sensitive_value
        
        plain_value = "plain_text_api_key"
        result = _decrypt_sensitive_value(plain_value)
        
        self.assertEqual(result, plain_value)
        print("✓ Plain values pass through unchanged")
    
    def test_encrypt_and_decrypt_with_hmac(self):
        """Test encrypting and decrypting a value with HMAC protection"""
        from schwab_auth import _encrypt_sensitive_value, _decrypt_sensitive_value
        
        original_value = "test_api_key_12345"
        
        # Encrypt with HMAC
        encrypted = _encrypt_sensitive_value(original_value)
        self.assertIsNotNone(encrypted)
        self.assertTrue(encrypted.startswith("enc:"))
        
        # Verify format includes HMAC (enc:hmac:data)
        parts = encrypted[4:].split(':', 1)
        self.assertEqual(len(parts), 2, "Encrypted value should have HMAC format")
        print(f"✓ Encrypted with HMAC: {encrypted[:50]}...")
        
        # Decrypt and verify
        decrypted = _decrypt_sensitive_value(encrypted)
        self.assertEqual(decrypted, original_value)
        print("✓ Successfully decrypted value with HMAC validation")
    
    def test_legacy_format_without_hmac(self):
        """Test that legacy encrypted values (without HMAC) still work"""
        from schwab_auth import _decrypt_sensitive_value
        
        # Create a legacy format encrypted value (enc:data without HMAC)
        fernet = Fernet(self.test_key)
        original_value = "legacy_api_key"
        encrypted_bytes = fernet.encrypt(original_value.encode('utf-8'))
        legacy_encrypted = "enc:" + encrypted_bytes.decode('utf-8')
        
        # Should still decrypt successfully
        decrypted = _decrypt_sensitive_value(legacy_encrypted)
        self.assertEqual(decrypted, original_value)
        print("✓ Legacy format (without HMAC) still works")
    
    def test_hmac_tampering_detection(self):
        """Test that HMAC detects tampering with encrypted data"""
        from schwab_auth import _encrypt_sensitive_value, _decrypt_sensitive_value
        
        original_value = "secure_api_key"
        encrypted = _encrypt_sensitive_value(original_value)
        
        # Tamper with the encrypted data (change last character)
        parts = encrypted.split(':')
        self.assertEqual(len(parts), 3, "Should have enc:hmac:data format")
        
        # Change one character in the encrypted data
        tampered_data = parts[2][:-1] + ('X' if parts[2][-1] != 'X' else 'Y')
        tampered_encrypted = f"{parts[0]}:{parts[1]}:{tampered_data}"
        
        # Decryption should fail and return empty string
        decrypted = _decrypt_sensitive_value(tampered_encrypted)
        self.assertEqual(decrypted, "")
        print("✓ HMAC successfully detected data tampering")
    
    def test_decryption_failure_logging(self):
        """Test that decryption failures log WARNING level messages"""
        from schwab_auth import _decrypt_sensitive_value
        
        # Create invalid encrypted value
        invalid_encrypted = "enc:invalid_hmac:invalid_data"
        
        # Clear previous log records
        self.log_handler.buffer.clear()
        
        # Try to decrypt - should fail and log warning
        result = _decrypt_sensitive_value(invalid_encrypted)
        self.assertEqual(result, "")
        
        # Check that WARNING was logged (not just DEBUG)
        self.log_handler.flush()
        warning_logged = False
        for record in self.log_handler.buffer:
            if record.levelno >= logging.WARNING:
                warning_logged = True
                self.assertIn("integrity check failed", record.getMessage().lower())
                break
        
        self.assertTrue(warning_logged, "Decryption failure should log WARNING")
        print("✓ Decryption failures log at WARNING level")
    
    def test_missing_encryption_key_warning(self):
        """Test that missing encryption key logs warning"""
        from schwab_auth import _decrypt_sensitive_value
        
        # Clear previous log records
        self.log_handler.buffer.clear()
        
        # Remove encryption key
        del os.environ['MP5_ENCRYPTION_KEY']
        
        # Try to decrypt - should fail with warning
        encrypted = "enc:some_hmac:some_data"
        result = _decrypt_sensitive_value(encrypted)
        self.assertEqual(result, "")
        
        # Flush and check for warning about missing key
        self.log_handler.flush()
        warning_found = False
        for record in self.log_handler.buffer:
            msg = record.getMessage().lower()
            # Debug: print all log messages
            if record.levelno >= logging.WARNING:
                # Could be warning from missing key OR from decryption failure
                if "encryption key" in msg or "decrypt" in msg:
                    warning_found = True
                    break
        
        self.assertTrue(warning_found, "Missing key should log WARNING")
        print("✓ Missing encryption key logs warning")
    
    def test_none_and_empty_values(self):
        """Test handling of None and empty string values"""
        from schwab_auth import _decrypt_sensitive_value
        
        # None should return empty string
        result_none = _decrypt_sensitive_value(None)
        self.assertEqual(result_none, "")
        
        # Empty string should return empty string
        result_empty = _decrypt_sensitive_value("")
        self.assertEqual(result_empty, "")
        
        print("✓ None and empty values handled correctly")
    
    def test_encryption_without_fernet(self):
        """Test graceful degradation when Fernet not available"""
        from schwab_auth import _encrypt_sensitive_value, _decrypt_sensitive_value
        
        with patch('schwab_auth.FERNET_AVAILABLE', False):
            # Encryption should return None
            encrypted = _encrypt_sensitive_value("test_value")
            self.assertIsNone(encrypted)
            
            # Decryption should pass through unchanged
            plain = "plain_value"
            decrypted = _decrypt_sensitive_value(plain)
            self.assertEqual(decrypted, plain)
        
        print("✓ Graceful degradation without Fernet")


class TestGetDecryptedEnv(unittest.TestCase):
    """Test get_decrypted_env function with HMAC support"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_key = Fernet.generate_key()
        os.environ['MP5_ENCRYPTION_KEY'] = self.test_key.decode('utf-8')
        
        # Store original env values
        self.original_schwab_key = os.environ.get('SCHWAB_API_KEY')
        self.original_schwab_secret = os.environ.get('SCHWAB_APP_SECRET')
    
    def tearDown(self):
        """Restore original environment"""
        if 'MP5_ENCRYPTION_KEY' in os.environ:
            del os.environ['MP5_ENCRYPTION_KEY']
        
        # Restore original values
        for key, original in [
            ('SCHWAB_API_KEY', self.original_schwab_key),
            ('SCHWAB_APP_SECRET', self.original_schwab_secret)
        ]:
            if original:
                os.environ[key] = original
            elif key in os.environ:
                del os.environ[key]
    
    def test_get_decrypted_env_with_hmac(self):
        """Test get_decrypted_env with HMAC-protected encrypted values"""
        from schwab_auth import _encrypt_sensitive_value, get_decrypted_env
        
        # Encrypt a sensitive value
        original_key = "test_schwab_api_key_secret"
        encrypted = _encrypt_sensitive_value(original_key)
        
        # Set in environment
        os.environ['SCHWAB_API_KEY'] = encrypted
        
        # Retrieve and decrypt
        result = get_decrypted_env('SCHWAB_API_KEY', '')
        self.assertEqual(result, original_key)
        print("✓ get_decrypted_env works with HMAC-protected values")
    
    def test_get_decrypted_env_default_value(self):
        """Test get_decrypted_env returns default when key missing"""
        from schwab_auth import get_decrypted_env
        
        # Remove key if it exists
        if 'SCHWAB_API_KEY' in os.environ:
            del os.environ['SCHWAB_API_KEY']
        
        result = get_decrypted_env('SCHWAB_API_KEY', 'default_value')
        self.assertEqual(result, 'default_value')
        print("✓ get_decrypted_env returns default for missing keys")


def run_tests():
    """Run the test suite"""
    print("=" * 70)
    print("HMAC INTEGRITY CHECK TESTS")
    print("=" * 70)
    print()
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestHMACIntegrity))
    suite.addTests(loader.loadTestsFromTestCase(TestGetDecryptedEnv))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✓ All HMAC integrity tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
