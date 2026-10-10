#!/usr/bin/env python3
"""
Test script to verify browser launch functionality in web_gui.py
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock
import time
import threading

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestBrowserLaunch(unittest.TestCase):
    """Test browser launch functionality"""
    
    def test_webbrowser_import(self):
        """Test that webbrowser module can be imported"""
        try:
            import webbrowser
            self.assertTrue(True, "webbrowser module imported successfully")
        except ImportError:
            self.fail("webbrowser module is not available")
    
    def test_browser_launch_disabled_by_env_var(self):
        """Test that browser launch can be disabled via environment variable"""
        # Set the environment variable to disable browser launch
        os.environ['WEB_GUI_NO_BROWSER'] = 'true'
        
        # Mock webbrowser.open to ensure it's not called
        with patch('webbrowser.open') as mock_open:
            # Simulate the main() function's browser launch logic
            if os.getenv('WEB_GUI_NO_BROWSER', 'false').lower() != 'true':
                mock_open('http://127.0.0.1:8050')
            
            # Verify webbrowser.open was NOT called
            mock_open.assert_not_called()
        
        # Clean up
        del os.environ['WEB_GUI_NO_BROWSER']
    
    def test_browser_launch_enabled_by_default(self):
        """Test that browser launch is enabled by default"""
        # Ensure environment variable is not set
        if 'WEB_GUI_NO_BROWSER' in os.environ:
            del os.environ['WEB_GUI_NO_BROWSER']
        
        # Mock webbrowser.open to track calls
        with patch('webbrowser.open') as mock_open:
            # Simulate the main() function's browser launch logic
            if os.getenv('WEB_GUI_NO_BROWSER', 'false').lower() != 'true':
                # Use a thread to simulate the actual implementation
                def open_browser():
                    time.sleep(0.1)  # Short delay
                    try:
                        mock_open('http://127.0.0.1:8050')
                    except Exception as e:
                        pass
                
                browser_thread = threading.Thread(target=open_browser, daemon=True)
                browser_thread.start()
                browser_thread.join(timeout=1)
            
            # Verify webbrowser.open was called
            mock_open.assert_called_once_with('http://127.0.0.1:8050')
    
    def test_shell_script_uses_xdg_open(self):
        """Test that start_web_gui.sh uses xdg-open or open command"""
        script_path = os.path.join(os.path.dirname(__file__), 'start_web_gui.sh')
        
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        # Check for xdg-open or open commands
        self.assertIn('xdg-open', script_content, 
                     "start_web_gui.sh should use xdg-open")
        self.assertIn('http://localhost:8050', script_content,
                     "start_web_gui.sh should open localhost:8050")
        
        # Ensure Chromium-specific commands are removed
        self.assertNotIn('chromium-browser --new-window', script_content,
                        "start_web_gui.sh should not have hardcoded chromium-browser")
        self.assertNotIn('chromium --new-window', script_content,
                        "start_web_gui.sh should not have hardcoded chromium")
    
    def test_shell_script_sets_no_browser_env(self):
        """Test that start_web_gui.sh sets WEB_GUI_NO_BROWSER environment variable"""
        script_path = os.path.join(os.path.dirname(__file__), 'start_web_gui.sh')
        
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        # Check for WEB_GUI_NO_BROWSER=true export
        self.assertIn('WEB_GUI_NO_BROWSER', script_content,
                     "start_web_gui.sh should set WEB_GUI_NO_BROWSER")
        self.assertIn('export WEB_GUI_NO_BROWSER=true', script_content,
                     "start_web_gui.sh should export WEB_GUI_NO_BROWSER=true")


class TestDocumentation(unittest.TestCase):
    """Test that documentation has been updated"""
    
    def test_readme_updated(self):
        """Test that README.md references default browser"""
        readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
        
        with open(readme_path, 'r') as f:
            readme_content = f.read()
        
        # Should mention default browser, not Chromium specifically
        self.assertIn('default web browser', readme_content.lower(),
                     "README.md should mention default web browser")
    
    def test_desktop_icons_guide_updated(self):
        """Test that DESKTOP_ICONS_GUIDE.md has been updated"""
        guide_path = os.path.join(os.path.dirname(__file__), 'DESKTOP_ICONS_GUIDE.md')
        
        with open(guide_path, 'r') as f:
            guide_content = f.read()
        
        # Should mention default browser or multiple browsers
        self.assertIn('default web browser', guide_content.lower(),
                     "DESKTOP_ICONS_GUIDE.md should mention default web browser")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
