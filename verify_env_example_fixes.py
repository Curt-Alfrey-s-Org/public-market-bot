#!/usr/bin/env python3
"""
Verify that .env.example fixes are correct:
1. All booleans use lowercase 'true'/'false'
2. ENABLE_PDT_RULES has deprecation notice
3. BACKTEST_MODE and SWING_HOLD_MIN_DAYS are present
"""

import re

def verify_env_example_fixes():
    """Verify all fixes to .env.example"""
    print("Verifying .env.example fixes...")
    print("=" * 60)
    
    with open('.env.example', 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    issues = []
    warnings = []
    successes = []
    
    # Check 1: Find any boolean values with capital T/F
    print("\n1. Checking boolean consistency...")
    boolean_pattern = re.compile(r'^([A-Z_]+)=(True|False)$', re.MULTILINE)
    bad_booleans = boolean_pattern.findall(content)
    
    if bad_booleans:
        for var, value in bad_booleans:
            issues.append(f"  ❌ {var} uses '{value}' instead of lowercase")
    else:
        successes.append("  ✓ All booleans use lowercase 'true'/'false'")
    
    # Check 2: Verify ENABLE_PDT_RULES has deprecation notice
    print("\n2. Checking ENABLE_PDT_RULES deprecation notice...")
    pdt_section_found = False
    deprecation_found = False
    
    for i, line in enumerate(lines):
        if 'ENABLE_PDT_RULES' in line and not line.strip().startswith('#'):
            pdt_section_found = True
            # Check previous lines for DEPRECATED notice
            for j in range(max(0, i-10), i):
                if 'DEPRECATED' in lines[j].upper():
                    deprecation_found = True
                    break
    
    if pdt_section_found and deprecation_found:
        successes.append("  ✓ ENABLE_PDT_RULES has DEPRECATED notice")
    elif pdt_section_found and not deprecation_found:
        issues.append("  ❌ ENABLE_PDT_RULES missing DEPRECATED notice")
    
    # Check 3: Verify critical variables are present
    print("\n3. Checking critical environment variables...")
    required_vars = {
        'BACKTEST_MODE': False,
        'SWING_HOLD_MIN_DAYS': False,
    }
    
    for line in lines:
        for var in required_vars:
            if line.startswith(f"{var}="):
                required_vars[var] = True
    
    for var, found in required_vars.items():
        if found:
            successes.append(f"  ✓ {var} is present")
        else:
            issues.append(f"  ❌ {var} is missing")
    
    # Check 4: Verify specific boolean values
    print("\n4. Checking specific boolean variables...")
    bool_vars_to_check = [
        'DYNAMIC_STOP_ENABLED',
        'PARTIAL_EXIT_ENABLED',
        'ENABLE_ALERTS',
        'PAPER_TRADING_MODE',
        'SCHWAB_ENCRYPT_TOKEN',
    ]
    
    for var in bool_vars_to_check:
        pattern = re.compile(f'^{var}=(true|false)$', re.MULTILINE)
        match = pattern.search(content)
        if match:
            successes.append(f"  ✓ {var} uses lowercase '{match.group(1)}'")
        else:
            # Check if it uses uppercase
            bad_pattern = re.compile(f'^{var}=(True|False)$', re.MULTILINE)
            bad_match = bad_pattern.search(content)
            if bad_match:
                issues.append(f"  ❌ {var} uses '{bad_match.group(1)}' (should be lowercase)")
    
    # Print results
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    
    if successes:
        print("\n✓ PASSED:")
        for success in successes:
            print(success)
    
    if warnings:
        print("\n⚠ WARNINGS:")
        for warning in warnings:
            print(warning)
    
    if issues:
        print("\n❌ FAILED:")
        for issue in issues:
            print(issue)
        print("\nFixes needed!")
        return False
    else:
        print("\n✓✓✓ All checks passed! ✓✓✓")
        return True

if __name__ == '__main__':
    import sys
    success = verify_env_example_fixes()
    sys.exit(0 if success else 1)
