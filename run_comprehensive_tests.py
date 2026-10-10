#!/usr/bin/env python3
"""
Comprehensive Test Runner for market-pie5-bot
Runs all tests in the correct order with proper isolation and reporting
"""

import os
import sys
import time
import warnings
import subprocess
from datetime import datetime
from typing import List, Dict, Tuple

# Suppress pandas warnings before any imports
warnings.filterwarnings("ignore", message=r".*Timestamp\.utcnow.*")
warnings.filterwarnings("ignore", category=FutureWarning)

# Test configuration
TEST_ENV = {
    'ENABLE_PDT_RULES': 'false',
    'PAPER_TRADING_MODE': 'true',
    'SCHWAB_SANDBOX_MODE': 'true',
    'BOT_ENABLE_AI': 'false',
    'BOT_ENABLE_ML': 'false',
    'ENABLE_STOCK_SCREENER': 'false',
    'ENABLE_EMAIL_ALERTS': 'false',
}

# Test categories and their execution order
TEST_CATEGORIES = {
    'imports': {
        'name': 'Import & Module Tests',
        'tests': [
            'tests/backend/test_imports.py',
        ],
        'description': 'Verify all modules can be imported without circular dependencies',
        'required': True,
    },
    'unit': {
        'name': 'Unit Tests',
        'tests': [
            'test_indicators.py',
            'test_strategies_comprehensive.py',
            'test_risk_management_comprehensive.py',
            'test_portfolio_optimizer.py',
            'test_ml_signal_filter.py',
            'tests/backend/test_yfinance_mode.py',
        ],
        'description': 'Test individual modules in isolation',
        'required': True,
    },
    'integration': {
        'name': 'Integration Tests',
        'tests': [
            'test_trading_bot.py',
            'test_backtesting.py',
            'test_sentiment_analyzer.py',
            'tests/backend/test_bot_integration.py',
            'tests/backend/test_error_patterns.py',
        ],
        'description': 'Test module interactions and workflows',
        'required': True,
    },
    'api': {
        'name': 'API Tests',
        'tests': [
            'tests/backend/test_api_endpoints.py',
            'test_api_integration.py',
        ],
        'description': 'Test API endpoints (requires API server)',
        'required': False,
    },
    'e2e': {
        'name': 'End-to-End Tests',
        'tests': [
            'tests/backend/test_e2e_critical_path.py',
        ],
        'description': 'Test complete workflows',
        'required': False,
    },
    'gui': {
        'name': 'GUI Tests',
        'tests': [
            'test_gui_features.py',
            'tests/frontend/test_gui_data_points.py',
        ],
        'description': 'Test GUI functionality',
        'required': False,
    },
}


