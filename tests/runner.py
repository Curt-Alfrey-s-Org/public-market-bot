#!/usr/bin/env python3
"""
Comprehensive Self-Test Runner
Runs all test modules and generates report
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.framework.base_test import BaseTestModule, TestStatus
from tests.framework.plugin_loader import PluginLoader
from tests.backend.test_imports import ImportValidationTest
from tests.backend.test_api_endpoints import APIEndpointsTest
from tests.backend.test_bot_integration import BotIntegrationTest
from tests.backend.test_error_patterns import ErrorPatternsTest
from tests.backend.test_e2e_critical_path import E2ECriticalPathTest
from tests.backend.test_yfinance_mode import YfinanceModeTest
from tests.backend.test_yfinance_regression import YfinanceRegressionTest
from tests.frontend.test_gui_data_points import GUIDataPointsTest
from tests.frontend.test_gui_visual import GUIVisualTest
from tests.frontend.test_gui_interactions import GUIInteractionTest


class TestRunner:
    """Main test runner"""
    
    def __init__(self, api_url: str = "http://localhost:8002", frontend_url: str = "http://localhost:5173"):
        self.api_url = api_url
        self.frontend_url = frontend_url
        self.modules: list[BaseTestModule] = []
        self.results = []
        self.start_time = None
        self.end_time = None
    
    def register_module(self, module: BaseTestModule):
        """Register a test module"""
        self.modules.append(module)
    
    def load_plugins(self, plugin_dir: str = None):
        """Load plugin test modules"""
        if not plugin_dir:
            plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
        
        loader = PluginLoader(plugin_dirs=["plugins"])
        plugins = loader.load_all_plugins(plugin_dir)
        
        for plugin_name, plugin_class in plugins.items():
            try:
                instance = plugin_class(api_base_url=self.api_url)
                self.register_module(instance)
                print(f"Loaded plugin: {plugin_name}")
            except Exception as e:
                print(f"Failed to load plugin {plugin_name}: {e}")
    
    def check_api_available(self):
        """Check if API is available before running tests"""
        try:
            import requests
            response = requests.get(f"{self.api_url}/api/health", timeout=2)
            if response.status_code == 200:
                return True, None
            else:
                return False, f"API returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to API. Is it running? Start with: ./start_api.sh or ./fix_api_connection.sh"
        except Exception as e:
            return False, f"Error checking API: {str(e)}"
    
    def run_all(self):
        """Run all registered test modules"""
        self.start_time = datetime.now()
        print("=" * 80)
        print("COMPREHENSIVE SELF-TEST SUITE")
        print("=" * 80)
        print(f"API URL: {self.api_url}")
        print(f"Frontend URL: {self.frontend_url}")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        # Check API availability
        api_available, api_error = self.check_api_available()
        if not api_available:
            print("⚠ WARNING: API is not accessible")
            print(f"   {api_error}")
            print("   Tests will fail if API is required.")
            print("   Start API with: ./start_api.sh or ./fix_api_connection.sh")
            print()
        else:
            print("✓ API is accessible")
            print()
        
        # Register default modules only if none registered yet (e.g. --yfinance-only registers its own)
        if not self.modules:
            self.register_module(ImportValidationTest(self.api_url))
            self.register_module(YfinanceModeTest(self.api_url))  # yfinance unit tests (no API)
            self.register_module(YfinanceRegressionTest(self.api_url))  # yfinance regression (no API)
            self.register_module(APIEndpointsTest(self.api_url))
            self.register_module(BotIntegrationTest(self.api_url))
            self.register_module(ErrorPatternsTest(self.api_url))  # Test for previously found errors
            self.register_module(E2ECriticalPathTest(self.api_url))  # Phase 8.2 E2E critical path (API)
            self.register_module(GUIDataPointsTest(self.api_url))
            self.register_module(GUIVisualTest(self.api_url, self.frontend_url))
            self.register_module(GUIInteractionTest(self.api_url, self.frontend_url))
        
        # Load plugins
        try:
            self.load_plugins()
        except Exception as e:
            print(f"Warning: Could not load plugins: {e}")
        
        # Run all modules
        all_results = []
        for module in self.modules:
            print(f"\n{'=' * 80}")
            print(f"Running: {module.name}")
            print(f"{'=' * 80}")
            
            module.start_time = datetime.now()
            try:
                results = module.run()
                module.end_time = datetime.now()
                all_results.extend(results)
                
                # Print module summary
                summary = module.get_summary()
                print(f"\nModule Summary: {module.name}")
                print(f"  Total: {summary['total']}")
                print(f"  Passed: {summary['passed']} ({summary['success_rate']:.1f}%)")
                print(f"  Failed: {summary['failed']}")
                print(f"  Warnings: {summary['warnings']}")
                print(f"  Duration: {summary['duration']:.2f}s")
                
            except Exception as e:
                print(f"ERROR: Module {module.name} failed: {e}")
                import traceback
                traceback.print_exc()
        
        self.end_time = datetime.now()
        self.results = all_results
        
        return all_results
    
    def generate_report(self, output_file: str = None):
        """Generate test report"""
        if not output_file:
            output_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Calculate summary
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        warnings = sum(1 for r in self.results if r.status == TestStatus.WARN)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIP)
        
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        
        report = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "skipped": skipped,
                "success_rate": (passed / total * 100) if total > 0 else 0,
                "duration": duration,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
            },
            "modules": [
                {
                    "name": module.name,
                    "summary": module.get_summary()
                }
                for module in self.modules
            ],
            "results": [r.to_dict() for r in self.results]
        }
        
        # Save JSON report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({report['summary']['success_rate']:.1f}%)")
        print(f"Failed: {failed}")
        print(f"Warnings: {warnings}")
        print(f"Skipped: {skipped}")
        print(f"Duration: {duration:.2f}s")
        print("=" * 80)
        
        # Print failed tests
        if failed > 0:
            print("\nFAILED TESTS:")
            print("-" * 80)
            for result in self.results:
                if result.status == TestStatus.FAIL:
                    print(f"  ✗ {result.name}")
                    print(f"    {result.message}")
        
        # Print skipped tests (e.g. API deps not installed)
        if skipped > 0:
            print("\nSKIPPED TESTS:")
            print("-" * 80)
            for result in self.results:
                if result.status == TestStatus.SKIP:
                    print(f"  ○ {result.name}")
                    print(f"    {result.message}")
        
        # Print warnings
        if warnings > 0:
            print("\nWARNINGS:")
            print("-" * 80)
            for result in self.results:
                if result.status == TestStatus.WARN:
                    print(f"  ⚠ {result.name}")
                    print(f"    {result.message}")
        
        print(f"\nFull report saved to: {output_file}")
        
        return report


def main():
    parser = argparse.ArgumentParser(description="Run comprehensive self-test suite")
    parser.add_argument("--api-url", default="http://localhost:8002", help="API base URL (8002 when 8000 used by Yacht)")
    parser.add_argument("--frontend-url", default="http://localhost:5173", help="Frontend URL")
    parser.add_argument("--output", help="Output file for test report")
    parser.add_argument("--plugins-dir", help="Directory containing plugin tests")
    parser.add_argument("--yfinance-only", action="store_true", help="Run only yfinance-related tests (unit + sim + fallback alert)")
    
    args = parser.parse_args()
    
    if args.yfinance_only:
        # Run root unittest scripts then runner with only yfinance + imports
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(project_root)
        failed = 0
        for script in ["test_yfinance_sim.py", "test_yfinance_fallback_alert.py"]:
            path = os.path.join(project_root, script)
            if os.path.isfile(path):
                print(f"\n{'='*60}\nRunning {script}\n{'='*60}")
                r = subprocess.run([sys.executable, path], check=False)
                if r.returncode != 0:
                    failed += 1
            else:
                print(f"Skip (not found): {script}")
        runner = TestRunner(api_url=args.api_url, frontend_url=args.frontend_url)
        runner.register_module(ImportValidationTest(runner.api_url))
        runner.register_module(YfinanceModeTest(runner.api_url))
        runner.register_module(YfinanceRegressionTest(runner.api_url))
        runner.run_all()
        report = runner.generate_report(args.output)
        failed += report["summary"]["failed"]
        sys.exit(1 if failed > 0 else 0)
    
    runner = TestRunner(api_url=args.api_url, frontend_url=args.frontend_url)
    
    try:
        runner.run_all()
        report = runner.generate_report(args.output)
        
        # Exit with error code if tests failed
        if report["summary"]["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
