#!/usr/bin/env python3
"""
Test the self-test framework itself
Verifies that the test framework works correctly
"""

import sys
import os
import subprocess
import time
import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_framework_imports():
    """Test that framework modules can be imported"""
    try:
        from tests.framework.base_test import BaseTestModule, TestStatus, TestResult
        from tests.framework.plugin_loader import PluginLoader
        from tests.backend.test_api_endpoints import APIEndpointsTest
        from tests.backend.test_bot_integration import BotIntegrationTest
        from tests.frontend.test_gui_data_points import GUIDataPointsTest
        from tests.frontend.test_gui_visual import GUIVisualTest
        print("✓ Framework imports successful")
        return True
    except Exception as e:
        print(f"✗ Framework import failed: {e}")
        return False

def test_api_startup():
    """Test that API can be started"""
    try:
        from tests.framework.base_test import BaseTestModule
        
        # Try to start API
        proc = subprocess.Popen(
            ['python3', '-m', 'uvicorn', 'api.main:app', '--host', '127.0.0.1', '--port', '8002'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        # Wait for API to start
        time.sleep(3)
        
        # Test connection
        try:
            response = requests.get('http://127.0.0.1:8002/api/health', timeout=2)
            if response.status_code == 200:
                print("✓ API can be started and responds")
                proc.terminate()
                proc.wait(timeout=2)
                return True
            else:
                print(f"✗ API returned status {response.status_code}")
                proc.terminate()
                proc.wait(timeout=2)
                return False
        except requests.exceptions.ConnectionError:
            print("⚠ API started but not accessible (may be permission issue)")
            proc.terminate()
            proc.wait(timeout=2)
            return False
        except Exception as e:
            print(f"✗ API test failed: {e}")
            proc.terminate()
            proc.wait(timeout=2)
            return False
    except Exception as e:
        print(f"✗ API startup test failed: {e}")
        return False

def test_runner_execution():
    """Test that runner can execute"""
    try:
        result = subprocess.run(
            ['python3', 'tests/runner.py', '--help'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            timeout=10
        )
        if result.returncode == 0 and 'usage:' in result.stdout:
            print("✓ Test runner executes correctly")
            return True
        else:
            print(f"✗ Test runner execution failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Test runner execution failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Testing Self-Test Framework")
    print("=" * 60)
    print()
    
    results = []
    
    print("1. Testing framework imports...")
    results.append(("Imports", test_framework_imports()))
    print()
    
    print("2. Testing API startup...")
    results.append(("API Startup", test_api_startup()))
    print()
    
    print("3. Testing runner execution...")
    results.append(("Runner Execution", test_runner_execution()))
    print()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ Self-test framework is working correctly!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed - framework may have issues")
        return 1

if __name__ == '__main__':
    sys.exit(main())
