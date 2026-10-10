#!/usr/bin/env python3
"""
Unit tests for the error log collection script
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from collect_errorlogs import ErrorLogCollector


class TestErrorLogCollector(unittest.TestCase):
    """Test the ErrorLogCollector class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.collector = ErrorLogCollector(output_file=str(self.test_dir / "test_output.txt"))
        # Override project root for testing
        self.collector.project_root = self.test_dir
        
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_add_section(self):
        """Test adding a section to the collector"""
        self.collector.add_section("Test Section", "Test content", "test_source")
        self.assertEqual(len(self.collector.sections), 1)
        self.assertEqual(self.collector.sections[0]['title'], "Test Section")
        self.assertEqual(self.collector.sections[0]['content'], "Test content")
        self.assertEqual(self.collector.sections[0]['source'], "test_source")
    
    def test_collect_file_contents(self):
        """Test collecting file contents"""
        # Create a test file
        test_file = self.test_dir / "test.log"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")
        
        result = self.collector.collect_file_contents(test_file)
        self.assertTrue(result)
        self.assertEqual(len(self.collector.sections), 1)
        self.assertIn("Line 1", self.collector.sections[0]['content'])
    
    def test_collect_file_with_max_lines(self):
        """Test collecting file with line limit"""
        # Create a test file with many lines
        test_file = self.test_dir / "test.log"
        test_file.write_text("\n".join([f"Line {i}" for i in range(100)]))
        
        result = self.collector.collect_file_contents(test_file, max_lines=10)
        self.assertTrue(result)
        self.assertIn("truncated", self.collector.sections[0]['content'])
    
    def test_collect_nonexistent_file(self):
        """Test collecting a file that doesn't exist"""
        result = self.collector.collect_file_contents(self.test_dir / "nonexistent.log")
        self.assertFalse(result)
    
    def test_collect_directory_files(self):
        """Test collecting files from a directory"""
        # Create test directory with files
        test_subdir = self.test_dir / "logs"
        test_subdir.mkdir()
        (test_subdir / "log1.txt").write_text("Log 1 content")
        (test_subdir / "log2.txt").write_text("Log 2 content")
        
        self.collector.collect_directory_files(test_subdir, "*.txt")
        self.assertEqual(len(self.collector.sections), 2)
    
    def test_write_output(self):
        """Test writing output file"""
        self.collector.add_section("Section 1", "Content 1")
        self.collector.add_section("Section 2", "Content 2")
        
        result = self.collector.write_output()
        self.assertTrue(result)
        
        output_file = self.test_dir / "test_output.txt"
        self.assertTrue(output_file.exists())
        
        content = output_file.read_text()
        self.assertIn("ERROR LOGS AND DEBUG INFORMATION", content)
        self.assertIn("TABLE OF CONTENTS", content)
        self.assertIn("Section 1", content)
        self.assertIn("Section 2", content)
    
    def test_collect_environment_info(self):
        """Test collecting environment information"""
        self.collector.collect_environment_info()
        self.assertEqual(len(self.collector.sections), 1)
        self.assertIn("ENVIRONMENT INFORMATION", self.collector.sections[0]['content'])
        self.assertIn("Python Version", self.collector.sections[0]['content'])


class TestScriptExecution(unittest.TestCase):
    """Test the script can be executed"""
    
    def test_script_exists(self):
        """Test that the script file exists"""
        script_path = Path(__file__).parent / "collect_errorlogs.py"
        self.assertTrue(script_path.exists())
    
    def test_script_is_executable(self):
        """Test that the script is executable"""
        script_path = Path(__file__).parent / "collect_errorlogs.py"
        self.assertTrue(os.access(script_path, os.X_OK))
    
    def test_shell_script_exists(self):
        """Test that the convenience shell script exists"""
        script_path = Path(__file__).parent / "collect_logs.sh"
        self.assertTrue(script_path.exists())
    
    def test_shell_script_is_executable(self):
        """Test that the shell script is executable"""
        script_path = Path(__file__).parent / "collect_logs.sh"
        self.assertTrue(os.access(script_path, os.X_OK))


if __name__ == '__main__':
    unittest.main()
