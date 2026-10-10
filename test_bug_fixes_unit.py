#!/usr/bin/env python3
"""
Unit Tests for Critical Bug Fixes
Tests that previously broken functionality now works
"""
import unittest
import subprocess
from pathlib import Path

class TestBugFixes(unittest.TestCase):
    """Test suite for critical bug fixes"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.bot_host = "operator@192.0.2.21"
        cls.project_dir = Path(__file__).parent
    
    def run_ssh(self, command):
        """Run SSH command and return output"""
        result = subprocess.run(
            ['ssh', self.bot_host, command],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip(), result.returncode
    
    # BUG #1: Headless Mode Auto-Start
    def test_bug1_headless_mode_auto_starts(self):
        """BUG FIX #1: Bot auto-starts in headless mode without user input"""
        stdout, _ = self.run_ssh('grep -i "headless" /tmp/bot_output.log')
        self.assertGreater(len(stdout), 0, "Headless mode not detected")
    
    def test_bug1_no_user_prompt_in_logs(self):
        """BUG FIX #1: No 'Type START' prompt appears in logs"""
        stdout, _ = self.run_ssh('grep -i "type.*start\\|enter.*start" /tmp/bot_output.log')
        self.assertEqual(len(stdout), 0, "User prompt found in logs - headless mode broken")
    
    # BUG #2: Single-Pass Trading Loop
    def test_bug2_while_true_loop_working(self):
        """BUG FIX #2: Bot runs in continuous while True loop"""
        stdout, _ = self.run_ssh('grep "Trading Cycle #" /tmp/bot_output.log | wc -l')
        count = int(stdout or 0)
        self.assertGreaterEqual(count, 2, "Less than 2 cycles - bot not looping continuously")
    
    # BUG #3: Execute Trade Indentation (CRITICAL)
    def test_bug3_trades_executing_with_valid_action(self):
        """BUG FIX #3: execute_trade is inside for loop (trades with valid action)"""
        stdout, _ = self.run_ssh('grep "Processing trade for" /tmp/bot_output.log | head -5')
        self.assertGreater(len(stdout), 0, "No trades being processed")
        
        # Verify no "None" actions
        for line in stdout.split('\n'):
            if "Processing trade for" in line:
                self.assertNotIn("(None)", line, f"Trade with None action: {line}")
    
    # BUG #4: bot.running Flag
    def test_bug4_bot_process_running(self):
        """BUG FIX #4: Bot process is running and active"""
        stdout, _ = self.run_ssh('pgrep -f "python main.py" | wc -l')
        count = int(stdout or 0)
        self.assertGreater(count, 0, "Bot process not running")
    
    # BUG #5: API Trades Database
    def test_bug5_trades_executing(self):
        """BUG FIX #5: Trades are executing (evidence in logs)"""
        stdout, _ = self.run_ssh('grep "Processing trade for" /tmp/bot_output.log | wc -l')
        count = int(stdout or 0)
        self.assertGreater(count, 5, "Not enough trades executed")
    
    # BUG #6: Strategy Manager Failure
    def test_bug6_strategy_signals_generated(self):
        """BUG FIX #6: Strategies generating signals correctly"""
        stdout, _ = self.run_ssh('grep -iE "(BUY|SELL|HOLD)" /tmp/bot_output.log | wc -l')
        count = int(stdout or 0)
        self.assertGreater(count, 10, "Not enough strategy signals generated")
    
    # BUG #7: Try/Except Indentation
    def test_bug7_no_syntax_errors(self):
        """BUG FIX #7: No SyntaxError from indentation issues"""
        stdout, _ = self.run_ssh('grep -i "SyntaxError" /tmp/bot_output.log')
        self.assertEqual(len(stdout), 0, "SyntaxError found - indentation still broken")
    
    # Integration Tests
    def test_integration_full_cycle(self):
        """Integration: Complete trading cycle working"""
        stdout, _ = self.run_ssh('grep "Cycle Summary" /tmp/bot_output.log | wc -l')
        count = int(stdout or 0)
        self.assertGreaterEqual(count, 1, "No complete trading cycles")
    
    def test_integration_no_crashes(self):
        """Integration: No fatal crashes"""
        stdout, _ = self.run_ssh('grep -i "Traceback" /tmp/bot_output.log')
        self.assertEqual(len(stdout), 0, "Python crash detected")
    
    def test_integration_pnl_working(self):
        """Integration: P&L calculations active"""
        stdout, _ = self.run_ssh('grep "P&L:" /tmp/bot_output.log | wc -l')
        count = int(stdout or 0)
        self.assertGreater(count, 0, "No P&L calculations found")

if __name__ == "__main__":
    unittest.main(verbosity=2)
