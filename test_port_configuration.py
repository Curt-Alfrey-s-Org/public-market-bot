#!/usr/bin/env python3
"""
Test port configuration to ensure correct ports are set for market bot
API should be on port 8000, Frontend should be on port 5173
"""

import unittest
import os
import re


class TestPortConfiguration(unittest.TestCase):
    """Test that port configuration is correct across all files"""

    def setUp(self):
        """Set up test fixtures"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))

    def test_start_web_gui_has_correct_api_port(self):
        """Test that start_web_gui.sh uses port 8000 for API"""
        script_path = os.path.join(self.project_root, 'start_web_gui.sh')
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Check for port 8000 in API startup
        self.assertIn('--port 8000', content,
                      "start_web_gui.sh should start API on port 8000")
        
        # Check for port 8000 in health check
        self.assertIn('localhost:8000/api/health', content,
                     "start_web_gui.sh should check API health on port 8000")
        
        # Make sure wrong port 8001 is not present
        self.assertNotIn('8001', content,
                        "start_web_gui.sh should not reference port 8001")

    def test_start_web_gui_has_correct_frontend_port(self):
        """Test that start_web_gui.sh uses port 5173 for frontend"""
        script_path = os.path.join(self.project_root, 'start_web_gui.sh')
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Check for port 5173 in output message
        self.assertIn('localhost:5173', content,
                     "start_web_gui.sh should reference frontend on port 5173")
        
        # Check the comment mentions 5173
        self.assertIn('port 5173', content.lower(),
                     "start_web_gui.sh should mention port 5173 in comments")
        
        # Make sure wrong port 3001 is not present
        self.assertNotIn('3001', content,
                        "start_web_gui.sh should not reference port 3001")

    def test_vite_config_has_correct_port(self):
        """Test that vite.config.ts is configured for port 5173"""
        vite_config_path = os.path.join(self.project_root, 'frontend', 'vite.config.ts')
        
        if not os.path.exists(vite_config_path):
            self.skipTest("vite.config.ts not found")
        
        with open(vite_config_path, 'r') as f:
            content = f.read()
        
        # Check for port 5173
        self.assertIn('port: 5173', content,
                     "vite.config.ts should use port 5173")

    def test_api_main_has_correct_cors_origins(self):
        """Test that api/main.py CORS allows port 5173"""
        api_main_path = os.path.join(self.project_root, 'api', 'main.py')
        
        if not os.path.exists(api_main_path):
            self.skipTest("api/main.py not found")
        
        with open(api_main_path, 'r') as f:
            content = f.read()
        
        # Check for port 5173 in CORS origins
        self.assertIn('localhost:5173', content,
                     "api/main.py should allow CORS from localhost:5173")

    def test_api_main_default_port_is_8000(self):
        """Test that api/main.py defaults to port 8000"""
        api_main_path = os.path.join(self.project_root, 'api', 'main.py')
        
        if not os.path.exists(api_main_path):
            self.skipTest("api/main.py not found")
        
        with open(api_main_path, 'r') as f:
            content = f.read()
        
        # Check for default port 8000
        # Looking for pattern like: port = int(os.getenv("API_PORT", "8000"))
        port_pattern = re.search(r'API_PORT["\']?,\s*["\']?(\d+)', content)
        if port_pattern:
            port = port_pattern.group(1)
            self.assertEqual(port, '8000',
                           "api/main.py should default to port 8000")

    def test_master_setup_has_correct_port_documentation(self):
        """Test that master_setup.sh documents correct ports"""
        script_path = os.path.join(self.project_root, 'master_setup.sh')
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Check for port 8000 documentation
        self.assertIn('8000', content,
                     "master_setup.sh should document API port 8000")
        
        # Check for port 5173 documentation
        self.assertIn('5173', content,
                     "master_setup.sh should document frontend port 5173")

    def test_no_references_to_wrong_ports(self):
        """Test that there are no references to wrong ports in main scripts"""
        files_to_check = [
            'start_web_gui.sh',
            'master_setup.sh'
        ]
        
        for filename in files_to_check:
            filepath = os.path.join(self.project_root, filename)
            if not os.path.exists(filepath):
                continue
            
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Should not contain port 8001 (wrong API port)
            self.assertNotIn('8001', content,
                           f"{filename} should not reference port 8001")
            
            # Should not contain port 3001 (wrong frontend port)
            self.assertNotIn('3001', content,
                           f"{filename} should not reference port 3001")

    def test_port_management_doc_has_correct_ports(self):
        """Test that PORT_MANAGEMENT.md documents correct ports"""
        doc_path = os.path.join(self.project_root, 'docs', 'PORT_MANAGEMENT.md')
        
        if not os.path.exists(doc_path):
            self.skipTest("docs/PORT_MANAGEMENT.md not found")
        
        with open(doc_path, 'r') as f:
            content = f.read()
        
        # Check for port 8000
        self.assertIn('8000', content,
                     "PORT_MANAGEMENT.md should document API port 8000")
        
        # Check for port 5173
        self.assertIn('5173', content,
                     "PORT_MANAGEMENT.md should document frontend port 5173")


if __name__ == '__main__':
    unittest.main()
