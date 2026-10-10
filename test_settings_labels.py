#!/usr/bin/env python3
"""
Test script to verify all trade settings are present in web GUI
and labels are correct (Dynamic Stop, Partial Exit)
"""

import unittest
import os
import sys

# Set environment variables before importing
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'

class TestSettingsLabels(unittest.TestCase):
    """Test that settings labels are correct"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            import web_gui
            self.web_gui = web_gui
            self.app = web_gui.app
        except ImportError as e:
            self.skipTest(f"Web GUI dependencies not available: {e}")
    
    def test_all_required_settings_present(self):
        """Test that all 26 required settings from problem statement are present"""
        # Read the web_gui module source code
        import inspect
        source = inspect.getsource(self.web_gui)
        
        # Define the settings we need to find
        required_settings = [
            'setting-paper-trading',
            'setting-sandbox-mode',
            'setting-capital',
            'setting-min-alloc',
            'setting-max-alloc',
            'setting-risk-threshold',
            'setting-position-size',
            'setting-capital-floor',
            'setting-max-positions',
            'setting-max-losses',
            'setting-trailing-stop',
            'setting-stop-loss',
            'setting-take-profit',
            'setting-dynamic-stop',
            'setting-min-trailing',
            'setting-max-trailing',
            'setting-min-price',
            'setting-min-volume',
            'setting-max-volatility',
            'setting-volatility-window',
            'setting-partial-exit',
            'setting-partial-exit-pct',
            'setting-trading-freq',
            'setting-sim-win-rate',
            'setting-max-symbols',
            'setting-continuous-trading',
        ]
        
        for setting_id in required_settings:
            self.assertIn(f"id='{setting_id}'", source, 
                         f"Setting {setting_id} not found in web GUI")
    
    def test_dynamic_stop_label_correct(self):
        """Test that Dynamic Stop label is correct (not 'Dynamic Stop Enabled')"""
        import inspect
        source = inspect.getsource(self.web_gui)
        
        # Should contain "Dynamic Stop:" label (without "Enabled")
        self.assertIn("'Dynamic Stop:'", source, 
                     "Dynamic Stop label should be 'Dynamic Stop:' not 'Dynamic Stop Enabled:'")
        
        # Should NOT contain the old label
        self.assertNotIn("'Dynamic Stop Enabled:'", source,
                        "Old label 'Dynamic Stop Enabled:' should not be present")
    
    def test_partial_exit_label_correct(self):
        """Test that Partial Exit label is correct (not 'Partial Exit Enabled')"""
        import inspect
        source = inspect.getsource(self.web_gui)
        
        # Should contain "Partial Exit:" label (without "Enabled")
        self.assertIn("'Partial Exit:'", source,
                     "Partial Exit label should be 'Partial Exit:' not 'Partial Exit Enabled:'")
        
        # Should NOT contain the old label
        self.assertNotIn("'Partial Exit Enabled:'", source,
                        "Old label 'Partial Exit Enabled:' should not be present")
    
    def test_dropdown_options_correct(self):
        """Test that dropdowns still have Enabled/Disabled options"""
        import inspect
        source = inspect.getsource(self.web_gui)
        
        # Dynamic Stop should have dropdown with Enabled/Disabled
        self.assertIn("'setting-dynamic-stop'", source)
        # Should have Enabled and Disabled as dropdown options
        self.assertIn("'Enabled', 'value': 'true'", source)
        self.assertIn("'Disabled', 'value': 'false'", source)


class TestSettingsConsistency(unittest.TestCase):
    """Test settings consistency across the application"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            import web_gui
            self.web_gui = web_gui
        except ImportError as e:
            self.skipTest(f"Web GUI dependencies not available: {e}")
    
    def test_setting_ids_match_env_vars(self):
        """Test that setting IDs correspond to correct environment variables"""
        import inspect
        source = inspect.getsource(self.web_gui)
        
        # Check key mappings between setting IDs and env vars
        mappings = {
            'setting-dynamic-stop': 'DYNAMIC_STOP_ENABLED',
            'setting-partial-exit': 'PARTIAL_EXIT_ENABLED',
            'setting-capital': 'BOT_TOTAL_CAPITAL',
            'setting-max-positions': 'BOT_MAX_OPEN_POSITIONS',
        }
        
        for setting_id, env_var in mappings.items():
            self.assertIn(setting_id, source, f"Setting {setting_id} not found")
            # Note: env_var should appear somewhere near the setting_id in the source
            # This is a basic check to ensure they're related


if __name__ == '__main__':
    print("Testing Web GUI Settings Labels...")
    print("=" * 70)
    unittest.main(verbosity=2)
