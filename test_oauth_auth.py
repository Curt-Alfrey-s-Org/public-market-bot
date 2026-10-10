#!/usr/bin/env python3
"""
Test script for Schwab OAuth authentication
Tests the authentication module without actually connecting to Schwab
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestSchwabAuthentication(unittest.TestCase):
    """Test the Schwab authentication module"""
    
    def test_import_schwab_auth(self):
        """Test that schwab_auth module can be imported"""
        try:
            import schwab_auth
            self.assertIsNotNone(schwab_auth)
            print("✓ schwab_auth module imported successfully")
            
            # Check if schwab-py is available
            if not schwab_auth.SCHWAB_PY_AVAILABLE:
                print("  ℹ Note: schwab-py library not installed (expected in test environment)")
        except ImportError as e:
            self.fail(f"Failed to import schwab_auth: {e}")
    
    def test_authenticator_init_without_schwab_py(self):
        """Test that SchwabAuthenticator gives helpful error when schwab-py missing"""
        import schwab_auth
        
        if not schwab_auth.SCHWAB_PY_AVAILABLE:
            # Should raise ImportError with helpful message
            with self.assertRaises(ImportError) as context:
                auth = schwab_auth.SchwabAuthenticator(
                    api_key="change-me",
                    app_secret="change-me",
                    callback_url="https://127.0.0.1:8182",
                    token_path="test_token.json"
                )
            
            self.assertIn("schwab-py library is not installed", str(context.exception))
            print("✓ Helpful error message when schwab-py not installed")
        else:
            print("✓ schwab-py is installed, skipping this test")
    
    def test_authenticator_init(self):
        """Test that SchwabAuthenticator can be initialized (when schwab-py is available)"""
        import schwab_auth
        
        if not schwab_auth.SCHWAB_PY_AVAILABLE:
            print("✓ Skipping test - schwab-py not installed")
            return
        
        try:
            from schwab_auth import SchwabAuthenticator
            
            auth = SchwabAuthenticator(
                api_key="change-me",
                app_secret="change-me",
                callback_url="https://127.0.0.1:8182",
                token_path="test_token.json"
            )
            
            self.assertEqual(auth.api_key, "test_key")
            self.assertEqual(auth.app_secret, "test_secret")
            self.assertEqual(auth.callback_url, "https://127.0.0.1:8182")
            self.assertEqual(auth.token_path, "test_token.json")
            print("✓ SchwabAuthenticator initialized successfully")
            
        except Exception as e:
            self.fail(f"Failed to initialize SchwabAuthenticator: {e}")
    
    def test_invalid_credentials(self):
        """Test that invalid credentials are caught"""
        import schwab_auth
        
        if not schwab_auth.SCHWAB_PY_AVAILABLE:
            print("✓ Skipping test - schwab-py not installed")
            return
        
        from schwab_auth import SchwabAuthenticator
        
        auth = SchwabAuthenticator(
            api_key="change-me",  # Placeholder
            app_secret="change-me",  # Placeholder
            callback_url="https://127.0.0.1:8182",
            token_path="test_token.json"
        )
        
        # Should raise ValueError for invalid credentials
        with self.assertRaises(ValueError) as context:
            auth.get_client(interactive=False)
        
        self.assertIn("Invalid SCHWAB_API_KEY", str(context.exception))
        print("✓ Invalid credentials properly detected")
    
    @patch('schwab_auth.auth')
    def test_client_creation_with_mock(self, mock_auth_module):
        """Test client creation with mocked schwab-py"""
        import schwab_auth
        
        if not schwab_auth.SCHWAB_PY_AVAILABLE:
            print("✓ Skipping test - schwab-py not installed")
            return
        
        from schwab_auth import SchwabAuthenticator
        
        # Mock the schwab client
        mock_client = Mock()
        mock_auth_module.easy_client = Mock(return_value=mock_client)
        
        auth = SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
            token_path="test_token.json"
        )
        
        # Get client (with mock)
        client = auth.get_client(interactive=False)
        
        self.assertIsNotNone(client)
        self.assertTrue(auth.is_authenticated())
        print("✓ Client creation works with mocked schwab-py")
    
    def test_main_py_imports(self):
        """Test that main.py can import with new changes"""
        try:
            # Just check syntax, don't actually run
            import ast
            with open('main.py', 'r') as f:
                ast.parse(f.read())
            print("✓ main.py syntax is valid")
        except SyntaxError as e:
            self.fail(f"main.py has syntax errors: {e}")


def run_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("Testing Schwab OAuth Authentication Implementation")
    print("="*60 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSchwabAuthentication)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    if result.wasSuccessful():
        print("✓ All tests passed!")
        print(f"  {result.testsRun} tests run, 0 failures")
    else:
        print("✗ Some tests failed")
        print(f"  {result.testsRun} tests run")
        print(f"  {len(result.failures)} failures")
        print(f"  {len(result.errors)} errors")
    print("="*60 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
