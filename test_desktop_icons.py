#!/usr/bin/env python3
"""
Test suite for desktop icon functionality.
Validates that desktop files are properly configured and executable.
"""

import unittest
import os
import stat
import configparser


class TestDesktopIcons(unittest.TestCase):
    """Test desktop icon files and installation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.repo_root = os.path.dirname(os.path.abspath(__file__))
        self.desktop_files = [
            'market-pie5-bot.desktop',
            'market-pie5-web-gui.desktop'
        ]
        self.start_scripts = [
            'start_bot.sh',
            'start_web_gui.sh'
        ]
    
    def test_desktop_files_exist(self):
        """Test that desktop files exist in the repository."""
        for desktop_file in self.desktop_files:
            path = os.path.join(self.repo_root, desktop_file)
            self.assertTrue(
                os.path.exists(path),
                f"Desktop file {desktop_file} should exist"
            )
    
    def test_desktop_files_are_executable(self):
        """Test that desktop files have executable permission."""
        for desktop_file in self.desktop_files:
            path = os.path.join(self.repo_root, desktop_file)
            file_stat = os.stat(path)
            is_executable = bool(file_stat.st_mode & stat.S_IXUSR)
            self.assertTrue(
                is_executable,
                f"Desktop file {desktop_file} should be executable (chmod +x)"
            )
    
    def test_desktop_files_valid_syntax(self):
        """Test that desktop files have valid INI syntax."""
        for desktop_file in self.desktop_files:
            path = os.path.join(self.repo_root, desktop_file)
            parser = configparser.ConfigParser()
            
            # Should parse without errors
            files_read = parser.read(path)
            self.assertTrue(
                files_read,
                f"Desktop file {desktop_file} should be parseable"
            )
            
            # Should have [Desktop Entry] section
            self.assertIn(
                'Desktop Entry', parser.sections(),
                f"Desktop file {desktop_file} should have [Desktop Entry] section"
            )
    
    def test_desktop_files_required_fields(self):
        """Test that desktop files have all required fields."""
        required_fields = ['Type', 'Name', 'Exec']
        
        for desktop_file in self.desktop_files:
            path = os.path.join(self.repo_root, desktop_file)
            parser = configparser.ConfigParser()
            parser.read(path)
            
            desktop_entry = parser['Desktop Entry']
            for field in required_fields:
                self.assertIn(
                    field, desktop_entry,
                    f"Desktop file {desktop_file} should have '{field}' field"
                )
    
    def test_desktop_files_type_is_application(self):
        """Test that desktop files have Type=Application."""
        for desktop_file in self.desktop_files:
            path = os.path.join(self.repo_root, desktop_file)
            parser = configparser.ConfigParser()
            parser.read(path)
            
            self.assertEqual(
                parser['Desktop Entry']['Type'], 'Application',
                f"Desktop file {desktop_file} should have Type=Application"
            )
    
    def test_desktop_files_exec_references_valid_script(self):
        """Test that Exec field references a valid script."""
        for desktop_file in self.desktop_files:
            path = os.path.join(self.repo_root, desktop_file)
            parser = configparser.ConfigParser()
            parser.read(path)
            
            exec_line = parser['Desktop Entry']['Exec']
            # Extract script name from Exec line (handle potential arguments)
            # Format: /home/pi/market-pie5-bot/start_bot.sh [args]
            script_name = os.path.basename(exec_line.split()[0])
            
            self.assertIn(
                script_name, self.start_scripts,
                f"Desktop file {desktop_file} should reference a valid start script"
            )
    
    def test_start_scripts_exist(self):
        """Test that referenced start scripts exist."""
        for script in self.start_scripts:
            path = os.path.join(self.repo_root, script)
            self.assertTrue(
                os.path.exists(path),
                f"Start script {script} should exist"
            )
    
    def test_start_scripts_are_executable(self):
        """Test that start scripts are executable."""
        for script in self.start_scripts:
            path = os.path.join(self.repo_root, script)
            file_stat = os.stat(path)
            is_executable = bool(file_stat.st_mode & stat.S_IXUSR)
            self.assertTrue(
                is_executable,
                f"Start script {script} should be executable"
            )
    
    def test_start_scripts_have_shebang(self):
        """Test that start scripts have proper shebang."""
        for script in self.start_scripts:
            path = os.path.join(self.repo_root, script)
            with open(path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
            
            self.assertTrue(
                first_line.startswith('#!/'),
                f"Start script {script} should have shebang"
            )
            self.assertIn(
                'bash', first_line.lower(),
                f"Start script {script} should use bash"
            )
    
    def test_desktop_files_have_terminal_true(self):
        """Test that desktop files have Terminal=true for error visibility."""
        for desktop_file in self.desktop_files:
            path = os.path.join(self.repo_root, desktop_file)
            parser = configparser.ConfigParser()
            parser.read(path)
            
            terminal_value = parser['Desktop Entry'].get('Terminal', 'false')
            self.assertEqual(
                terminal_value.lower(), 'true',
                f"Desktop file {desktop_file} should have Terminal=true"
            )
    
    def test_install_script_exists_and_executable(self):
        """Test that install_desktop_icons.sh exists and is executable."""
        install_script = os.path.join(self.repo_root, 'install_desktop_icons.sh')
        
        self.assertTrue(
            os.path.exists(install_script),
            "install_desktop_icons.sh should exist"
        )
        
        file_stat = os.stat(install_script)
        is_executable = bool(file_stat.st_mode & stat.S_IXUSR)
        self.assertTrue(
            is_executable,
            "install_desktop_icons.sh should be executable"
        )
    
    def test_desktop_files_have_proper_categories(self):
        """Test that desktop files have appropriate categories."""
        expected_categories = ['Finance', 'Office']
        
        for desktop_file in self.desktop_files:
            path = os.path.join(self.repo_root, desktop_file)
            parser = configparser.ConfigParser()
            parser.read(path)
            
            if 'Categories' in parser['Desktop Entry']:
                categories = parser['Desktop Entry']['Categories']
                # Check if at least one expected category is present
                has_expected_category = any(
                    cat in categories for cat in expected_categories
                )
                self.assertTrue(
                    has_expected_category,
                    f"Desktop file {desktop_file} should have Finance or Office category"
                )
    
    def test_custom_icon_file_exists(self):
        """Test that the custom icon file exists."""
        icon_path = os.path.join(self.repo_root, 'market-pie5-icon.svg')
        self.assertTrue(
            os.path.exists(icon_path),
            "Custom icon file market-pie5-icon.svg should exist"
        )
        
        # Check file is not empty
        file_size = os.path.getsize(icon_path)
        self.assertGreater(
            file_size, 0,
            "Icon file should not be empty"
        )
    
    def test_desktop_files_reference_custom_icon(self):
        """Test that desktop files reference the custom icon."""
        for desktop_file in self.desktop_files:
            path = os.path.join(self.repo_root, desktop_file)
            parser = configparser.ConfigParser()
            parser.read(path)
            
            if 'Icon' in parser['Desktop Entry']:
                icon_value = parser['Desktop Entry']['Icon']
                self.assertIn(
                    'market-pie5-icon.svg', icon_value,
                    f"Desktop file {desktop_file} should reference custom icon"
                )



if __name__ == '__main__':
    unittest.main()

