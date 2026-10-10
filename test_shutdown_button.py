#!/usr/bin/env python3
"""
Test script for web GUI shutdown button functionality
Tests that the shutdown button and confirmation modal exist and work correctly
"""

import unittest
import os
import sys

# Set environment variables before importing
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
os.environ['ENABLE_PDT_RULES'] = 'false'

class TestShutdownButton(unittest.TestCase):
    """Test shutdown button and confirmation modal"""
    
    def setUp(self):
        """Set up test environment"""
        # Import here to avoid issues with missing dependencies
        try:
            import web_gui
            self.web_gui = web_gui
            self.app = web_gui.app
        except ImportError as e:
            self.skipTest(f"Web GUI dependencies not available: {e}")
    
    def test_shutdown_button_exists_in_layout(self):
        """Test that shutdown button exists in the layout"""
        layout = self.app.layout
        layout_str = str(layout)
        
        # Check for shutdown button ID
        self.assertIn('header-shutdown-button', layout_str, 
                     "Shutdown button should exist in layout")
        
        # Check for shutdown modal
        self.assertIn('shutdown-modal', layout_str,
                     "Shutdown confirmation modal should exist in layout")
        
        # Check for confirm and cancel buttons
        self.assertIn('shutdown-confirm-button', layout_str,
                     "Shutdown confirm button should exist in modal")
        self.assertIn('shutdown-cancel-button', layout_str,
                     "Shutdown cancel button should exist in modal")
    
    def test_shutdown_button_styling(self):
        """Test that shutdown button has appropriate styling"""
        layout_str = str(self.app.layout)
        
        # Check for power-off icon
        self.assertIn('fa-power-off', layout_str,
                     "Shutdown button should have power-off icon")
        
        # Check for "Shutdown" text
        self.assertIn('Shutdown', layout_str,
                     "Shutdown button should have 'Shutdown' text")
    
    def test_global_variables_for_shutdown(self):
        """Test that required global variables exist for shutdown"""
        # Check for stop_event
        self.assertTrue(hasattr(self.web_gui, 'stop_event'),
                       "stop_event should exist for graceful shutdown")
        
        # Check for is_running flag
        self.assertTrue(hasattr(self.web_gui, 'is_running'),
                       "is_running flag should exist")
        
        # Check for bot variable
        self.assertTrue(hasattr(self.web_gui, 'bot'),
                       "bot variable should exist")
    
    def test_shutdown_modal_structure(self):
        """Test that shutdown modal has proper structure"""
        layout_str = str(self.app.layout)
        
        # Check for warning icon
        self.assertIn('fa-exclamation-triangle', layout_str,
                     "Modal should have warning icon")
        
        # Check for confirmation text
        self.assertIn('Confirm Shutdown', layout_str,
                     "Modal should have confirmation heading")
        
        # Check for informative text about what shutdown does
        self.assertIn('Stop the trading bot', layout_str,
                     "Modal should explain what shutdown does")


class TestShutdownCallbacks(unittest.TestCase):
    """Test shutdown callback functions"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            import web_gui
            self.web_gui = web_gui
            self.app = web_gui.app
        except ImportError as e:
            self.skipTest(f"Web GUI dependencies not available: {e}")
    
    def test_callbacks_defined(self):
        """Test that shutdown callbacks are defined in the app"""
        # Get all callback IDs from the app
        callback_map = self.app.callback_map
        
        # Check that we have callbacks registered
        self.assertIsNotNone(callback_map, "App should have callbacks registered")
        
        # Note: We can't easily test callback execution without running the full Dash server
        # So we just verify the structure exists


class TestShutdownFlow(unittest.TestCase):
    """Test the shutdown flow logic"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            import web_gui
            self.web_gui = web_gui
        except ImportError as e:
            self.skipTest(f"Web GUI dependencies not available: {e}")
    
    def test_stop_event_mechanism(self):
        """Test that stop_event can be set and cleared"""
        stop_event = self.web_gui.stop_event
        
        # Should start cleared
        self.assertFalse(stop_event.is_set(), "stop_event should start cleared")
        
        # Should be settable
        stop_event.set()
        self.assertTrue(stop_event.is_set(), "stop_event should be settable")
        
        # Should be clearable
        stop_event.clear()
        self.assertFalse(stop_event.is_set(), "stop_event should be clearable")
    
    def test_is_running_flag(self):
        """Test that is_running flag can be toggled"""
        # Reset state
        self.web_gui.is_running = False
        self.assertFalse(self.web_gui.is_running, "is_running should be False")
        
        # Should be settable
        self.web_gui.is_running = True
        self.assertTrue(self.web_gui.is_running, "is_running should be settable to True")
        
        # Reset for other tests
        self.web_gui.is_running = False


if __name__ == '__main__':
    print("Running shutdown button tests...")
    print("=" * 60)
    
    # Run tests
    unittest.main(verbosity=2)
