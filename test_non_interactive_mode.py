#!/usr/bin/env python3
"""
Test Non-Interactive Mode OAuth Handling

This test verifies that the bot handles non-interactive environments correctly
and doesn't fail with "EOF when reading a line" errors.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path to import main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_non_interactive_without_token():
    """
    Test that bot gracefully handles non-interactive mode without token file.
    Should automatically switch to yfinance simulation mode.
    """
    print("\n" + "="*60)
    print("TEST: Non-Interactive Mode Without Token")
    print("="*60)
    
    # Set up environment
    original_env = {}
    env_vars = {
        'NON_INTERACTIVE': 'true',
        'SCHWAB_API_ENABLED': 'on',  # Enabled but should gracefully fall back
        'SCHWAB_API_KEY': 'change-me',
        'SCHWAB_APP_SECRET': 'change-me',
        'SCHWAB_CALLBACK_URL': 'https://127.0.0.1:8182',
        'SCHWAB_ACCOUNT_ID': 'test_account',
        'SCHWAB_TOKEN_PATH': 'test_token_nonexistent.json',
        'PAPER_TRADING_MODE': 'true',
        'SCHWAB_SANDBOX_MODE': 'true'
    }
    
    # Save original env vars
    for key in env_vars:
        original_env[key] = os.environ.get(key)
        os.environ[key] = env_vars[key]
    
    try:
        # Import after setting env vars
        from main import TradingBot
        
        print("\n✓ Creating TradingBot instance...")
        bot = TradingBot(total_capital=1000.0)
        
        # Verify bot is in yfinance sim mode
        assert bot.using_yfinance_sim == True, \
            "Bot should be in yfinance_sim mode when NON_INTERACTIVE=true without token"
        assert bot.schwab_api_available == False, \
            "Schwab API should be marked unavailable in non-interactive mode without token"
        
        print("✓ Bot correctly entered yfinance simulation mode")
        print("✓ No EOF error occurred")
        print("\n" + "="*60)
        print("TEST PASSED: Non-Interactive Mode Without Token")
        print("="*60)
        return True
        
    except EOFError as e:
        print(f"✗ TEST FAILED: EOFError occurred: {e}")
        print("  This means the bot tried to read stdin in non-interactive mode")
        return False
    except Exception as e:
        print(f"✗ TEST FAILED: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original env vars
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_non_interactive_with_token():
    """
    Test that bot can use existing token in non-interactive mode.
    """
    print("\n" + "="*60)
    print("TEST: Non-Interactive Mode With Token")
    print("="*60)
    
    # Use the default token path
    token_path = 'token.json'
    
    # Create a temporary token file at the default location
    token_existed = os.path.exists(token_path)
    original_content = None
    if token_existed:
        # Back up existing token
        with open(token_path, 'r') as f:
            original_content = f.read()
    
    # Write a minimal token structure (won't be valid but tests file existence check)
    with open(token_path, 'w') as f:
        f.write('{"access_token": "change-me", "refresh_token": "change-me"}')
    
    try:
        # Set up environment
        original_env = {}
        env_vars = {
            'NON_INTERACTIVE': 'true',
            'SCHWAB_API_ENABLED': 'on',
            'SCHWAB_API_KEY': 'change-me',
            'SCHWAB_APP_SECRET': 'change-me',
            'SCHWAB_CALLBACK_URL': 'https://127.0.0.1:8182',
            'SCHWAB_ACCOUNT_ID': 'test_account',
            'PAPER_TRADING_MODE': 'true',
            'SCHWAB_SANDBOX_MODE': 'true'
        }
        
        # Save original env vars
        for key in env_vars:
            original_env[key] = os.environ.get(key)
            os.environ[key] = env_vars[key]
        
        # Import after setting env vars
        from main import TradingBot
        
        print(f"\n✓ Created temporary token file: {token_path}")
        print("✓ Creating TradingBot instance...")
        bot = TradingBot(total_capital=1000.0)
        
        # Note: Bot should initialize authenticator when token exists
        # It may still fail later when trying to use the fake token, but shouldn't fail on init
        print("✓ Bot initialized successfully with token file present")
        print("✓ No EOF error occurred during initialization")
        print("\n" + "="*60)
        print("TEST PASSED: Non-Interactive Mode With Token")
        print("="*60)
        return True
        
    except EOFError as e:
        print(f"✗ TEST FAILED: EOFError occurred: {e}")
        print("  This means the bot tried to read stdin in non-interactive mode")
        return False
    except Exception as e:
        print(f"✗ TEST FAILED: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if token_existed and original_content:
            # Restore original token
            with open(token_path, 'w') as f:
                f.write(original_content)
        elif not token_existed and os.path.exists(token_path):
            # Remove test token
            os.remove(token_path)
        
        # Restore original env vars
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_api_disabled_mode():
    """
    Test that bot works correctly when SCHWAB_API_ENABLED=off.
    Should use yfinance without attempting OAuth.
    """
    print("\n" + "="*60)
    print("TEST: API Disabled Mode")
    print("="*60)
    
    # Set up environment
    original_env = {}
    env_vars = {
        'NON_INTERACTIVE': 'true',
        'SCHWAB_API_ENABLED': 'off',  # API disabled
        'SCHWAB_API_KEY': 'change-me',
        'SCHWAB_APP_SECRET': 'change-me',
        'SCHWAB_CALLBACK_URL': 'https://127.0.0.1:8182',
        'SCHWAB_ACCOUNT_ID': 'test_account',
        'SCHWAB_TOKEN_PATH': 'test_token_nonexistent.json',
        'PAPER_TRADING_MODE': 'true',
        'SCHWAB_SANDBOX_MODE': 'true'
    }
    
    # Save original env vars
    for key in env_vars:
        original_env[key] = os.environ.get(key)
        os.environ[key] = env_vars[key]
    
    try:
        # Import after setting env vars
        from main import TradingBot
        
        print("\n✓ Creating TradingBot instance with API disabled...")
        bot = TradingBot(total_capital=1000.0)
        
        # Verify bot is in simulation mode with API disabled
        assert bot.using_yfinance_sim == True, \
            "Bot should be in yfinance_sim mode when SCHWAB_API_ENABLED=off"
        assert bot.schwab_api_available == False, \
            "Schwab API should be marked unavailable when SCHWAB_API_ENABLED=off"
        assert bot.schwab_authenticator is None, \
            "Schwab authenticator should not be initialized when API is disabled"
        
        print("✓ Bot correctly skipped Schwab OAuth initialization")
        print("✓ Bot is using yfinance simulation mode")
        print("✓ No EOF error occurred")
        print("\n" + "="*60)
        print("TEST PASSED: API Disabled Mode")
        print("="*60)
        return True
        
    except EOFError as e:
        print(f"✗ TEST FAILED: EOFError occurred: {e}")
        print("  This means the bot tried to read stdin even with API disabled")
        return False
    except Exception as e:
        print(f"✗ TEST FAILED: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original env vars
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Non-Interactive Mode OAuth Tests")
    print("="*60)
    
    results = []
    
    # Test 1: Non-interactive without token (should auto-fallback)
    results.append(("Non-Interactive Without Token", test_non_interactive_without_token()))
    
    # Test 2: Non-interactive with token (should initialize authenticator)
    results.append(("Non-Interactive With Token", test_non_interactive_with_token()))
    
    # Test 3: API disabled (should skip OAuth entirely)
    results.append(("API Disabled Mode", test_api_disabled_mode()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*60)
    
    return all(result for _, result in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
