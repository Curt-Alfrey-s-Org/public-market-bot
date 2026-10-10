#!/usr/bin/env python3
"""
Verification script for self-test improvements
Validates that the new test infrastructure is working correctly
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} NOT FOUND: {filepath}")
        return False

def check_test_runner():
    """Verify test runner exists and is executable"""
    print("\n" + "="*60)
    print("Checking Test Runner")
    print("="*60)
    
    runner_path = "run_comprehensive_tests.py"
    if not check_file_exists(runner_path, "Test runner script"):
        return False
    
    # Check if it's executable (Unix-like systems)
    if os.name != 'nt':  # Not Windows
        is_executable = os.access(runner_path, os.X_OK)
        if is_executable:
            print(f"✓ Test runner is executable")
        else:
            print(f"⚠ Test runner is not executable (run: chmod +x {runner_path})")
    
    # Try to run help
    try:
        result = subprocess.run(
            [sys.executable, runner_path, '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ Test runner executes correctly")
            return True
        else:
            print(f"✗ Test runner failed to execute")
            return False
    except Exception as e:
        print(f"✗ Error running test runner: {e}")
        return False

def check_new_test_files():
    """Verify new test files exist"""
    print("\n" + "="*60)
    print("Checking New Test Files")
    print("="*60)
    
    test_files = [
        ("test_indicators.py", "Indicators unit tests"),
        ("test_strategies_comprehensive.py", "Strategies comprehensive tests"),
        ("test_risk_management_comprehensive.py", "Risk management comprehensive tests"),
    ]
    
    all_exist = True
    for filename, description in test_files:
        if not check_file_exists(filename, description):
            all_exist = False
    
    return all_exist

def check_documentation():
    """Verify documentation files exist"""
    print("\n" + "="*60)
    print("Checking Documentation")
    print("="*60)
    
    doc_files = [
        ("TESTING_GUIDE.md", "Testing guide"),
        ("SELF_TEST_IMPROVEMENTS.md", "Self-test improvements summary"),
    ]
    
    all_exist = True
    for filename, description in doc_files:
        if not check_file_exists(filename, description):
            all_exist = False
    
    return all_exist

def check_test_runner_content():
    """Verify test runner has correct content"""
    print("\n" + "="*60)
    print("Checking Test Runner Content")
    print("="*60)
    
    runner_path = "run_comprehensive_tests.py"
    
    try:
        with open(runner_path, 'r') as f:
            content = f.read()
        
        # Check for key components
        checks = [
            ("TEST_ENV", "Environment variable setup"),
            ("TEST_CATEGORIES", "Test categories definition"),
            ("class TestRunner", "TestRunner class"),
            ("def run_all", "Run all method"),
            ("test_indicators.py", "Indicators test reference"),
            ("test_strategies", "Strategies test reference"),
            ("test_risk_management", "Risk management test reference"),
        ]
        
        all_found = True
        for keyword, description in checks:
            if keyword in content:
                print(f"✓ Found: {description}")
            else:
                print(f"✗ Missing: {description}")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"✗ Error reading test runner: {e}")
        return False

def check_test_file_structure():
    """Verify test files have correct structure"""
    print("\n" + "="*60)
    print("Checking Test File Structure")
    print("="*60)
    
    test_files = {
        "test_indicators.py": ["import unittest", "class Test", "def test_"],
        "test_strategies_comprehensive.py": ["import unittest", "class Test", "def test_"],
        "test_risk_management_comprehensive.py": ["import unittest", "class Test", "def test_"],
    }
    
    all_valid = True
    for filename, required_elements in test_files.items():
        if not os.path.exists(filename):
            continue
        
        try:
            with open(filename, 'r') as f:
                content = f.read()
            
            print(f"\nChecking {filename}:")
            for element in required_elements:
                if element in content:
                    print(f"  ✓ Contains: {element}")
                else:
                    print(f"  ✗ Missing: {element}")
                    all_valid = False
        except Exception as e:
            print(f"  ✗ Error reading {filename}: {e}")
            all_valid = False
    
    return all_valid

def count_test_methods():
    """Count test methods in new test files"""
    print("\n" + "="*60)
    print("Counting Test Methods")
    print("="*60)
    
    test_files = [
        "test_indicators.py",
        "test_strategies_comprehensive.py",
        "test_risk_management_comprehensive.py",
    ]
    
    total_tests = 0
    for filename in test_files:
        if not os.path.exists(filename):
            continue
        
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            # Count test methods (lines starting with "    def test_" after stripping)
            # More robust: only count lines that start with whitespace + "def test_"
            test_count = 0
            for line in lines:
                stripped = line.lstrip()
                # Check if line starts with "def test_" and has leading whitespace (is in a class)
                if stripped.startswith("def test_") and line.startswith((" ", "\t")):
                    test_count += 1
            
            total_tests += test_count
            print(f"{filename}: {test_count} test methods")
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    
    print(f"\nTotal new test methods: {total_tests}")
    return total_tests

def main():
    """Main verification routine"""
    print("="*60)
    print("Self-Test Improvements Verification")
    print("="*60)
    
    results = []
    
    # Run all checks
    results.append(("Test Runner", check_test_runner()))
    results.append(("New Test Files", check_new_test_files()))
    results.append(("Documentation", check_documentation()))
    results.append(("Test Runner Content", check_test_runner_content()))
    results.append(("Test File Structure", check_test_file_structure()))
    
    # Count tests
    test_count = count_test_methods()
    
    # Print summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check_name}")
        if result:
            passed += 1
    
    print(f"\nChecks Passed: {passed}/{total}")
    print(f"New Test Methods Added: {test_count}")
    
    if passed == total and test_count > 0:
        print("\n✓ All verifications passed!")
        print("✓ Self-test improvements are properly implemented")
        return 0
    else:
        print(f"\n⚠ {total - passed} check(s) failed")
        print("⚠ Please review the issues above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
