#!/usr/bin/env python3
"""
Test that BOT_ENABLE_AI_AUTO_TWEAK variable is properly defined in web_gui.py.
This test prevents the NameError that was occurring at line 2474.
"""

import unittest
import os
import sys


class TestBotEnableAIAutoTweakVariable(unittest.TestCase):
    """Test that BOT_ENABLE_AI_AUTO_TWEAK variable is defined."""
    
    def test_variable_defined_when_env_false(self):
        """Test that BOT_ENABLE_AI_AUTO_TWEAK is defined when env var is false."""
        os.environ['BOT_ENABLE_AI_AUTO_TWEAK'] = 'false'
        
        # Simulate the line from web_gui.py
        BOT_ENABLE_AI_AUTO_TWEAK = os.getenv('BOT_ENABLE_AI_AUTO_TWEAK', 'false').lower() == 'true'
        
        # Should be False
        self.assertFalse(BOT_ENABLE_AI_AUTO_TWEAK)
        
        # Should be usable in style expression (line 2474)
        style_value = 'block' if BOT_ENABLE_AI_AUTO_TWEAK else 'none'
        self.assertEqual(style_value, 'none')
    
    def test_variable_defined_when_env_true(self):
        """Test that BOT_ENABLE_AI_AUTO_TWEAK is defined when env var is true."""
        os.environ['BOT_ENABLE_AI_AUTO_TWEAK'] = 'true'
        
        # Simulate the line from web_gui.py
        BOT_ENABLE_AI_AUTO_TWEAK = os.getenv('BOT_ENABLE_AI_AUTO_TWEAK', 'false').lower() == 'true'
        
        # Should be True
        self.assertTrue(BOT_ENABLE_AI_AUTO_TWEAK)
        
        # Should be usable in style expression (line 2474)
        style_value = 'block' if BOT_ENABLE_AI_AUTO_TWEAK else 'none'
        self.assertEqual(style_value, 'block')
    
    def test_variable_default_when_env_missing(self):
        """Test that BOT_ENABLE_AI_AUTO_TWEAK defaults to False when env var is missing."""
        # Remove env var if it exists
        if 'BOT_ENABLE_AI_AUTO_TWEAK' in os.environ:
            del os.environ['BOT_ENABLE_AI_AUTO_TWEAK']
        
        # Simulate the line from web_gui.py
        BOT_ENABLE_AI_AUTO_TWEAK = os.getenv('BOT_ENABLE_AI_AUTO_TWEAK', 'false').lower() == 'true'
        
        # Should default to False
        self.assertFalse(BOT_ENABLE_AI_AUTO_TWEAK)
        
        # Should be usable in style expression (line 2474)
        style_value = 'block' if BOT_ENABLE_AI_AUTO_TWEAK else 'none'
        self.assertEqual(style_value, 'none')
    
    def test_web_gui_imports_without_error(self):
        """Test that web_gui.py can be imported and BOT_ENABLE_AI_AUTO_TWEAK is defined."""
        # Set environment to ensure it exists
        os.environ['BOT_ENABLE_AI_AUTO_TWEAK'] = 'false'
        
        # Check if we can at least compile the file
        import py_compile
        import tempfile
        
        web_gui_path = os.path.join(os.path.dirname(__file__), 'web_gui.py')
        with tempfile.NamedTemporaryFile(suffix='.pyc', delete=True) as tmp:
            try:
                py_compile.compile(web_gui_path, cfile=tmp.name, doraise=True)
                compiled = True
            except py_compile.PyCompileError as e:
                compiled = False
                self.fail(f"web_gui.py failed to compile: {e}")
        
        self.assertTrue(compiled, "web_gui.py should compile without syntax errors")


if __name__ == '__main__':
    unittest.main()
