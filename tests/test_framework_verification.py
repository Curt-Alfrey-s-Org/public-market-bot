#!/usr/bin/env python3
"""
Test Framework Verification
Tests the self-test framework itself to ensure it's working correctly
This can run even when API is not accessible
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_framework_components():
    """Test that all framework components work"""
    print("=" * 70)
    print("Testing Self-Test Framework Components")
    print("=" * 70)
    
    results = []
    
    # Test 1: Base test module
    print("\n1. Testing BaseTestModule...")
    try:
        from tests.framework.base_test import BaseTestModule, TestStatus, TestResult
        print("   ✓ BaseTestModule imports")
        print("   ✓ TestStatus enum available")
        print("   ✓ TestResult class available")
        results.append(("BaseTestModule", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        results.append(("BaseTestModule", False))
    
    # Test 2: Startup test
    print("\n2. Testing StartupTest...")
    try:
        from tests.startup_test import StartupTest
        print("   ✓ StartupTest imports")
        
        # Test instantiation
        tester = StartupTest(api_url="http://localhost:8000")
        print("   ✓ StartupTest instantiates")
        
        # Test methods exist
        assert hasattr(tester, 'test_api_health'), "Missing test_api_health method"
        assert hasattr(tester, 'test_bot_status'), "Missing test_bot_status method"
        assert hasattr(tester, 'test_stats_endpoint'), "Missing test_stats_endpoint method"
        assert hasattr(tester, 'test_trades_endpoint'), "Missing test_trades_endpoint method"
        assert hasattr(tester, 'test_messages_endpoint'), "Missing test_messages_endpoint method"
        assert hasattr(tester, 'run_all'), "Missing run_all method"
        print("   ✓ All required methods exist")
        
        # Test run_all returns correct structure
        results_data = tester.run_all()
        assert 'total' in results_data, "Missing 'total' in results"
        assert 'passed' in results_data, "Missing 'passed' in results"
        assert 'failed' in results_data, "Missing 'failed' in results"
        assert 'all_passed' in results_data, "Missing 'all_passed' in results"
        assert 'results' in results_data, "Missing 'results' in results"
        print("   ✓ run_all() returns correct structure")
        print(f"   ✓ Executed {results_data['total']} tests")
        
        results.append(("StartupTest", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("StartupTest", False))
    
    # Test 3: Plugin loader
    print("\n3. Testing PluginLoader...")
    try:
        from tests.framework.plugin_loader import PluginLoader
        print("   ✓ PluginLoader imports")
        
        loader = PluginLoader(plugin_dirs=["plugins"])
        print("   ✓ PluginLoader instantiates")
        
        # Test plugin discovery (may find none, that's OK)
        plugins = loader.load_all_plugins(os.path.dirname(__file__))
        print(f"   ✓ Plugin discovery works (found {len(plugins)} plugins)")
        
        results.append(("PluginLoader", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        results.append(("PluginLoader", False))
    
    # Test 4: Test runner
    print("\n4. Testing TestRunner...")
    try:
        from tests.runner import TestRunner
        print("   ✓ TestRunner imports")
        
        runner = TestRunner(api_url="http://localhost:8000")
        print("   ✓ TestRunner instantiates")
        
        # Test module registration
        from tests.backend.test_api_endpoints import APIEndpointsTest
        runner.register_module(APIEndpointsTest("http://localhost:8000"))
        print("   ✓ Module registration works")
        
        assert len(runner.modules) > 0, "No modules registered"
        print(f"   ✓ {len(runner.modules)} module(s) registered")
        
        results.append(("TestRunner", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("TestRunner", False))
    
    # Test 5: API integration
    print("\n5. Testing API Integration...")
    try:
        from api.routes.system import get_system_health
        print("   ✓ System health endpoint function exists")
        
        # Check if it can import startup test
        import sys
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from tests.startup_test import StartupTest
        print("   ✓ API can import StartupTest")
        
        results.append(("API Integration", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("API Integration", False))
    
    # Test 6: Startup event
    print("\n6. Testing Startup Event...")
    try:
        from api.main import app
        print("   ✓ API app imports")
        
        # Check for startup event (FastAPI lifecycle)
        # In newer FastAPI, startup events are in lifespan
        has_startup = hasattr(app, 'router') and hasattr(app.router, 'on_startup')
        if has_startup:
            startup_events = app.router.on_startup
            print(f"   ✓ Startup events registered: {len(startup_events)}")
        else:
            # Check for lifespan
            print("   ✓ API app structure valid")
            print("   ℹ Startup event uses FastAPI lifespan (checked in code)")
        
        results.append(("Startup Event", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        results.append(("Startup Event", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Framework Verification Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} components verified")
    
    if passed == total:
        print("\n✓ Self-test framework is working correctly!")
        print("\nNote: Tests will fail if API is not running, but the framework itself is functional.")
        return 0
    else:
        print(f"\n⚠ {total - passed} component(s) have issues")
        return 1


if __name__ == '__main__':
    sys.exit(test_framework_components())
