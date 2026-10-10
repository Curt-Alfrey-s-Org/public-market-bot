#!/usr/bin/env python3
"""
Test to verify callback parameter alignment fix
Tests that callback decorators match function signatures
"""

import unittest
import re


class TestCallbackParameterAlignment(unittest.TestCase):
    """Test that callback decorators and function signatures are aligned"""
    
    def setUp(self):
        """Read web_gui.py content"""
        with open('web_gui.py', 'r') as f:
            self.content = f.read()
    
    def test_apply_settings_callback_alignment(self):
        """Test that apply_settings callback parameters match function signature"""
        # Find apply_settings callback
        match = re.search(
            r"@app.callback\(\s*Output\('settings-feedback'.*?\)\s*def apply_settings\((.*?)\):",
            self.content,
            re.DOTALL
        )
        self.assertIsNotNone(match, "apply_settings callback not found")
        
        callback_section = match.group(0)
        
        # Count Input and State parameters
        input_count = len(re.findall(r"Input\('", callback_section))
        state_count = len(re.findall(r"State\('", callback_section))
        
        # Count function parameters
        params_str = match.group(1)
        param_list = [p.strip() for p in params_str.split(',') if p.strip()]
        param_count = len(param_list)
        
        # Verify counts match
        expected = input_count + state_count
        self.assertEqual(
            param_count,
            expected,
            f"Parameter count mismatch: {param_count} params vs {expected} expected ({input_count} Inputs + {state_count} States)"
        )
        
        # Verify volatility_norm_range is present (was missing before fix)
        self.assertIn(
            'volatility_norm_range',
            param_list,
            "volatility_norm_range parameter missing from function signature"
        )
        
        # Verify max_price is present (was missing before fix)
        self.assertIn(
            'max_price',
            param_list,
            "max_price parameter missing from function signature"
        )
        
        # Verify max_price is between min_price and min_volume
        min_price_idx = param_list.index('min_price')
        max_price_idx = param_list.index('max_price')
        min_volume_idx = param_list.index('min_volume')
        
        self.assertLess(
            min_price_idx,
            max_price_idx,
            "min_price should come before max_price"
        )
        self.assertLess(
            max_price_idx,
            min_volume_idx,
            "max_price should come before min_volume"
        )
        self.assertEqual(
            max_price_idx,
            min_price_idx + 1,
            "max_price should come immediately after min_price"
        )
    
    def test_control_bot_callback_alignment(self):
        """Test that control_bot callback parameters match function signature"""
        # Find control_bot callback
        match = re.search(
            r"@app.callback\(\s*\[Output\('status-indicator'.*?\)\s*def control_bot\((.*?)\):",
            self.content,
            re.DOTALL
        )
        self.assertIsNotNone(match, "control_bot callback not found")
        
        callback_section = match.group(0)
        
        # Count Input and State parameters
        input_count = len(re.findall(r"Input\('", callback_section))
        state_count = len(re.findall(r"State\('", callback_section))
        
        # Count function parameters
        params_str = match.group(1)
        param_list = [p.strip() for p in params_str.split(',') if p.strip()]
        param_count = len(param_list)
        
        # Verify counts match
        expected = input_count + state_count
        self.assertEqual(
            param_count,
            expected,
            f"Parameter count mismatch: {param_count} params vs {expected} expected ({input_count} Inputs + {state_count} States)"
        )
        
        # Verify max_price is present (was missing before fix)
        self.assertIn(
            'max_price',
            param_list,
            "max_price parameter missing from function signature"
        )
        
        # Verify max_price is between min_price and min_volume
        min_price_idx = param_list.index('min_price')
        max_price_idx = param_list.index('max_price')
        min_volume_idx = param_list.index('min_volume')
        
        self.assertLess(
            min_price_idx,
            max_price_idx,
            "min_price should come before max_price"
        )
        self.assertLess(
            max_price_idx,
            min_volume_idx,
            "max_price should come before min_volume"
        )
        self.assertEqual(
            max_price_idx,
            min_price_idx + 1,
            "max_price should come immediately after min_price"
        )
    
    def test_max_price_state_in_callbacks(self):
        """Test that setting-max-price State is present in both callbacks"""
        # Check apply_settings callback
        apply_match = re.search(
            r"@app.callback\(\s*Output\('settings-feedback'.*?\)\s*def apply_settings",
            self.content,
            re.DOTALL
        )
        self.assertIsNotNone(apply_match)
        apply_callback = apply_match.group(0)
        
        self.assertIn(
            "State('setting-max-price', 'value')",
            apply_callback,
            "State('setting-max-price') missing from apply_settings callback"
        )
        
        # Check control_bot callback
        control_match = re.search(
            r"@app.callback\(\s*\[Output\('status-indicator'.*?\)\s*def control_bot",
            self.content,
            re.DOTALL
        )
        self.assertIsNotNone(control_match)
        control_callback = control_match.group(0)
        
        self.assertIn(
            "State('setting-max-price', 'value')",
            control_callback,
            "State('setting-max-price') missing from control_bot callback"
        )


if __name__ == '__main__':
    unittest.main()
