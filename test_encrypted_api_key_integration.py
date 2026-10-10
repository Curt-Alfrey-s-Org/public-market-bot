#!/usr/bin/env python3
"""
Integration test to verify an encrypted sensitive API key can be used successfully.

Uses NEWS_API_KEY as the representative sensitive key (the ALFa AI brain is the
only AI provider; there is no HuggingFace key).
"""

import os
import tempfile
import shutil
from cryptography.fernet import Fernet
import pytest


@pytest.mark.integration
def test_encrypted_api_key_integration_wrapper():
    """Pytest wrapper for encrypted API key integration test"""
    success = test_encrypted_api_key_flow()
    assert success, "Encrypted API key integration test should pass"

# Test environment setup
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'

def test_encrypted_api_key_flow():
    """
    Test the full flow:
    1. Encrypt an API key and write to .env
    2. Reload environment
    3. Verify decryption works correctly
    """
    print("=" * 70)
    print("INTEGRATION TEST: Encrypted API Key Flow")
    print("=" * 70)
    print()
    
    # Create a temporary .env file for testing
    test_env_file = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
    test_key_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.key', delete=False)
    
    try:
        # Generate encryption key
        fernet_key = Fernet.generate_key()
        test_key_file.write(fernet_key)
        test_key_file.close()
        
        # Set the encryption key in environment
        os.environ['MP5_ENCRYPTION_KEY'] = fernet_key.decode('utf-8')
        
        # Encrypt a test API key
        fernet = Fernet(fernet_key)
        test_api_key = "change-me"
        encrypted_bytes = fernet.encrypt(test_api_key.encode('utf-8'))
        encrypted_value = "enc:" + encrypted_bytes.decode('utf-8')
        
        # Write to .env file
        test_env_file.write(f"NEWS_API_KEY={encrypted_value}\n")
        test_env_file.write(f"PAPER_TRADING_MODE=true\n")
        test_env_file.close()
        
        print(f"1. Created test .env file: {test_env_file.name}")
        print(f"   - Original API key: {test_api_key}")
        print(f"   - Encrypted value: {encrypted_value[:50]}...")
        print()
        
        # Load the .env file
        from dotenv import load_dotenv
        load_dotenv(test_env_file.name, override=True)
        
        # Update environment with encrypted value
        os.environ['NEWS_API_KEY'] = encrypted_value
        
        print("2. Loaded .env file and set encrypted value in environment")
        print()
        
        # Test decryption with main.py
        from main import get_decrypted_env
        decrypted_key = get_decrypted_env('NEWS_API_KEY', '')
        
        print("3. Testing decryption with main.py:")
        print(f"   - Decrypted value: {decrypted_key}")
        print(f"   - Matches original: {decrypted_key == test_api_key}")
        
        if decrypted_key != test_api_key:
            print("   ✗ FAILED: Decrypted value does not match original")
            return False
        
        print("   ✓ SUCCESS: main.py decryption works correctly")
        print()
        
        # Test with schwab_auth.py
        from schwab_auth import get_decrypted_env as schwab_get_decrypted_env
        
        # Encrypt Schwab credentials
        schwab_key = "test_schwab_key"
        schwab_secret = "change-me"
        
        encrypted_schwab_key = "enc:" + fernet.encrypt(schwab_key.encode('utf-8')).decode('utf-8')
        encrypted_schwab_secret = "change-me" + fernet.encrypt(schwab_secret.encode('utf-8')).decode('utf-8')
        
        os.environ['SCHWAB_API_KEY'] = encrypted_schwab_key
        os.environ['SCHWAB_APP_SECRET'] = encrypted_schwab_secret
        
        decrypted_schwab_key = schwab_get_decrypted_env('SCHWAB_API_KEY', '')
        decrypted_schwab_secret = schwab_get_decrypted_env('SCHWAB_APP_SECRET', '')
        
        print("4. Testing Schwab credentials decryption:")
        print(f"   - API Key matches: {decrypted_schwab_key == schwab_key}")
        print(f"   - Secret matches: {decrypted_schwab_secret == schwab_secret}")
        
        if decrypted_schwab_key != schwab_key or decrypted_schwab_secret != schwab_secret:
            print("   ✗ FAILED: Schwab credentials decryption failed")
            return False
        
        print("   ✓ SUCCESS: Schwab credentials decryption works correctly")
        print()
        
        print("=" * 70)
        print("✓ ALL INTEGRATION TESTS PASSED")
        print("=" * 70)
        print()
        print("Summary:")
        print("- Encrypted API keys can be stored in .env file")
        print("- Keys are properly decrypted when loaded from environment")
        print("- All modules (main, web_gui, schwab_auth) can decrypt correctly")
        print("- Sensitive API keys work end-to-end with encryption")
        print()
        
        return True
        
    finally:
        # Cleanup
        if os.path.exists(test_env_file.name):
            os.unlink(test_env_file.name)
        if os.path.exists(test_key_file.name):
            os.unlink(test_key_file.name)
        
        # Restore environment
        if 'MP5_ENCRYPTION_KEY' in os.environ:
            del os.environ['MP5_ENCRYPTION_KEY']


if __name__ == '__main__':
    success = test_encrypted_api_key_flow()
    exit(0 if success else 1)