class TestRunner:
    """Comprehensive test runner with proper ordering and reporting"""
    
    def __init__(self, verbose: bool = True, stop_on_failure: bool = False):
        self.verbose = verbose
        self.stop_on_failure = stop_on_failure
        self.results: Dict[str, List[Dict]] = {}
        self.start_time = None
        self.end_time = None
        
    def setup_environment(self):
        """Set up test environment variables"""
        for key, value in TEST_ENV.items():
            os.environ[key] = value
            if self.verbose:
                print(f"  {key}={value}")
    
    def run_test_file(self, test_file: str) -> Tuple[bool, str, float]:
        """
        Run a single test file
        Returns: (success, output, duration)
        """
        if not os.path.exists(test_file):
            return False, f"Test file not found: {test_file}", 0.0
        
        start_time = time.time()
        
        # Determine test framework
        if test_file.startswith('tests/'):
            # Use pytest for tests/ directory
            cmd = [sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short']
        else:
            # Use unittest for root level tests
            cmd = [sys.executable, test_file]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                env=os.environ.copy()
            )
            duration = time.time() - start_time
            success = result.returncode == 0
            output = result.stdout + result.stderr
            return success, output, duration
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return False, "Test timeout after 120 seconds", duration
        except Exception as e:
            duration = time.time() - start_time
            return False, f"Test execution error: {str(e)}", duration
    
    def run_category(self, category: str, config: Dict) -> Dict:
        """Run all tests in a category"""
        print(f"\n{'='*80}")
        print(f"{config['name']}")
        print(f"{'='*80}")
        print(f"Description: {config['description']}")
        print(f"Required: {'Yes' if config['required'] else 'No'}")
        print()
        
        results = {
            'category': category,
            'name': config['name'],
            'tests': [],
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'duration': 0.0,
        }
        
        for test_file in config['tests']:
            print(f"Running: {test_file}")
            
            success, output, duration = self.run_test_file(test_file)
            
            test_result = {
                'file': test_file,
                'success': success,
                'duration': duration,
                'output': output if not success or self.verbose else '',
            }
            
            results['tests'].append(test_result)
            results['total'] += 1
            results['duration'] += duration
            
            if success:
                results['passed'] += 1
                print(f"  ✓ PASSED ({duration:.2f}s)")
            else:
                results['failed'] += 1
                print(f"  ✗ FAILED ({duration:.2f}s)")
                if not self.verbose and output:
                    # Print last 20 lines of output on failure
                    lines = output.split('\n')
                    print("  Last output lines:")
                    for line in lines[-20:]:
                        print(f"    {line}")
            
            # Stop on failure if requested and this is a required category
            if not success and self.stop_on_failure and config['required']:
                print(f"\n⚠ Stopping on failure (required test failed)")
                break
        
        # Print category summary
        print(f"\nCategory Summary:")
        print(f"  Total: {results['total']}")
        print(f"  Passed: {results['passed']}")
        print(f"  Failed: {results['failed']}")
        print(f"  Duration: {results['duration']:.2f}s")
        
        return results
    
    def run_all(self) -> bool:
        """Run all test categories in order"""
        self.start_time = datetime.now()
        
        print("="*80)
        print("COMPREHENSIVE SELF-TEST SUITE")
        print("="*80)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Setup environment
        print("Setting up test environment:")
        self.setup_environment()
        
        # Run test categories in order
        all_passed = True
        for category, config in TEST_CATEGORIES.items():
            results = self.run_category(category, config)
            self.results[category] = results
            
            # Check if we should stop
            if results['failed'] > 0:
                all_passed = False
                if self.stop_on_failure and config['required']:
                    break
        
        self.end_time = datetime.now()
        
        # Print overall summary
        self.print_summary()
        
        return all_passed
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("OVERALL TEST SUMMARY")
        print("="*80)
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_duration = 0.0
        
        for category, results in self.results.items():
            total_tests += results['total']
            total_passed += results['passed']
            total_failed += results['failed']
            total_duration += results['duration']
        
        print(f"\nCategories Run: {len(self.results)}")
        print(f"Total Tests: {total_tests}")
        if total_tests > 0:
            success_rate = total_passed / total_tests * 100
            print(f"Passed: {total_passed} ({success_rate:.1f}%)")
        else:
            print(f"Passed: {total_passed} (N/A - no tests run)")
        print(f"Failed: {total_failed}")
        print(f"Duration: {total_duration:.2f}s")
        
        if self.start_time and self.end_time:
            elapsed = (self.end_time - self.start_time).total_seconds()
            print(f"Elapsed Time: {elapsed:.2f}s")
        
        # Print failed tests
        if total_failed > 0:
            print("\nFailed Tests:")
            print("-" * 80)
            for category, results in self.results.items():
                for test in results['tests']:
                    if not test['success']:
                        print(f"  ✗ {test['file']} ({test['duration']:.2f}s)")
        
        print("="*80)
        
        if total_failed == 0:
            print("\n✓ All tests passed!")
        else:
            print(f"\n⚠ {total_failed} test(s) failed")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run comprehensive self-tests")
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Verbose output')
    parser.add_argument('-s', '--stop-on-failure', action='store_true',
                       help='Stop on first failure')
    parser.add_argument('-c', '--category', choices=list(TEST_CATEGORIES.keys()),
                       help='Run only specific category')
    
    args = parser.parse_args()
    
    runner = TestRunner(verbose=args.verbose, stop_on_failure=args.stop_on_failure)
    
    # If category specified, run only that category
    if args.category:
        config = TEST_CATEGORIES[args.category]
        runner.setup_environment()
        results = runner.run_category(args.category, config)
        success = results['failed'] == 0
    else:
        success = runner.run_all()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
