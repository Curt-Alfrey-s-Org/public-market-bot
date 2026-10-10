#!/usr/bin/env python3
"""
Test suite for encryption key generation and security enhancements
Tests key generation, file permissions, and secure storage
"""

import os
import sys
import stat
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set test environment
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'


class TestEncryptionKeyGeneration(unittest.TestCase):
    """Test encryption key generation and security"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Clear environment variable if it exists
        if 'MP5_ENCRYPTION_KEY' in os.environ:
            self.saved_env_key = os.environ['MP5_ENCRYPTION_KEY']
            del os.environ['MP5_ENCRYPTION_KEY']
        else:
            self.saved_env_key = None
    
    def tearDown(self):
        """Clean up test environment"""
        # Restore environment
        if self.saved_env_key:
            os.environ['MP5_ENCRYPTION_KEY'] = self.saved_env_key
        elif 'MP5_ENCRYPTION_KEY' in os.environ:
            del os.environ['MP5_ENCRYPTION_KEY']
        
        # Change back to original directory and clean up
        os.chdir(self.old_cwd)
        
        # Clean up temporary files
        for filename in ['.env.key']:
            filepath = os.path.join(self.test_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        
        # Remove temporary directory
        try:
            os.rmdir(self.test_dir)
        except OSError:
            pass  # Directory not empty, ignore
    
    def test_key_generation_main(self):
        """Test that main.py generates a key if it doesn't exist"""
        import main
        
        # Ensure no key file exists
        key_path = '.env.key'
        if os.path.exists(key_path):
            os.remove(key_path)
        
        # Call the function
        key = main._get_encryption_key()
        
        # Verify key was generated
        self.assertIsNotNone(key)
        self.assertIsInstance(key, bytes)
        
        # Verify key file was created
        self.assertTrue(os.path.exists(key_path))
        
        # Verify file permissions are secure (owner read/write only)
        file_stats = os.stat(key_path)
        file_mode = stat.S_IMODE(file_stats.st_mode)
        self.assertEqual(file_mode, 0o600, f"File permissions are {oct(file_mode)}, expected 0o600")
        
        print(f"✓ Key generated successfully with secure permissions: {oct(file_mode)}")
    
    def test_key_generation_schwab_auth(self):
        """Test that schwab_auth.py generates a key if it doesn't exist"""
        import schwab_auth
        
        # Ensure no key file exists
        key_path = '.env.key'
        if os.path.exists(key_path):
            os.remove(key_path)
        
        # Call the function
        key = schwab_auth._get_encryption_key()
        
        # Verify key was generated
        self.assertIsNotNone(key)
        self.assertIsInstance(key, bytes)
        
        # Verify key file was created
        self.assertTrue(os.path.exists(key_path))
        
        # Verify file permissions
        file_stats = os.stat(key_path)
        file_mode = stat.S_IMODE(file_stats.st_mode)
        self.assertEqual(file_mode, 0o600, f"File permissions are {oct(file_mode)}, expected 0o600")
        
        print(f"✓ schwab_auth key generated successfully with secure permissions: {oct(file_mode)}")
    
    def test_key_generation_sentiment_analyzer(self):
        """Test that sentiment_analyzer.py generates a key if it doesn't exist"""
        import sentiment_analyzer
        
        # Ensure no key file exists
        key_path = '.env.key'
        if os.path.exists(key_path):
            os.remove(key_path)
        
        # Call the function
        key = sentiment_analyzer._get_encryption_key()
        
        # Verify key was generated
        self.assertIsNotNone(key)
        self.assertIsInstance(key, bytes)
        
        # Verify key file was created
        self.assertTrue(os.path.exists(key_path))
        
        # Verify file permissions
        file_stats = os.stat(key_path)
        file_mode = stat.S_IMODE(file_stats.st_mode)
        self.assertEqual(file_mode, 0o600, f"File permissions are {oct(file_mode)}, expected 0o600")
        
        print(f"✓ sentiment_analyzer key generated successfully with secure permissions: {oct(file_mode)}")
    
    def test_key_generation_data_fetcher(self):
        """Test that data_fetcher.py generates a key if it doesn't exist"""
        import data_fetcher
        
        # Ensure no key file exists
        key_path = '.env.key'
        if os.path.exists(key_path):
            os.remove(key_path)
        
        # Call the function
        key = data_fetcher._get_encryption_key()
        
        # Verify key was generated
        self.assertIsNotNone(key)
        self.assertIsInstance(key, bytes)
        
        # Verify key file was created
        self.assertTrue(os.path.exists(key_path))
        
        # Verify file permissions
        file_stats = os.stat(key_path)
        file_mode = stat.S_IMODE(file_stats.st_mode)
        self.assertEqual(file_mode, 0o600, f"File permissions are {oct(file_mode)}, expected 0o600")
        
        print(f"✓ data_fetcher key generated successfully with secure permissions: {oct(file_mode)}")
    
    def test_key_retrieval_from_environment(self):
        """Test that key can be retrieved from environment variable"""
        import main
        
        # Set environment variable
        test_key = Fernet.generate_key()
        os.environ['MP5_ENCRYPTION_KEY'] = test_key.decode('utf-8')
        
        # Call the function
        key = main._get_encryption_key()
        
        # Verify key matches environment variable
        self.assertEqual(key, test_key)
        
        print("✓ Key retrieved successfully from environment variable")
    
    def test_key_retrieval_from_existing_file(self):
        """Test that key can be retrieved from existing .env.key file"""
        import main
        
        # Create a key file
        key_path = '.env.key'
        test_key = Fernet.generate_key()
        with open(key_path, 'wb') as f:
            f.write(test_key)
        
        # Call the function
        key = main._get_encryption_key()
        
        # Verify key matches file contents
        self.assertEqual(key, test_key)
        
        print("✓ Key retrieved successfully from existing file")
    
    def test_key_persistence_across_calls(self):
        """Test that generated key is persisted and reused"""
        import main
        
        # Ensure no key file exists
        key_path = '.env.key'
        if os.path.exists(key_path):
            os.remove(key_path)
        
        # First call - generates key
        key1 = main._get_encryption_key()
        
        # Second call - should retrieve the same key
        key2 = main._get_encryption_key()
        
        # Verify keys are the same
        self.assertEqual(key1, key2)
        
        print("✓ Key persisted and reused across calls")
    
    def test_key_can_decrypt_values(self):
        """Test that generated key can encrypt and decrypt values"""
        import main
        
        # Ensure no key file exists
        key_path = '.env.key'
        if os.path.exists(key_path):
            os.remove(key_path)
        
        # Get/generate key
        key = main._get_encryption_key()
        fernet = Fernet(key)
        
        # Test encryption/decryption
        test_value = "test_secret_value"
        encrypted = fernet.encrypt(test_value.encode('utf-8'))
        decrypted = fernet.decrypt(encrypted).decode('utf-8')
        
        self.assertEqual(test_value, decrypted)
        
        print("✓ Generated key can successfully encrypt and decrypt values")


if __name__ == '__main__':
    unittest.main(verbosity=2)
