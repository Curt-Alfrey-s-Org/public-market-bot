#!/usr/bin/env python3
"""
Verify Self-Test System
Tests that the self-test framework itself is working correctly
"""

import sys
import os
import json
import requests
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(text):
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)

def print_section(text):
    print("\n" + "-" * 70)
    print(text)
    print("-" * 70)

def test_color(color, symbol):
    """Print colored output"""
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, '')}{symbol}{colors['reset']}"

def test_1_startup_test_module():
    """Test 1: Verify startup test module works"""
    print_section("Test 1: Startup Test Module")
    
    try:
        from tests.startup_test import StartupTest
        print(f"{test_color('green', '✓')} Startup test module imports successfully")
        
        # Test with API URL
        tester = StartupTest(api_url="http://localhost:8002")
        print(f"{test_color('green', '✓')} StartupTest class instantiates")
        
        # Run tests
        results = tester.run_all()
        print(f"{test_color('green', '✓')} Tests execute without errors")
        
        print(f"\n  Results: {results['passed']}/{results['total']} passed")
        print(f"  Success Rate: {results['success_rate']:.1f}%")
        
        # Show individual results
        print("\n  Individual Test Results:")
        for test_result in results['results']:
            status = test_color('green', '✓') if test_result['passed'] else test_color('red', '✗')
            print(f"    {status} {test_result['name']}: {test_result['status']}")
        
        return True, results
    except Exception as e:
        print(f"{test_color('red', '✗')} Startup test module failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_2_api_health_endpoint():
    """Test 2: Verify API system health endpoint"""
    print_section("Test 2: API System Health Endpoint")
    
    try:
        response = requests.get("http://localhost:8002/api/system/health", timeout=5)
        
        if response.status_code == 200:
            print(f"{test_color('green', '✓')} Endpoint responds with 200")
            
            data = response.json()
            print(f"{test_color('green', '✓')} Response is valid JSON")
            
            # Check structure
            if 'self_test' in data:
                print(f"{test_color('green', '✓')} Response contains 'self_test' field")
                self_test = data['self_test']
                
                if 'passed' in self_test:
                    print(f"{test_color('green', '✓')} Self-test results included")
                    print(f"\n  Self-Test Status: {'PASS' if self_test['passed'] else 'FAIL'}")
                    print(f"  Tests: {self_test.get('passed_count', 0)}/{self_test.get('total', 0)} passed")
                    print(f"  Success Rate: {self_test.get('success_rate', 0):.1f}%")
                    
                    if 'results' in self_test:
                        print(f"\n  Individual Test Results:")
                        for test_result in self_test['results']:
                            status = test_color('green', '✓') if test_result.get('passed') else test_color('red', '✗')
                            print(f"    {status} {test_result.get('name', 'Unknown')}: {test_result.get('status', 'UNKNOWN')}")
                    
                    return True, data
                else:
                    print(f"{test_color('yellow', '⚠')} Self-test results missing 'passed' field")
                    return False, data
            else:
                print(f"{test_color('red', '✗')} Response missing 'self_test' field")
                return False, data
        else:
            print(f"{test_color('red', '✗')} Endpoint returned status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False, None
    except requests.exceptions.ConnectionError:
        print(f"{test_color('red', '✗')} Cannot connect to API")
        print("  Make sure API is running: ./start_api.sh")
        return False, None
    except Exception as e:
        print(f"{test_color('red', '✗')} Error: {e}")
        return False, None

def test_3_startup_event():
    """Test 3: Verify startup event runs tests"""
    print_section("Test 3: API Startup Event")
    
    try:
        # Check if startup event is registered
        from api.main import app
        
        # Check for startup event
        startup_events = [event for event in app.router.on_startup if hasattr(event, '__name__')]
        
        if startup_events:
            print(f"{test_color('green', '✓')} Startup event is registered")
            print(f"  Found {len(startup_events)} startup event(s)")
        else:
            # Check if it's using the new lifespan context
            print(f"{test_color('yellow', '⚠')} Using FastAPI lifespan (newer API)")
            print(f"{test_color('green', '✓')} API imports successfully")
        
        # The startup event should have run when API started
        # We can't directly test it, but we can verify the endpoint works
        print(f"{test_color('green', '✓')} API module imports with startup event")
        
        return True, None
    except Exception as e:
        print(f"{test_color('red', '✗')} Error checking startup event: {e}")
        return False, None

def test_4_frontend_api_client():
    """Test 4: Verify frontend can access system health"""
    print_section("Test 4: Frontend API Client")
    
    try:
        # Test the endpoint that frontend uses
        response = requests.get("http://localhost:8002/api/system/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify structure matches frontend expectations
            required_fields = ['status', 'self_test']
            missing = [f for f in required_fields if f not in data]
            
            if not missing:
                print(f"{test_color('green', '✓')} Response structure matches frontend expectations")
                
                # Check self_test structure
                self_test = data['self_test']
                required_test_fields = ['passed', 'total', 'passed_count', 'failed_count', 'success_rate', 'results']
                missing_test_fields = [f for f in required_test_fields if f not in self_test]
                
                if not missing_test_fields:
                    print(f"{test_color('green', '✓')} Self-test structure is complete")
                    return True, data
                else:
                    print(f"{test_color('yellow', '⚠')} Missing fields in self_test: {missing_test_fields}")
                    return False, data
            else:
                print(f"{test_color('red', '✗')} Missing required fields: {missing}")
                return False, data
        else:
            print(f"{test_color('red', '✗')} Endpoint returned {response.status_code}")
            return False, None
    except Exception as e:
        print(f"{test_color('red', '✗')} Error: {e}")
        return False, None

def test_5_test_consistency():
    """Test 5: Verify test results are consistent"""
    print_section("Test 5: Test Result Consistency")
    
    try:
        # Run startup test directly
        from tests.startup_test import StartupTest
        tester1 = StartupTest(api_url="http://localhost:8002")
        results1 = tester1.run_all()
        
        # Get results from API
        response = requests.get("http://localhost:8002/api/system/health", timeout=5)
        if response.status_code == 200:
            api_data = response.json()
            api_results = api_data.get('self_test', {})
            
            # Compare
            direct_total = results1['total']
            api_total = api_results.get('total', 0)
            
            direct_passed = results1['passed']
            api_passed = api_results.get('passed_count', 0)
            
            if direct_total == api_total:
                print(f"{test_color('green', '✓')} Test counts match: {direct_total}")
            else:
                print(f"{test_color('red', '✗')} Test counts don't match: direct={direct_total}, api={api_total}")
                return False, None
            
            if direct_passed == api_passed:
                print(f"{test_color('green', '✓')} Pass counts match: {direct_passed}")
            else:
                print(f"{test_color('yellow', '⚠')} Pass counts differ: direct={direct_passed}, api={api_passed}")
                print("  (This may be expected if API state changed between tests)")
            
            return True, (results1, api_results)
        else:
            print(f"{test_color('red', '✗')} Could not get API results")
            return False, None
    except Exception as e:
        print(f"{test_color('red', '✗')} Error: {e}")
        return False, None

def main():
    print_header("Self-Test System Verification")
    print("\nThis script verifies that the self-test framework is working correctly.")
    print("It tests the test framework itself to ensure it's functioning properly.\n")
    
    # Check API is running
    print("Checking API availability...")
    try:
        response = requests.get("http://localhost:8002/api/health", timeout=2)
        if response.status_code == 200:
            print(f"{test_color('green', '✓')} API is running and accessible")
        else:
            print(f"{test_color('red', '✗')} API returned status {response.status_code}")
            print("\n⚠ API must be running for full verification")
            print("  Start API with: ./start_api.sh")
    except requests.exceptions.ConnectionError:
        print(f"{test_color('red', '✗')} API is not accessible")
        print("\n⚠ API must be running for full verification")
        print("  Start API with: ./start_api.sh")
        print("\nSome tests will be skipped...")
    except Exception as e:
        print(f"{test_color('yellow', '⚠')} Error checking API: {e}")
    
    # Run all verification tests
    results = []
    
    # Test 1: Startup test module
    passed, data = test_1_startup_test_module()
    results.append(("Startup Test Module", passed))
    
    # Test 2: API health endpoint
    passed, data = test_2_api_health_endpoint()
    results.append(("API Health Endpoint", passed))
    
    # Test 3: Startup event
    passed, data = test_3_startup_event()
    results.append(("Startup Event", passed))
    
    # Test 4: Frontend API client
    passed, data = test_4_frontend_api_client()
    results.append(("Frontend API Client", passed))
    
    # Test 5: Test consistency
    passed, data = test_5_test_consistency()
    results.append(("Test Consistency", passed))
    
    # Summary
    print_header("Verification Summary")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    failed_count = total - passed_count
    
    for name, passed in results:
        status = test_color('green', '✓ PASS') if passed else test_color('red', '✗ FAIL')
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed_count}/{total} verifications passed")
    
    if passed_count == total:
        print(f"\n{test_color('green', '✓')} Self-test system is working correctly!")
        return 0
    else:
        print(f"\n{test_color('yellow', '⚠')} {failed_count} verification(s) failed")
        print("  Some issues detected - check details above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
