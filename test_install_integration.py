#!/usr/bin/env python3
"""
Test suite for install.sh script integration features.
Validates desktop icon and ClamAV integration in install script.
"""

import unittest
import os
import subprocess
from pathlib import Path
import pytest


@pytest.mark.integration
class TestInstallScriptIntegration(unittest.TestCase):
    """Test install.sh script integration features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.repo_root = Path(__file__).parent.absolute()
        self.install_script = self.repo_root / 'install.sh'
    
    def test_install_script_exists(self):
        """Test that install.sh exists."""
        self.assertTrue(
            self.install_script.exists(),
            "install.sh should exist in repository root"
        )
    
    def test_install_script_is_executable(self):
        """Test that install.sh is executable."""
        self.assertTrue(
            os.access(self.install_script, os.X_OK),
            "install.sh should be executable"
        )
    
    def test_install_script_has_desktop_icon_section(self):
        """Test that install.sh includes desktop icon installation."""
        content = self.install_script.read_text()
        
        # Check for desktop icon installation section
        self.assertIn(
            'Desktop Icons Installation',
            content,
            "install.sh should have Desktop Icons Installation section"
        )
        
        # Check for desktop icon prompt
        self.assertIn(
            'Install desktop icons?',
            content,
            "install.sh should prompt for desktop icon installation"
        )
        
        # Check for desktop icon installation logic
        self.assertIn(
            'market-pie5-web-gui.desktop',
            content,
            "install.sh should reference web GUI desktop file"
        )
        
        self.assertIn(
            'market-pie5-bot.desktop',
            content,
            "install.sh should reference bot desktop file"
        )
        
        # Check for desktop database update
        self.assertIn(
            'update-desktop-database',
            content,
            "install.sh should update desktop database"
        )
    
    def test_install_script_has_clamav_section(self):
        """Test that install.sh includes ClamAV installation."""
        content = self.install_script.read_text()
        
        # Check for ClamAV installation section
        self.assertIn(
            'ClamAV Security Scanning',
            content,
            "install.sh should have ClamAV Security Scanning section"
        )
        
        # Check for ClamAV prompt
        self.assertIn(
            'Install ClamAV with automatic updates?',
            content,
            "install.sh should prompt for ClamAV installation"
        )
        
        # Check for ClamAV package installation
        self.assertIn(
            'clamav',
            content,
            "install.sh should reference clamav package"
        )
        
        self.assertIn(
            'clamav-freshclam',
            content,
            "install.sh should reference clamav-freshclam for automatic updates"
        )
        
        # Check for freshclam service management
        self.assertIn(
            'systemctl enable clamav-freshclam',
            content,
            "install.sh should enable clamav-freshclam service"
        )
        
        self.assertIn(
            'systemctl start clamav-freshclam',
            content,
            "install.sh should start clamav-freshclam service"
        )
    
    def test_install_script_syntax(self):
        """Test that install.sh has valid bash syntax."""
        result = subprocess.run(
            ['bash', '-n', str(self.install_script)],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(
            result.returncode, 0,
            f"install.sh should have valid bash syntax. Error: {result.stderr}"
        )
    
    def test_desktop_icon_script_exists(self):
        """Test that install_desktop_icons.sh still exists as standalone option."""
        desktop_icon_script = self.repo_root / 'install_desktop_icons.sh'
        self.assertTrue(
            desktop_icon_script.exists(),
            "install_desktop_icons.sh should still exist as standalone option"
        )
    
    def test_install_script_mentions_manual_installation(self):
        """Test that install.sh mentions manual installation options."""
        content = self.install_script.read_text()
        
        # Check for reference to standalone desktop icon installer
        self.assertIn(
            'install_desktop_icons.sh',
            content,
            "install.sh should mention install_desktop_icons.sh for manual installation"
        )


class TestInstallDocumentation(unittest.TestCase):
    """Test that documentation reflects install script changes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.repo_root = Path(__file__).parent.absolute()
        self.readme = self.repo_root / 'README.md'
        self.security_md = self.repo_root / 'SECURITY.md'
    
    def test_readme_documents_desktop_icons(self):
        """Test that README.md documents desktop icon installation."""
        content = self.readme.read_text()
        
        self.assertIn(
            'Desktop Icons',
            content,
            "README.md should mention Desktop Icons"
        )
    
    def test_readme_documents_clamav(self):
        """Test that README.md documents ClamAV installation."""
        content = self.readme.read_text()
        
        self.assertIn(
            'ClamAV',
            content,
            "README.md should mention ClamAV"
        )
        
        self.assertIn(
            'automatic updates',
            content.lower(),
            "README.md should mention automatic updates for ClamAV"
        )
    
    def test_security_md_documents_clamav(self):
        """Test that SECURITY.md documents ClamAV security feature."""
        content = self.security_md.read_text()
        
        self.assertIn(
            'ClamAV',
            content,
            "SECURITY.md should mention ClamAV"
        )
        
        self.assertIn(
            'freshclam',
            content,
            "SECURITY.md should mention freshclam daemon"
        )


if __name__ == '__main__':
    unittest.main()
