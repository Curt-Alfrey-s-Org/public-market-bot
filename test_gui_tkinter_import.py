#!/usr/bin/env python3
"""
Test script for gui.py tkinter ImportError handling
Verifies that gui.py provides helpful error message when tkinter is missing
"""

import sys
import unittest
import subprocess


class TestGUITkinterImportError(unittest.TestCase):
    """Test that GUI handles missing tkinter gracefully"""
    
    def test_gui_syntax_is_valid(self):
        """Test that gui.py has no syntax errors"""
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', 'gui.py'],
            capture_output=True,
            text=True,
            cwd='/home/runner/work/market-pie5-bot/market-pie5-bot'
        )
        
        self.assertEqual(result.returncode, 0, "gui.py should have no syntax errors")
    
    def test_error_message_uses_stderr(self):
        """Test that the error handling code uses sys.stderr instead of print"""
        with open('/home/runner/work/market-pie5-bot/market-pie5-bot/gui.py', 'r') as f:
            content = f.read()
        
        # Check that the ImportError handler uses sys.stderr.write()
        self.assertIn('sys.stderr.write(error_message)', content,
                      "ImportError handler should use sys.stderr.write()")
        
        # Check that it doesn't use print() in the ImportError handler
        lines = content.split('\n')
        in_import_error_handler = False
        for i, line in enumerate(lines):
            if 'except ImportError' in line:
                in_import_error_handler = True
            elif in_import_error_handler and 'sys.exit(1)' in line:
                in_import_error_handler = False
            elif in_import_error_handler and 'print(' in line:
                self.fail(f"Line {i+1}: ImportError handler should not use print(), found: {line.strip()}")
    
    def test_error_message_content(self):
        """Test that the error message contains all required information"""
        with open('/home/runner/work/market-pie5-bot/market-pie5-bot/gui.py', 'r') as f:
            content = f.read()
        
        # Check for combined Ubuntu/Debian/Raspberry Pi OS section
        self.assertIn('Ubuntu/Debian/Raspberry Pi OS', content,
                      "Should combine Ubuntu/Debian/Raspberry Pi OS into one section")
        
        # Check for installation instructions
        self.assertIn('sudo apt-get install python3-tk', content,
                      "Should provide apt-get installation instructions")
        self.assertIn('sudo dnf install python3-tkinter', content,
                      "Should provide dnf installation instructions")
        self.assertIn('sudo pacman -S tk', content,
                      "Should provide pacman installation instructions")
        self.assertIn('brew install python-tk', content,
                      "Should provide brew installation instructions")
        
        # Check for web GUI alternative
        self.assertIn('./start_web_gui.sh', content,
                      "Should suggest web GUI alternative")
        
        # Should not have separate Raspberry Pi OS section
        lines = content.split('\n')
        raspberry_pi_lines = [i for i, line in enumerate(lines) if 'On Raspberry Pi OS:' in line and 'Ubuntu/Debian' not in line]
        self.assertEqual(len(raspberry_pi_lines), 0,
                         "Should not have separate 'On Raspberry Pi OS:' section")
    
    def test_geometry_manager_consistency(self):
        """Test that pdt_frame and alert_frame don't mix .pack() and .grid()"""
        with open('/home/runner/work/market-pie5-bot/market-pie5-bot/gui.py', 'r') as f:
            content = f.read()
        
        # Find the pdt_frame section
        lines = content.split('\n')
        pdt_frame_start = None
        alert_frame_start = None
        
        for i, line in enumerate(lines):
            if 'pdt_frame = ttk.LabelFrame' in line:
                pdt_frame_start = i
            elif 'alert_frame = ttk.LabelFrame' in line:
                alert_frame_start = i
                break
        
        self.assertIsNotNone(pdt_frame_start, "Should find pdt_frame definition")
        self.assertIsNotNone(alert_frame_start, "Should find alert_frame definition")
        
        # Check pdt_frame section (from pdt_frame definition to alert_frame definition)
        pdt_section = '\n'.join(lines[pdt_frame_start:alert_frame_start])
        
        # Should not have .grid() calls directly on pdt_frame children
        # (It's OK to have grid in bot_frame or other frames)
        pdt_grid_lines = [line for line in pdt_section.split('\n') if '.grid(' in line and 'pdt_frame' in line]
        self.assertEqual(len(pdt_grid_lines), 0,
                         f"pdt_frame should not use .grid() on its direct children. Found: {pdt_grid_lines}")
    
    def test_with_tkinter_available_imports_successfully(self):
        """Test that GUI can be imported when tkinter is available"""
        # This test only runs if tkinter is actually available
        try:
            import tkinter
            tkinter_available = True
        except ImportError:
            tkinter_available = False
        
        if not tkinter_available:
            self.skipTest("tkinter not available for testing")
        
        # Try to import GUI module
        test_script = '''
import sys
sys.path.insert(0, '/home/runner/work/market-pie5-bot/market-pie5-bot')

# Check that the module doesn't exit due to tkinter ImportError
try:
    import gui
    # If we get here without SystemExit, tkinter was imported successfully
    print("SUCCESS: No tkinter ImportError")
except ImportError as e:
    # Other import errors (psutil, etc.) are okay for this test
    if "tkinter" not in str(e).lower():
        print("SUCCESS: No tkinter ImportError")
    else:
        print(f"FAIL: tkinter ImportError: {e}")
except SystemExit as e:
    # SystemExit from the tkinter error handler
    print(f"FAIL: SystemExit raised (code {e.code})")
'''
        
        result = subprocess.run(
            [sys.executable, '-c', test_script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Should see SUCCESS in output
        self.assertIn('SUCCESS', result.stdout, 
                      "GUI module should import without tkinter error when tkinter is available")
        self.assertNotIn('FAIL', result.stdout,
                         "Should not fail with tkinter error when tkinter is available")


if __name__ == '__main__':
    unittest.main()
