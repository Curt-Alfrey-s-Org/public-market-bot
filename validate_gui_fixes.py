#!/usr/bin/env python3
"""
Validation script for gui.py fixes
Verifies that key changes are present in the code
"""

import re
import sys


def validate_file_changes(filename):
    """Validate that key changes are present in gui.py"""
    
    with open(filename, 'r') as f:
        content = f.read()
    
    checks = []
    
    # Check 1: is_running_lock is initialized
    if 'self.is_running_lock = threading.Lock()' in content:
        checks.append(('✓', 'is_running_lock initialized'))
    else:
        checks.append(('✗', 'is_running_lock NOT initialized'))
    
    # Check 2: start_bot uses lock
    if 'with self.is_running_lock:' in content and 'def start_bot' in content:
        # Find start_bot method and check if it uses the lock
        start_bot_match = re.search(r'def start_bot\(self\):.*?(?=\n    def |\nclass |\Z)', content, re.DOTALL)
        if start_bot_match and 'with self.is_running_lock:' in start_bot_match.group(0):
            checks.append(('✓', 'start_bot uses lock for thread safety'))
        else:
            checks.append(('✗', 'start_bot does NOT use lock'))
    else:
        checks.append(('✗', 'start_bot does NOT use lock'))
    
    # Check 3: start_bot checks if thread is alive
    if 'if self.bot_thread and self.bot_thread.is_alive():' in content:
        checks.append(('✓', 'start_bot checks if previous thread is alive'))
    else:
        checks.append(('✗', 'start_bot does NOT check previous thread'))
    
    # Check 4: stop_bot joins thread
    if 'self.bot_thread.join(timeout=' in content:
        checks.append(('✓', 'stop_bot joins thread with timeout'))
    else:
        checks.append(('✗', 'stop_bot does NOT join thread'))
    
    # Check 5: run_bot checks is_running with lock
    run_bot_match = re.search(r'def run_bot\(self\):.*?(?=\n    def |\nclass |\Z)', content, re.DOTALL)
    if run_bot_match and 'with self.is_running_lock:' in run_bot_match.group(0):
        checks.append(('✓', 'run_bot checks is_running with lock'))
    else:
        checks.append(('✗', 'run_bot does NOT check is_running with lock'))
    
    # Check 6: PDT tracking added in run_bot
    if 'self.pdt_tracker.add_day_trade(symbol)' in content:
        checks.append(('✓', 'PDT day trade tracking added'))
    else:
        checks.append(('✗', 'PDT day trade tracking NOT added'))
    
    # Check 7: PDT tracking logs message
    if '[PDT] Day trade recorded' in content:
        checks.append(('✓', 'PDT tracking includes log message'))
    else:
        checks.append(('✗', 'PDT tracking does NOT include log message'))
    
    # Check 8: export_settings has nested try-catch for JSON
    export_match = re.search(r'def export_settings\(self\):.*?(?=\n    def |\nclass |\Z)', content, re.DOTALL)
    if export_match:
        export_content = export_match.group(0)
        # Check for nested try-catch with json.dump
        if 'with open(filename' in export_content and 'json.dump(settings, f' in export_content:
            # Check if there's a try block wrapping the open/json.dump
            if export_content.count('try:') >= 2:
                checks.append(('✓', 'export_settings has nested exception handling'))
            else:
                checks.append(('⚠', 'export_settings may need better exception nesting'))
        else:
            checks.append(('✗', 'export_settings structure not found'))
    else:
        checks.append(('✗', 'export_settings method not found'))
    
    # Check 9: export_settings handles ValueError
    if 'except ValueError as e:' in content and 'Cannot serialize settings to JSON' in content:
        checks.append(('✓', 'export_settings handles JSON encoding errors'))
    else:
        checks.append(('⚠', 'export_settings may not handle JSON encoding errors'))
    
    # Check 10: export_settings handles IOError separately
    export_match = re.search(r'def export_settings\(self\):.*?(?=\n    def |\nclass |\Z)', content, re.DOTALL)
    if export_match and 'except IOError as e:' in export_match.group(0):
        checks.append(('✓', 'export_settings handles IOError separately'))
    else:
        checks.append(('⚠', 'export_settings may not handle IOError separately'))
    
    # Print results
    print("\n" + "="*70)
    print("GUI.PY VALIDATION REPORT")
    print("="*70)
    
    passed = 0
    warned = 0
    failed = 0
    
    for status, message in checks:
        print(f"{status} {message}")
        if status == '✓':
            passed += 1
        elif status == '⚠':
            warned += 1
        else:
            failed += 1
    
    print("\n" + "-"*70)
    print(f"Results: {passed} passed, {warned} warnings, {failed} failed")
    print("-"*70 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = validate_file_changes('gui.py')
    sys.exit(0 if success else 1)
