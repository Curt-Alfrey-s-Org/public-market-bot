#!/usr/bin/env python3
"""
Integration test to verify schwab_auth changes don't break main.py initialization
Tests the integration between main.py and schwab_auth.py
"""

import sys
import ast
import pytest


@pytest.mark.integration
def test_schwab_auth_integration():
    """Pytest wrapper for schwab auth integration test"""
    result = main()
    assert result == 0, "Schwab auth integration test should pass"


def test_syntax():
    """Test that both files have valid Python syntax"""
    print("="*70)
    print("Testing Python Syntax")
    print("="*70)
    
    files_to_check = ['schwab_auth.py', 'main.py']
    
    for filename in files_to_check:
        print(f"\nChecking {filename}...")
        try:
            with open(filename, 'r') as f:
                code = f.read()
            ast.parse(code)
            print(f"  ✓ {filename} has valid syntax")
        except SyntaxError as e:
            print(f"  ✗ {filename} has syntax error: {e}")
            return False
    
    return True

def test_imports():
    """Test that schwab_auth can be imported"""
    print("\n" + "="*70)
    print("Testing Module Imports")
    print("="*70)
    
    print("\nTesting schwab_auth import...")
    try:
        import schwab_auth
        print("  ✓ schwab_auth imported successfully")
        print(f"  - SCHWAB_PY_AVAILABLE: {schwab_auth.SCHWAB_PY_AVAILABLE}")
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import schwab_auth: {e}")
        return False

def test_authenticator_initialization():
    """Test that SchwabAuthenticator can be initialized with environment parameter"""
    print("\n" + "="*70)
    print("Testing SchwabAuthenticator Initialization")
    print("="*70)
    
    try:
        import schwab_auth
        
        if not schwab_auth.SCHWAB_PY_AVAILABLE:
            print("\n  ℹ schwab-py not installed - testing initialization logic only")
            
            # Test that environment validation works even without schwab-py
            print("\n  Testing environment parameter validation...")
            try:
                # This should fail because schwab-py is not available
                schwab_auth.SchwabAuthenticator(
                    api_key="change-me",
                    app_secret="change-me",
                    callback_url="https://127.0.0.1:8182",
                    environment="sandbox"
                )
                print("  ✗ Should have raised ImportError")
                return False
            except ImportError as e:
                if "schwab-py library is not installed" in str(e):
                    print("  ✓ Correct ImportError raised when schwab-py missing")
                else:
                    print(f"  ✗ Wrong error: {e}")
                    return False
            
            # Test invalid environment parameter
            print("\n  Testing parameter signature (environment parameter exists)...")
            import inspect
            sig = inspect.signature(schwab_auth.SchwabAuthenticator.__init__)
            params = list(sig.parameters.keys())
            if 'environment' in params:
                print(f"  ✓ 'environment' parameter exists in __init__")
                print(f"  - All parameters: {params}")
            else:
                print(f"  ✗ 'environment' parameter missing")
                print(f"  - Found parameters: {params}")
                return False
            
            return True
        else:
            print("\n  schwab-py is installed - testing full initialization")
            
            # Test with sandbox
            print("\n  Testing sandbox environment...")
            auth = schwab_auth.SchwabAuthenticator(
                api_key="change-me",
                app_secret="change-me",
                callback_url="https://127.0.0.1:8182",
                environment="sandbox"
            )
            if auth.environment == "sandbox":
                print(f"  ✓ Sandbox environment set correctly")
            else:
                print(f"  ✗ Environment is {auth.environment}, expected sandbox")
                return False
            
            # Test with production
            print("\n  Testing production environment...")
            auth = schwab_auth.SchwabAuthenticator(
                api_key="change-me",
                app_secret="change-me",
                callback_url="https://127.0.0.1:8182",
                environment="production"
            )
            if auth.environment == "production":
                print(f"  ✓ Production environment set correctly")
            else:
                print(f"  ✗ Environment is {auth.environment}, expected production")
                return False
            
            # Test invalid environment
            print("\n  Testing invalid environment...")
            try:
                schwab_auth.SchwabAuthenticator(
                    api_key="change-me",
                    app_secret="change-me",
                    callback_url="https://127.0.0.1:8182",
                    environment="invalid"
                )
                print(f"  ✗ Should have raised ValueError for invalid environment")
                return False
            except ValueError as e:
                if "Invalid environment" in str(e):
                    print(f"  ✓ Correct ValueError raised for invalid environment")
                else:
                    print(f"  ✗ Wrong ValueError message: {e}")
                    return False
            
            # Test default environment
            print("\n  Testing default environment...")
            auth = schwab_auth.SchwabAuthenticator(
                api_key="change-me",
                app_secret="change-me",
                callback_url="https://127.0.0.1:8182"
            )
            if auth.environment == "sandbox":
                print(f"  ✓ Default environment is sandbox")
            else:
                print(f"  ✗ Default environment is {auth.environment}, expected sandbox")
                return False
            
            return True
            
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_create_schwab_client_signature():
    """Test that create_schwab_client has environment parameter"""
    print("\n" + "="*70)
    print("Testing create_schwab_client Function")
    print("="*70)
    
    try:
        import schwab_auth
        import inspect
        
        sig = inspect.signature(schwab_auth.create_schwab_client)
        params = list(sig.parameters.keys())
        
        print(f"\nFunction signature parameters: {params}")
        
        if 'environment' in params:
            print("  ✓ 'environment' parameter exists in create_schwab_client")
            
            # Check if it's optional
            param = sig.parameters['environment']
            if param.default != inspect.Parameter.empty:
                print(f"  ✓ 'environment' parameter is optional (default: {param.default})")
            else:
                print(f"  ℹ 'environment' parameter is required")
            
            return True
        else:
            print("  ✗ 'environment' parameter missing from create_schwab_client")
            return False
            
    except Exception as e:
        print(f"  ✗ Error checking function signature: {e}")
        return False

def main():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("Schwab Auth Integration Test")
    print("="*70 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Syntax Check", test_syntax()))
    results.append(("Import Test", test_imports()))
    results.append(("Authenticator Init", test_authenticator_initialization()))
    results.append(("Function Signature", test_create_schwab_client_signature()))
    
    # Print summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("✓ All integration tests passed!")
    else:
        print("✗ Some integration tests failed")
    print("="*70 + "\n")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
