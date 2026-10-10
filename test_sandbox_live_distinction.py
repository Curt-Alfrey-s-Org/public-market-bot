#!/usr/bin/env python3
"""
Test script for Schwab Auth Sandbox/Live Environment Distinction
Tests that the environment parameter is properly tracked and validated
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch
import schwab_auth

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestSandboxLiveDistinction(unittest.TestCase):
    """Test environment parameter in SchwabAuthenticator"""
    
    def test_import_schwab_auth(self):
        """Test that schwab_auth module can be imported"""
        self.assertIsNotNone(schwab_auth)
        print("✓ schwab_auth module imported successfully")
    
    def test_authenticator_sandbox_environment(self):
        """Test that SchwabAuthenticator accepts sandbox environment"""
        import schwab_auth
        
        if not schwab_auth.SCHWAB_PY_AVAILABLE:
            print("✓ Skipping test - schwab-py not installed")
            return
        
        auth = schwab_auth.SchwabAuthenticator(
            environment="sandbox"
        )
        
        self.assertEqual(auth.environment, "sandbox")
        self.assertEqual(auth.get_environment(), "sandbox")
        print("✓ Sandbox environment properly set")
    
    def test_authenticator_production_environment(self):
        """Test that SchwabAuthenticator accepts production environment"""
        import schwab_auth
        
        if not schwab_auth.SCHWAB_PY_AVAILABLE:
            print("✓ Skipping test - schwab-py not installed")
            return
        
        auth = schwab_auth.SchwabAuthenticator(
            api_key="change-me",
            environment="production",
        )
        
        self.assertEqual(auth.environment, "production")
        self.assertEqual(auth.get_environment(), "production")
        print("✓ Production environment properly set")
    
    def test_authenticator_default_environment(self):
        """Test that SchwabAuthenticator defaults to sandbox"""
        import schwab_auth
        
        if not schwab_auth.SCHWAB_PY_AVAILABLE:
            print("✓ Skipping test - schwab-py not installed")
            return
        
        auth = schwab_auth.SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
        )
        self.assertEqual(auth.environment, "sandbox")
        print("✓ Default environment is sandbox")
    
    def test_authenticator_invalid_environment(self):
        """Test that SchwabAuthenticator rejects invalid environment"""
        import schwab_auth
        
        if not schwab_auth.SCHWAB_PY_AVAILABLE:
            print("✓ Skipping test - schwab-py not installed")
            return
        
        with self.assertRaises(ValueError) as context:
            auth = schwab_auth.SchwabAuthenticator(
                api_key="change-me",
                app_secret="change-me",
                callback_url="https://127.0.0.1:8182",
                token_path="test_token.json",
                environment="invalid"
            )
        
        self.assertIn("sandbox", str(context.exception))
        self.assertIn("production", str(context.exception))
        print("✓ Invalid environment properly rejected")
    
    def test_create_schwab_client_sandbox_from_env(self):
        """Test that create_schwab_client uses SCHWAB_SANDBOX_MODE=true"""
        import schwab_auth
        
        if not schwab_auth.SCHWAB_PY_AVAILABLE:
            print("✓ Skipping test - schwab-py not installed")
            return
        
        # Set environment variable
        os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
        
        with patch('schwab_auth.SchwabAuthenticator') as MockAuth:
            mock_auth_instance = Mock()
            mock_client = Mock()
            mock_auth_instance.get_client.return_value = mock_client
            MockAuth.return_value = mock_auth_instance
            
            from schwab_auth import create_schwab_client
            
            client = create_schwab_client(
                api_key="change-me",
                app_secret="change-me",
                interactive=False
            )
            
            # Verify authenticator was created with sandbox environment
            MockAuth.assert_called_once()
            call_kwargs = MockAuth.call_args[1]
            self.assertEqual(call_kwargs['environment'], 'sandbox')
            print("✓ create_schwab_client respects SCHWAB_SANDBOX_MODE=true")
    
    def test_create_schwab_client_production_from_env(self):
        """Test that create_schwab_client uses SCHWAB_SANDBOX_MODE=false"""
        import schwab_auth
        
        if not schwab_auth.SCHWAB_PY_AVAILABLE:
            print("✓ Skipping test - schwab-py not installed")
            return
        
        # Set environment variable
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        
        with patch('schwab_auth.SchwabAuthenticator') as MockAuth:
            mock_auth_instance = Mock()
            mock_client = Mock()
            mock_auth_instance.get_client.return_value = mock_client
            MockAuth.return_value = mock_auth_instance
            
            from schwab_auth import create_schwab_client
            
            client = create_schwab_client(
                api_key="change-me",
                app_secret="change-me",
                interactive=False
            )
            
            # Verify authenticator was created with production environment
            MockAuth.assert_called_once()
            call_kwargs = MockAuth.call_args[1]
            self.assertEqual(call_kwargs['environment'], 'production')
            print("✓ create_schwab_client respects SCHWAB_SANDBOX_MODE=false")
    
    def test_create_schwab_client_explicit_environment(self):
        """Test that explicit environment parameter overrides SCHWAB_SANDBOX_MODE"""
        import schwab_auth
        
        if not schwab_auth.SCHWAB_PY_AVAILABLE:
            print("✓ Skipping test - schwab-py not installed")
            return
        
        # Set environment variable to sandbox
        os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
        
        with patch('schwab_auth.SchwabAuthenticator') as MockAuth:
            mock_auth_instance = Mock()
            mock_client = Mock()
            mock_auth_instance.get_client.return_value = mock_client
            MockAuth.return_value = mock_auth_instance
            
            # But pass production explicitly
            client = schwab_auth.create_schwab_client(
                api_key="change-me",
                app_secret="change-me",
                interactive=False,
                environment="production"
            )
            
            # Verify authenticator was created with production (explicit override)
            MockAuth.assert_called_once()
            call_kwargs = MockAuth.call_args[1]
            self.assertEqual(call_kwargs['environment'], 'production')
            print("✓ Explicit environment parameter overrides SCHWAB_SANDBOX_MODE")
    
    def test_encrypt_token_parameter(self):
        """Test that encrypt_token parameter is properly handled"""
        import schwab_auth
        
        if not schwab_auth.SCHWAB_PY_AVAILABLE:
            print("✓ Skipping test - schwab-py not installed")
            return
        
        # Test with encrypt_token=True
        auth = schwab_auth.SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
            token_path="test_token.json",
            environment="sandbox",
            encrypt_token=True
        )
        
        self.assertTrue(auth.encrypt_token)
        print("✓ encrypt_token parameter properly set to True")
        
        # Test with encrypt_token=False
        auth2 = schwab_auth.SchwabAuthenticator(
            api_key="change-me",
            app_secret="change-me",
            callback_url="https://127.0.0.1:8182",
            token_path="test_token.json",
            environment="sandbox",
            encrypt_token=False
        )
        
        self.assertFalse(auth2.encrypt_token)
        print("✓ encrypt_token parameter properly set to False")
    
    def test_credential_environment_validation_warnings(self):
        """Test that credential/environment mismatch generates warnings"""
        import schwab_auth
        import logging
        if not schwab_auth.SCHWAB_PY_AVAILABLE:
            print("✓ Skipping test - schwab-py not installed")
            return
        
        # Set up logging to capture warnings
        log_capture = []
        
        class TestHandler(logging.Handler):
            def emit(self, record):
                log_capture.append(record.getMessage())
        
        handler = TestHandler()
        handler.setLevel(logging.WARNING)
        logger = logging.getLogger('schwab_auth')
        logger.addHandler(handler)
        
        try:
            # Test production environment - should show warnings
            auth = schwab_auth.SchwabAuthenticator(
                api_key="change-me",
                app_secret="change-me",
                callback_url="https://127.0.0.1:8182",
                token_path="test_token.json",
                environment="production"
            )
            # Check that production warnings were logged
            production_warnings = [msg for msg in log_capture if 'PRODUCTION' in msg]
            self.assertTrue(len(production_warnings) > 0, "Production mode should log warnings")
            print("✓ Production environment generates appropriate warnings")
            
        finally:
            logger.removeHandler(handler)


def run_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("Testing Schwab Auth Sandbox/Live Environment Distinction")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSandboxLiveDistinction)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    if result.wasSuccessful():
        print("✓ All tests passed!")
        print(f"  {result.testsRun} tests run, 0 failures")
    else:
        print("✗ Some tests failed")
        print(f"  {result.testsRun} tests run")
        print(f"  {len(result.failures)} failures")
        print(f"  {len(result.errors)} errors")
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
