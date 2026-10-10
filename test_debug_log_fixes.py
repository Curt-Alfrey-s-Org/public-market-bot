#!/usr/bin/env python3
"""
Test script to verify debug log error fixes for:
1. Flask shutdown without request context error
2. yfinance deprecation warnings are suppressed
"""

import unittest
import warnings
import logging
import sys
import os
from io import StringIO
from unittest.mock import patch, MagicMock

# Ensure we're in the correct directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestWarningsSuppression(unittest.TestCase):
    """Test that pandas/yfinance deprecation warnings are suppressed"""
    
    def test_warnings_filters_configured_in_main(self):
        """Test that main.py has warning filters configured"""
        with open('main.py', 'r') as f:
            content = f.read()
            # Check for warning filter imports and configuration
            self.assertIn('import warnings', content,
                         "main.py should import warnings module")
            self.assertIn('warnings.filterwarnings', content,
                         "main.py should have warning filters configured")
            self.assertIn('Timestamp.utcnow', content,
                         "main.py should filter Timestamp.utcnow warnings")
    
    def test_warnings_filters_configured_in_web_gui(self):
        """Test that web_gui.py has warning filters configured"""
        with open('web_gui.py', 'r') as f:
            content = f.read()
            # Check for warning filter imports and configuration
            self.assertIn('import warnings', content,
                         "web_gui.py should import warnings module")
            self.assertIn('warnings.filterwarnings', content,
                         "web_gui.py should have warning filters configured")
            self.assertIn('Timestamp.utcnow', content,
                         "web_gui.py should filter Timestamp.utcnow warnings")


class TestFlaskShutdownFix(unittest.TestCase):
    """Test shutdown logic in web_gui.py"""
    
    def test_shutdown_func_captured_before_threading(self):
        """Test that shutdown function is captured before threading to avoid request context error"""
        with open('web_gui.py', 'r') as f:
            content = f.read()
            
            # Find the shutdown callback
            shutdown_callback_start = content.find('def confirm_shutdown')
            self.assertGreater(shutdown_callback_start, 0, 
                             "confirm_shutdown callback should exist")
            
            # Extract the callback content (look for the next @app.callback or end of file)
            next_callback = content.find('@app.callback', shutdown_callback_start + 100)
            if next_callback == -1:
                next_callback = len(content)
            callback_content = content[shutdown_callback_start:next_callback]
            
            # Verify shutdown_func is captured before def shutdown_server()
            shutdown_func_capture = callback_content.find('shutdown_func = None')
            request_environ_call = callback_content.find("request.environ.get('werkzeug.server.shutdown')")
            shutdown_server_def = callback_content.find('def shutdown_server():')
            
            self.assertGreater(shutdown_func_capture, 0,
                             "shutdown_func should be captured")
            self.assertGreater(request_environ_call, 0,
                             "request.environ.get should be called")
            self.assertGreater(shutdown_server_def, 0,
                             "shutdown_server function should exist")
            
            # Critical: request.environ.get must be called BEFORE shutdown_server function
            self.assertLess(request_environ_call, shutdown_server_def,
                          "request.environ.get should be called BEFORE shutdown_server is defined")
            
            # Verify request.environ.get is NOT inside shutdown_server function
            # Extract shutdown_server function content
            thread_start = callback_content.find('threading.Thread(target=shutdown_server')
            self.assertGreater(thread_start, 0, "threading.Thread should be called")
            
            shutdown_server_content = callback_content[shutdown_server_def:thread_start]
            
            # The shutdown_server function should use shutdown_func variable, not request.environ
            self.assertNotIn('request.environ.get', shutdown_server_content,
                           "request.environ.get should NOT be inside shutdown_server function")
            self.assertIn('shutdown_func', shutdown_server_content,
                        "shutdown_server should use captured shutdown_func variable")
    
    def test_shutdown_has_error_handling(self):
        """Test that shutdown logic has proper error handling for missing request context"""
        with open('web_gui.py', 'r') as f:
            content = f.read()
            
            # Find the shutdown callback
            shutdown_callback_start = content.find('def confirm_shutdown')
            next_callback = content.find('@app.callback', shutdown_callback_start + 100)
            if next_callback == -1:
                next_callback = len(content)
            callback_content = content[shutdown_callback_start:next_callback]
            
            # Should have try-except around request.environ.get
            self.assertIn('try:', callback_content,
                        "Should have try-except for error handling")
            self.assertIn('except RuntimeError:', callback_content,
                        "Should catch RuntimeError for missing request context")


class TestModuleImports(unittest.TestCase):
    """Test that modules import without errors (when dependencies are available)"""
    
    def test_main_imports_without_errors(self):
        """Test that main.py imports without errors"""
        try:
            # Suppress all warnings during import test
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                import main
            self.assertTrue(True, "main imported successfully")
        except ModuleNotFoundError as e:
            # Skip test if dependencies are not installed
            self.skipTest(f"Skipping import test - dependency not available: {e}")
        except Exception as e:
            self.fail(f"main import failed: {e}")
    
    def test_web_gui_imports_without_errors(self):
        """Test that web_gui.py imports without errors"""
        try:
            # Suppress all warnings during import test
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                import web_gui
            self.assertTrue(True, "web_gui imported successfully")
        except ModuleNotFoundError as e:
            # Skip test if dependencies are not installed
            self.skipTest(f"Skipping import test - dependency not available: {e}")
        except Exception as e:
            self.fail(f"web_gui import failed: {e}")


if __name__ == '__main__':
    # Set environment variables for testing
    os.environ['PAPER_TRADING_MODE'] = 'true'
    os.environ['ENABLE_PDT_RULES'] = 'false'
    os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
    
    # Run tests
    print('\n' + '='*80)
    print('Testing Debug Log Error Fixes')
    print('='*80 + '\n')
    
    unittest.main(verbosity=2)
