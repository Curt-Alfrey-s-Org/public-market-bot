#!/usr/bin/env python3
"""
Test to verify stat module import in schwab_auth.py
Regression test for issue: "name 'stat' is not defined"
"""

import unittest
import os
import tempfile


class TestSchwabAuthStatImport(unittest.TestCase):
    """Test that schwab_auth correctly imports and uses the stat module"""
    
    def setUp(self):
        """Import the module for testing"""
        import schwab_auth
        self.schwab_auth = schwab_auth
    
    def test_module_imports_without_error(self):
        """Test that schwab_auth module imports without NameError"""
        # If we get here, the import in setUp succeeded
        self.assertIsNotNone(self.schwab_auth)
    
    def test_check_file_permissions_secure(self):
        """Test _check_file_permissions correctly identifies secure permissions"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(b"test data")
        
        try:
            # Set secure permissions (0o600)
            os.chmod(tmp_path, 0o600)
            result = self.schwab_auth._check_file_permissions(tmp_path)
            self.assertTrue(result, "Should return True for 0o600 permissions")
        finally:
            os.unlink(tmp_path)
    
    def test_check_file_permissions_insecure(self):
        """Test _check_file_permissions correctly rejects insecure permissions"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(b"test data")
        
        try:
            # Set insecure permissions (0o644)
            os.chmod(tmp_path, 0o644)
            result = self.schwab_auth._check_file_permissions(tmp_path)
            self.assertFalse(result, "Should return False for 0o644 permissions")
        finally:
            os.unlink(tmp_path)
    
    def test_fix_file_permissions(self):
        """Test _fix_file_permissions correctly sets secure permissions"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(b"test data")
        
        try:
            # Set insecure permissions
            os.chmod(tmp_path, 0o644)
            
            # Fix permissions
            result = self.schwab_auth._fix_file_permissions(tmp_path)
            self.assertTrue(result, "Should return True on successful fix")
            
            # Verify permissions were fixed
            import stat
            file_stats = os.stat(tmp_path)
            file_mode = stat.S_IMODE(file_stats.st_mode)
            self.assertEqual(file_mode, 0o600, "Permissions should be set to 0o600")
        finally:
            os.unlink(tmp_path)
    
    def test_stat_module_available(self):
        """Test that stat module functionality is available in schwab_auth"""
        # This test would fail with NameError if stat is not imported
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(b"test")
        
        try:
            os.chmod(tmp_path, 0o600)
            # This call uses stat.S_IMODE internally
            # Would raise NameError if stat not imported
            result = self.schwab_auth._check_file_permissions(tmp_path)
            self.assertIsNotNone(result)
        finally:
            os.unlink(tmp_path)


if __name__ == '__main__':
    unittest.main()
