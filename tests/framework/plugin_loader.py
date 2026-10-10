"""
Plugin Loader
Dynamically loads test modules and plugins
"""

import os
import sys
import importlib
import inspect
from typing import List, Type, Dict, Optional
from pathlib import Path

from .base_test import BaseTestModule


class PluginLoader:
    """Loads and manages test plugins"""
    
    def __init__(self, plugin_dirs: List[str] = None):
        self.plugin_dirs = plugin_dirs or []
        self.loaded_plugins: Dict[str, Type[BaseTestModule]] = {}
    
    def discover_plugins(self, base_dir: str) -> List[str]:
        """Discover all plugin modules in directory"""
        plugins = []
        base_path = Path(base_dir)
        
        if not base_path.exists():
            return plugins
        
        # Look for Python files in plugin directories
        for plugin_dir in self.plugin_dirs:
            plugin_path = base_path / plugin_dir
            if plugin_path.exists() and plugin_path.is_dir():
                for file in plugin_path.glob("*.py"):
                    if file.name != "__init__.py":
                        module_path = f"{plugin_dir.replace('/', '.')}.{file.stem}"
                        plugins.append(module_path)
        
        return plugins
    
    def load_plugin(self, module_path: str) -> Optional[Type[BaseTestModule]]:
        """Load a plugin module"""
        try:
            # Add base directory to path
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if base_dir not in sys.path:
                sys.path.insert(0, base_dir)
            
            module = importlib.import_module(module_path)
            
            # Find BaseTestModule subclasses
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseTestModule) and 
                    obj != BaseTestModule):
                    return obj
            
            return None
        except Exception as e:
            print(f"Error loading plugin {module_path}: {e}")
            return None
    
    def load_all_plugins(self, base_dir: str) -> Dict[str, Type[BaseTestModule]]:
        """Load all discovered plugins"""
        plugin_modules = self.discover_plugins(base_dir)
        
        for module_path in plugin_modules:
            plugin_class = self.load_plugin(module_path)
            if plugin_class:
                self.loaded_plugins[plugin_class.__name__] = plugin_class
        
        return self.loaded_plugins
    
    def get_plugin(self, name: str) -> Optional[Type[BaseTestModule]]:
        """Get a loaded plugin by name"""
        return self.loaded_plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """List all loaded plugin names"""
        return list(self.loaded_plugins.keys())
