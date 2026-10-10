#!/usr/bin/env python3
"""
QUICK START TEST RUNNER
Run all test suites with a single command
"""
import subprocess
import sys
from datetime import datetime

def run_test_suite(script_name, description):
    """Run a single test suite"""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Script: {script_name}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*80}\n")
    
    result = subprocess.run([sys.executable, script_name])
    return result.returncode == 0

def main():
    print(f"\n{'='*80}")
    print("TRADING BOT TEST SUITE RUNNER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    suites = [
        ("test_bot_functionality.py", "Core Functionality Tests (17 tests)"),
        ("test_bot_advanced.py", "Advanced Edge Cases & Performance (18 tests)"),
        ("test_bug_fixes_unit.py", "Critical Bug Fix Verification (11 tests)"),
    ]
    
    results = {}
    
    for script, description in suites:
        try:
            passed = run_test_suite(script, description)
            results[description] = "PASSED" if passed else "FAILED"
        except Exception as e:
            print(f"ERROR: Could not run {script}: {e}")
            results[description] = "ERROR"
    
    # Print summary
    print(f"\n{'='*80}")
    print("TEST SUITE SUMMARY")
    print(f"{'='*80}\n")
    
    for description, status in results.items():
        symbol = "✓" if status == "PASSED" else "✗"
        print(f"{symbol} {status:10} - {description}")
    
    passed = sum(1 for s in results.values() if s == "PASSED")
    total = len(results)
    
    print(f"\n{'='*80}")
    print(f"Overall: {passed}/{total} test suites completed")
    print(f"Status: {'READY FOR DEPLOYMENT ✅' if passed == total else 'REVIEW REQUIRED ⚠'}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
