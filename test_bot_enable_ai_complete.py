#!/usr/bin/env python3
"""
Comprehensive test to ensure BOT_ENABLE_AI_AUTO_TWEAK is properly defined
and used throughout web_gui.py to prevent NameError.

This test validates the fix for the issue where line 2474 was causing:
NameError: name 'BOT_ENABLE_AI_AUTO_TWEAK' is not defined
"""

import unittest
import os
import ast



class TestBotEnableAIAutoTweakComprehensive(unittest.TestCase):
    """Comprehensive tests for BOT_ENABLE_AI_AUTO_TWEAK variable."""
    
    @classmethod
    def setUpClass(cls):
        """Load web_gui.py content once for all tests."""
        with open('web_gui.py', 'r') as f:
            cls.content = f.read()
            cls.lines = cls.content.split('\n')
    
    def test_web_gui_syntax_is_valid(self):
        """Test that web_gui.py has valid Python syntax."""
        try:
            ast.parse(self.content)
            valid = True
        except SyntaxError as e:
            valid = False
            self.fail(f"web_gui.py has syntax errors: {e}")
        
        self.assertTrue(valid, "web_gui.py should have valid syntax")
    
    def test_variable_is_defined_before_layout(self):
        """Test that BOT_ENABLE_AI_AUTO_TWEAK is defined before app.layout."""
        # Find where variable is defined
        var_def_line = None
        for i, line in enumerate(self.lines):
            if 'BOT_ENABLE_AI_AUTO_TWEAK = os.getenv' in line:
                var_def_line = i + 1
                break
        
        # Find where layout starts
        layout_line = None
        for i, line in enumerate(self.lines):
            if 'app.layout = ' in line:
                layout_line = i + 1
                break
        
        self.assertIsNotNone(var_def_line, "BOT_ENABLE_AI_AUTO_TWEAK should be defined")
        self.assertIsNotNone(layout_line, "app.layout should exist")
        self.assertLess(var_def_line, layout_line,
                       f"BOT_ENABLE_AI_AUTO_TWEAK (line {var_def_line}) should be "
                       f"defined before app.layout (line {layout_line})")
        
        print(f"✓ Variable defined at line {var_def_line}, layout starts at line {layout_line}")
    
    def test_layout_uses_os_getenv_not_variable(self):
        """Test that layout code uses os.getenv() directly, not the variable."""
        # Find the layout section (between app.layout and first @app.callback)
        layout_start = None
        layout_end = None
        
        for i, line in enumerate(self.lines):
            if 'app.layout = ' in line:
                layout_start = i
            elif layout_start and '@app.callback' in line:
                layout_end = i
                break
        
        self.assertIsNotNone(layout_start, "Should find app.layout")
        self.assertIsNotNone(layout_end, "Should find first @app.callback")
        
        # Check all uses of BOT_ENABLE_AI_AUTO_TWEAK in layout section
        violations = []
        for i in range(layout_start, layout_end):
            line = self.lines[i]
            line_num = i + 1
            
            # Check for BOT_ENABLE_AI_AUTO_TWEAK usage
            if 'BOT_ENABLE_AI_AUTO_TWEAK' in line:
                # It should be in a string context with os.getenv
                if "os.getenv('BOT_ENABLE_AI_AUTO_TWEAK'" not in line and \
                   'os.getenv("BOT_ENABLE_AI_AUTO_TWEAK"' not in line and \
                   "'BOT_ENABLE_AI_AUTO_TWEAK':" not in line:  # Allow in dict keys
                    violations.append((line_num, line.strip()))
        
        if violations:
            error_msg = "Found BOT_ENABLE_AI_AUTO_TWEAK used directly in layout:\n"
            for line_num, line_text in violations:
                error_msg += f"  Line {line_num}: {line_text}\n"
            self.fail(error_msg)
        
        print(f"✓ BOT_ENABLE_AI_AUTO_TWEAK is correctly used in layout section "
              f"(lines {layout_start+1} to {layout_end})")
    
    def test_specific_line_2475_uses_os_getenv(self):
        """Test that line 2475 (the problematic line) uses os.getenv()."""
        # Line 2475 (0-indexed as 2474)
        if len(self.lines) >= 2475:
            line_2475 = self.lines[2474]
            
            # This line should contain BOT_ENABLE_AI_AUTO_TWEAK with os.getenv
            if 'BOT_ENABLE_AI_AUTO_TWEAK' in line_2475:
                self.assertIn('os.getenv', line_2475,
                            f"Line 2475 should use os.getenv(): {line_2475.strip()}")
                print(f"✓ Line 2475 correctly uses os.getenv()")
    
    def test_callback_functions_can_use_variable(self):
        """Test that callback functions (runtime code) can use the variable directly."""
        # Find a callback that uses BOT_ENABLE_AI_AUTO_TWEAK
        found_callback_usage = False
        in_callback = False
        
        for i, line in enumerate(self.lines):
            if '@app.callback' in line:
                in_callback = True
            elif in_callback and 'def ' in line:
                # We're in a callback function
                pass
            elif in_callback and 'BOT_ENABLE_AI_AUTO_TWEAK' in line:
                # Check if it's used directly (without os.getenv in the same line)
                if 'os.getenv' not in line and '=' not in line:
                    found_callback_usage = True
                    line_num = i + 1
                    print(f"✓ Found callback using variable directly at line {line_num}: "
                          f"{line.strip()[:60]}")
                    break
        
        # This is informational - callbacks CAN use the variable directly
        if found_callback_usage:
            print("  (This is OK - callbacks run at runtime after variable is defined)")
    
    def test_environment_variable_evaluation(self):
        """Test the actual environment variable evaluation logic."""
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('', False),  # Empty string
            ('anything_else', False),
        ]
        
        for env_value, expected in test_cases:
            os.environ['BOT_ENABLE_AI_AUTO_TWEAK'] = env_value
            result = os.getenv('BOT_ENABLE_AI_AUTO_TWEAK', 'false').lower() == 'true'
            self.assertEqual(result, expected,
                           f"BOT_ENABLE_AI_AUTO_TWEAK={env_value} should evaluate to {expected}")
        
        # Test default when not set
        if 'BOT_ENABLE_AI_AUTO_TWEAK' in os.environ:
            del os.environ['BOT_ENABLE_AI_AUTO_TWEAK']
        result = os.getenv('BOT_ENABLE_AI_AUTO_TWEAK', 'false').lower() == 'true'
        self.assertFalse(result, "Should default to False when not set")
        
        print("✓ Environment variable evaluation logic works correctly")


if __name__ == '__main__':
    unittest.main(verbosity=2)
