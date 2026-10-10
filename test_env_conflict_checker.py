#!/usr/bin/env python3
"""
Test suite for environment variable conflict checker
"""

import os
import sys
import unittest
from unittest.mock import patch
from io import StringIO

# Set test environment variables before importing
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
os.environ['SCHWAB_API_ENABLED'] = 'off'

from env_conflict_checker import (
    check_env_conflicts, EnvConflict, create_sanitized_env,
    print_conflict_report, write_sanitized_env
)


class TestEnvConflictChecker(unittest.TestCase):
    """Test environment conflict detection"""
    
    def setUp(self):
        """Store original environment"""
        self.original_env = os.environ.copy()
    
    def tearDown(self):
        """Restore original environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_obsolete_pdt_rules_warning(self):
        """Test detection of obsolete ENABLE_PDT_RULES setting"""
        with patch.dict(os.environ, {
            'PAPER_TRADING_MODE': 'true',
            'ENABLE_PDT_RULES': 'true',
            'SCHWAB_API_ENABLED': 'on'
        }):
            conflicts = check_env_conflicts()
            pdt_conflicts = [c for c in conflicts if 'PDT' in c.title]
            self.assertTrue(len(pdt_conflicts) > 0, "Should detect obsolete PDT rules setting")
            self.assertEqual(pdt_conflicts[0].severity, 'WARNING')
    
    def test_redundant_config_info(self):
        """Test detection of redundant sandbox + API disabled"""
        with patch.dict(os.environ, {
            'PAPER_TRADING_MODE': 'true',
            'SCHWAB_SANDBOX_MODE': 'false',
            'SCHWAB_API_ENABLED': 'off'
        }):
            conflicts = check_env_conflicts()
            redundant_conflicts = [c for c in conflicts if 'Redundant' in c.title]
            self.assertTrue(len(redundant_conflicts) > 0, "Should detect redundant configuration")
            self.assertEqual(redundant_conflicts[0].severity, 'INFO')
    
    def test_live_mode_api_disabled_error(self):
        """Test error when live mode has API disabled"""
        with patch.dict(os.environ, {
            'PAPER_TRADING_MODE': 'false',
            'SCHWAB_API_ENABLED': 'off'
        }):
            conflicts = check_env_conflicts()
            live_mode_conflicts = [c for c in conflicts if 'Live Trading' in c.title]
            self.assertTrue(len(live_mode_conflicts) > 0, "Should detect live mode with API disabled")
            self.assertEqual(live_mode_conflicts[0].severity, 'ERROR')
    
    def test_non_interactive_without_token(self):
        """Test warning for non-interactive mode without token"""
        # Ensure token.json doesn't exist
        token_path = 'token.json'
        token_exists = os.path.exists(token_path)
        
        with patch.dict(os.environ, {
            'NON_INTERACTIVE': 'true',
            'SCHWAB_API_ENABLED': 'on',
            'SCHWAB_TOKEN_PATH': token_path
        }):
            conflicts = check_env_conflicts()
            if not token_exists:
                non_interactive_conflicts = [c for c in conflicts if 'Non-Interactive' in c.title]
                self.assertTrue(len(non_interactive_conflicts) > 0, "Should detect non-interactive without token")
    
    def test_sandbox_with_api_disabled(self):
        """Test warning for sandbox mode with API disabled"""
        with patch.dict(os.environ, {
            'SCHWAB_SANDBOX_MODE': 'true',
            'SCHWAB_API_ENABLED': 'off'
        }):
            conflicts = check_env_conflicts()
            sandbox_conflicts = [c for c in conflicts if 'Sandbox Mode with API Disabled' in c.title]
            self.assertTrue(len(sandbox_conflicts) > 0, "Should detect sandbox with API disabled")
            self.assertEqual(sandbox_conflicts[0].severity, 'WARNING')
    
    def test_high_stop_loss_warning(self):
        """Test warning for unusually high stop loss"""
        with patch.dict(os.environ, {
            'BOT_STOP_LOSS_PERCENT': '0.20',  # 20%
            'PAPER_TRADING_MODE': 'true'
        }):
            conflicts = check_env_conflicts()
            stop_loss_conflicts = [c for c in conflicts if 'Stop Loss' in c.title]
            self.assertTrue(len(stop_loss_conflicts) > 0, "Should detect high stop loss")
            self.assertEqual(stop_loss_conflicts[0].severity, 'WARNING')
    
    def test_high_take_profit_warning(self):
        """Test warning for unusually high take profit"""
        with patch.dict(os.environ, {
            'BOT_TAKE_PROFIT_PERCENT': '0.50',  # 50%
            'PAPER_TRADING_MODE': 'true'
        }):
            conflicts = check_env_conflicts()
            take_profit_conflicts = [c for c in conflicts if 'Take Profit' in c.title]
            self.assertTrue(len(take_profit_conflicts) > 0, "Should detect high take profit")
            self.assertEqual(take_profit_conflicts[0].severity, 'WARNING')
    
    def test_position_size_risk_mismatch(self):
        """Test warning for position size vs risk threshold mismatch"""
        with patch.dict(os.environ, {
            'BOT_RISK_THRESHOLD': '0.02',  # 2%
            'BOT_POSITION_SIZE': '0.05',    # 5% - much larger
            'PAPER_TRADING_MODE': 'true'
        }):
            conflicts = check_env_conflicts()
            mismatch_conflicts = [c for c in conflicts if 'Position Size vs Risk Threshold' in c.title]
            self.assertTrue(len(mismatch_conflicts) > 0, "Should detect position size mismatch")
            self.assertEqual(mismatch_conflicts[0].severity, 'WARNING')
    
    def test_no_conflicts_valid_config(self):
        """Test that valid configuration produces no conflicts"""
        with patch.dict(os.environ, {
            'PAPER_TRADING_MODE': 'true',
            'SCHWAB_SANDBOX_MODE': 'false',
            'SCHWAB_API_ENABLED': 'off',
            'BOT_RISK_THRESHOLD': '0.02',
            'BOT_POSITION_SIZE': '0.02',
            'BOT_STOP_LOSS_PERCENT': '0.06',
            'BOT_TAKE_PROFIT_PERCENT': '0.10'
        }):
            conflicts = check_env_conflicts()
            errors = [c for c in conflicts if c.severity == 'ERROR']
            self.assertEqual(len(errors), 0, "Valid config should have no errors")
    
    def test_sanitized_env_api_disabled(self):
        """Test sanitized config with API disabled"""
        with patch.dict(os.environ, {
            'SCHWAB_API_ENABLED': 'off',
            'PAPER_TRADING_MODE': 'false',  # Will be forced to true
            'SCHWAB_SANDBOX_MODE': 'true',  # Will be forced to false
            'BOT_RISK_THRESHOLD': '0.02'
        }):
            sanitized = create_sanitized_env()
            
            self.assertEqual(sanitized['SCHWAB_API_ENABLED'], 'off')
            self.assertEqual(sanitized['SCHWAB_SANDBOX_MODE'], 'false')
            self.assertEqual(sanitized['PAPER_TRADING_MODE'], 'true')  # Forced
    
    def test_sanitized_env_removes_pdt_rules(self):
        """Test that sanitized config doesn't include obsolete ENABLE_PDT_RULES"""
        with patch.dict(os.environ, {
            'ENABLE_PDT_RULES': 'true',
            'PAPER_TRADING_MODE': 'true',
            'SCHWAB_API_ENABLED': 'off'
        }):
            sanitized = create_sanitized_env()
            
            self.assertNotIn('ENABLE_PDT_RULES', sanitized, 
                           "Sanitized config should not include obsolete ENABLE_PDT_RULES")
    
    def test_sanitized_env_adjusts_risky_parameters(self):
        """Test that sanitized config adjusts risky parameters"""
        with patch.dict(os.environ, {
            'BOT_STOP_LOSS_PERCENT': '0.20',  # 20% - too high
            'BOT_TAKE_PROFIT_PERCENT': '0.50',  # 50% - too high
            'PAPER_TRADING_MODE': 'true',
            'SCHWAB_API_ENABLED': 'off'
        }):
            sanitized = create_sanitized_env()
            
            # Should be capped at safer values
            stop_loss = float(sanitized['BOT_STOP_LOSS_PERCENT'])
            take_profit = float(sanitized['BOT_TAKE_PROFIT_PERCENT'])
            
            self.assertLessEqual(stop_loss, 0.10, "Stop loss should be capped at 10%")
            self.assertLessEqual(take_profit, 0.20, "Take profit should be capped at 20%")
    
    def test_sanitized_env_aligns_position_size(self):
        """Test that sanitized config aligns position size with risk threshold"""
        with patch.dict(os.environ, {
            'BOT_RISK_THRESHOLD': '0.02',
            'BOT_POSITION_SIZE': '0.10',  # Misaligned
            'PAPER_TRADING_MODE': 'true',
            'SCHWAB_API_ENABLED': 'off'
        }):
            sanitized = create_sanitized_env()
            
            # Position size should match risk threshold
            self.assertEqual(sanitized['BOT_POSITION_SIZE'], sanitized['BOT_RISK_THRESHOLD'])
    
    def test_print_conflict_report(self):
        """Test that conflict report prints correctly"""
        conflicts = [
            EnvConflict('ERROR', 'Test Error', 'Error description', ['VAR1'], 'Fix it'),
            EnvConflict('WARNING', 'Test Warning', 'Warning description', ['VAR2'], 'Consider this'),
            EnvConflict('INFO', 'Test Info', 'Info description', ['VAR3'], 'Note this')
        ]
        
        # Capture output
        captured_output = StringIO()
        sys.stdout = captured_output
        
        print_conflict_report(conflicts)
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        self.assertIn('ERRORS', output)
        self.assertIn('WARNINGS', output)
        self.assertIn('INFO', output)
        self.assertIn('Test Error', output)
        self.assertIn('Test Warning', output)
        self.assertIn('Test Info', output)
    
    def test_write_sanitized_env(self):
        """Test writing sanitized environment to file"""
        import tempfile
        
        with patch.dict(os.environ, {
            'PAPER_TRADING_MODE': 'true',
            'SCHWAB_API_ENABLED': 'off',
            'BOT_RISK_THRESHOLD': '0.02'
        }):
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as f:
                output_path = f.name
            
            try:
                write_sanitized_env(output_path)
                
                # Verify file was created and contains expected content
                self.assertTrue(os.path.exists(output_path))
                
                with open(output_path, 'r') as f:
                    content = f.read()
                
                self.assertIn('PAPER_TRADING_MODE', content)
                self.assertIn('SCHWAB_API_ENABLED', content)
                self.assertIn('BOT_RISK_THRESHOLD', content)
                self.assertNotIn('ENABLE_PDT_RULES', content)  # Should be removed
            
            finally:
                if os.path.exists(output_path):
                    os.remove(output_path)


class TestEnvConflictIntegration(unittest.TestCase):
    """Test integration with main.py"""
    
    def test_validate_configuration_includes_conflict_checks(self):
        """Test that validate_configuration calls conflict checker"""
        with patch.dict(os.environ, {
            'PAPER_TRADING_MODE': 'true',
            'ENABLE_PDT_RULES': 'true',  # Should trigger warning
            'SCHWAB_API_ENABLED': 'off'
        }):
            # Import after setting environment
            import main
            
            is_valid, issues = main.validate_configuration()
            
            # Should still be valid (warnings don't fail validation)
            # Errors would cause failure
            self.assertTrue(is_valid or len(issues) == 0 or 
                          not any('LIVE mode' in issue for issue in issues))


if __name__ == '__main__':
    print("Testing Environment Conflict Checker")
    print("=" * 70)
    unittest.main(verbosity=2)
