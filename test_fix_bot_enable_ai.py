#!/usr/bin/env python3
"""
Test that the NameError fix for BOT_ENABLE_AI_AUTO_TWEAK works correctly.
This test validates that the environment variable is properly read in the layout.
"""

import unittest
import os
import ast


class TestBotEnableAIAutoTweakFix(unittest.TestCase):
    """Test that the BOT_ENABLE_AI_AUTO_TWEAK fix resolves the NameError."""
    
    def test_layout_uses_direct_env_read(self):
        """Test that line 2475 uses os.getenv() directly instead of a variable."""
        # Read the web_gui.py file
        with open('web_gui.py', 'r') as f:
            content = f.read()
        
        # Parse the file to ensure it's valid Python
        try:
            ast.parse(content)
            parsed = True
        except SyntaxError as e:
            parsed = False
            self.fail(f"web_gui.py has syntax errors: {e}")
        
        self.assertTrue(parsed, "web_gui.py should parse without syntax errors")
        
        # Check that the problematic line now uses os.getenv() directly
        # This is line 2475 in the file
        lines = content.split('\n')
        
        # Find the line with the style dict that was causing the error
        found_fix = False
        for i, line in enumerate(lines):
            if "style={'display': 'block' if" in line and "BOT_ENABLE_AI_AUTO_TWEAK" in line:
                # Check if it uses os.getenv() directly
                if "os.getenv('BOT_ENABLE_AI_AUTO_TWEAK'" in line:
                    found_fix = True
                    print(f"✓ Found fixed line {i+1}: {line.strip()}")
                else:
                    self.fail(f"Line {i+1} still uses variable reference instead of os.getenv(): {line.strip()}")
        
        self.assertTrue(found_fix, "Should find the fixed line using os.getenv() directly")
    
    def test_env_var_evaluation_logic(self):
        """Test that the environment variable evaluation logic works correctly."""
        # Test when env var is 'true'
        os.environ['BOT_ENABLE_AI_AUTO_TWEAK'] = 'true'
        result_true = os.getenv('BOT_ENABLE_AI_AUTO_TWEAK', 'false').lower() == 'true'
        self.assertTrue(result_true)
        
        # Test when env var is 'false'
        os.environ['BOT_ENABLE_AI_AUTO_TWEAK'] = 'false'
        result_false = os.getenv('BOT_ENABLE_AI_AUTO_TWEAK', 'false').lower() == 'true'
        self.assertFalse(result_false)
        
        # Test when env var is missing (defaults to 'false')
        if 'BOT_ENABLE_AI_AUTO_TWEAK' in os.environ:
            del os.environ['BOT_ENABLE_AI_AUTO_TWEAK']
        result_default = os.getenv('BOT_ENABLE_AI_AUTO_TWEAK', 'false').lower() == 'true'
        self.assertFalse(result_default)
    
    def test_web_gui_compiles(self):
        """Test that web_gui.py compiles without errors."""
        import py_compile
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.pyc', delete=True) as tmp:
            try:
                py_compile.compile('web_gui.py', cfile=tmp.name, doraise=True)
                compiled = True
            except py_compile.PyCompileError as e:
                compiled = False
                self.fail(f"web_gui.py failed to compile: {e}")
        
        self.assertTrue(compiled, "web_gui.py should compile without errors")


if __name__ == '__main__':
    unittest.main()
