"""
Test that .env.example has proper documentation for critical variables.

This test validates that BACKTEST_MODE and SWING_HOLD_MIN_DAYS have
appropriate warnings and documentation in .env.example.
"""

import unittest


class TestEnvExampleDocumentation(unittest.TestCase):
    """Test .env.example documentation quality."""
    
    def setUp(self):
        """Load .env.example content."""
        with open('.env.example', 'r') as f:
            self.env_content = f.read()
            self.env_lines = self.env_content.split('\n')
    
    def test_backtest_mode_has_warning(self):
        """Test that BACKTEST_MODE has a WARNING comment."""
        # Find the BACKTEST_MODE variable
        backtest_found = False
        warning_found = False
        
        for i, line in enumerate(self.env_lines):
            if 'BACKTEST_MODE=' in line:
                backtest_found = True
                # Check the lines before it for WARNING
                for j in range(max(0, i-15), i):
                    if 'WARNING' in self.env_lines[j].upper():
                        warning_found = True
                        break
                break
        
        self.assertTrue(backtest_found, "BACKTEST_MODE not found in .env.example")
        self.assertTrue(warning_found, 
                       "BACKTEST_MODE does not have a WARNING in its documentation")
    
    def test_backtest_mode_has_proper_value(self):
        """Test that BACKTEST_MODE has default value of 'false'."""
        backtest_line = None
        for line in self.env_lines:
            if line.strip().startswith('BACKTEST_MODE='):
                backtest_line = line
                break
        
        self.assertIsNotNone(backtest_line, "BACKTEST_MODE not found")
        self.assertIn('BACKTEST_MODE=false', backtest_line,
                     "BACKTEST_MODE should default to 'false'")
    
    def test_swing_hold_min_days_has_warning(self):
        """Test that SWING_HOLD_MIN_DAYS has a WARNING comment."""
        # Find the SWING_HOLD_MIN_DAYS variable
        swing_found = False
        warning_found = False
        
        for i, line in enumerate(self.env_lines):
            if 'SWING_HOLD_MIN_DAYS=' in line:
                swing_found = True
                # Check the lines before it for WARNING
                for j in range(max(0, i-20), i):
                    if 'WARNING' in self.env_lines[j].upper():
                        warning_found = True
                        break
                break
        
        self.assertTrue(swing_found, "SWING_HOLD_MIN_DAYS not found in .env.example")
        self.assertTrue(warning_found,
                       "SWING_HOLD_MIN_DAYS does not have a WARNING in its documentation")
    
    def test_swing_hold_min_days_has_proper_value(self):
        """Test that SWING_HOLD_MIN_DAYS has default value of 1."""
        swing_line = None
        for line in self.env_lines:
            if line.strip().startswith('SWING_HOLD_MIN_DAYS='):
                swing_line = line
                break
        
        self.assertIsNotNone(swing_line, "SWING_HOLD_MIN_DAYS not found")
        self.assertIn('SWING_HOLD_MIN_DAYS=1', swing_line,
                     "SWING_HOLD_MIN_DAYS should default to '1'")
    
    def test_swing_hold_mentions_pdt(self):
        """Test that SWING_HOLD_MIN_DAYS documentation mentions PDT rules."""
        # Find the section with SWING_HOLD_MIN_DAYS
        swing_section = []
        
        for i, line in enumerate(self.env_lines):
            # Start collecting when we see the section header or variable
            if 'Swing Trading Hold Period' in line or 'SWING_HOLD_MIN_DAYS' in line:
                # Include 15 lines before and 5 after
                start = max(0, i - 15)
                end = min(len(self.env_lines), i + 5)
                swing_section = self.env_lines[start:end]
                break
        
        swing_text = '\n'.join(swing_section)
        self.assertIn('PDT', swing_text.upper(),
                     "SWING_HOLD_MIN_DAYS documentation should mention PDT rules")
    
    def test_backtest_mode_mentions_historical_data(self):
        """Test that BACKTEST_MODE documentation mentions historical data."""
        # Find the section with BACKTEST_MODE
        backtest_section = []
        
        for i, line in enumerate(self.env_lines):
            if 'BACKTEST_MODE=' in line:
                # Include 15 lines before
                start = max(0, i - 15)
                backtest_section = self.env_lines[start:i+1]
                break
        
        backtest_text = '\n'.join(backtest_section)
        self.assertIn('historical', backtest_text.lower(),
                     "BACKTEST_MODE documentation should mention historical data")
    
    def test_env_example_syntax_valid(self):
        """Test that .env.example has valid syntax (all vars have = sign)."""
        issues = []
        for i, line in enumerate(self.env_lines, 1):
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Check if line has '=' (valid env var)
            if '=' not in line:
                issues.append(f'Line {i}: Invalid format (no = sign): {line}')
        
        self.assertEqual([], issues, f"Syntax errors found: {issues}")


if __name__ == '__main__':
    unittest.main()
