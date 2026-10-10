"""
Import and Module Validation Tests
Tests that all modules can be imported without errors, including circular import detection
"""

import os
import sys
import importlib
import traceback
from typing import List, Dict, Any
from tests.framework.base_test import BaseTestModule, TestResult, TestStatus

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _api_deps_available() -> bool:
    """True if FastAPI and API deps are installed (e.g. in API venv)."""
    try:
        import fastapi  # noqa: F401
        return True
    except ModuleNotFoundError:
        return False


class ImportValidationTest(BaseTestModule):
    """Test module imports and detect circular imports"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        super().__init__("Import Validation", api_base_url)
        self.import_errors: List[Dict[str, Any]] = []
    
    def test_api_main_import(self) -> TestResult:
        """Test that api.main can be imported without errors"""
        if not _api_deps_available():
            return self.run_test("API Main Import", lambda: TestResult(
                "API Main Import",
                TestStatus.SKIP,
                "API dependencies not installed (pip install -r requirements-api.txt)"
            ))
        def _test():
            try:
                # Try to import api.main - this will catch circular imports
                import api.main
                # Try to access the app object
                if hasattr(api.main, 'app'):
                    return True
                else:
                    return TestResult(
                        "API Main Import",
                        TestStatus.FAIL,
                        "api.main imported but 'app' object not found"
                    )
            except ImportError as e:
                error_msg = str(e)
                if "partially initialized" in error_msg or "circular" in error_msg.lower():
                    return TestResult(
                        "API Main Import",
                        TestStatus.FAIL,
                        f"Circular import detected: {error_msg}\n{traceback.format_exc()}"
                    )
                return TestResult(
                    "API Main Import",
                    TestStatus.FAIL,
                    f"Import error: {error_msg}\n{traceback.format_exc()}"
                )
            except Exception as e:
                return TestResult(
                    "API Main Import",
                    TestStatus.FAIL,
                    f"Unexpected error importing api.main: {str(e)}\n{traceback.format_exc()}"
                )
        
        return self.run_test("API Main Import", _test)
    
    def test_route_imports(self) -> TestResult:
        """Test that all route modules can be imported"""
        if not _api_deps_available():
            return self.run_test("Route Imports", lambda: TestResult(
                "Route Imports",
                TestStatus.SKIP,
                "API dependencies not installed (pip install -r requirements-api.txt)"
            ))
        route_modules = [
            "api.routes.bot",
            "api.routes.stats",
            "api.routes.settings",
            "api.routes.trades",
            "api.routes.system",
            "api.routes.messages",
            "api.routes.ai",
            "api.routes.tax",
            "api.routes.logs",
        ]
        
        failed_imports = []
        
        def _test():
            for module_name in route_modules:
                try:
                    # Try to import the module
                    module = importlib.import_module(module_name)
                    # Check if it has a router
                    if not hasattr(module, 'router'):
                        failed_imports.append(f"{module_name}: No 'router' attribute")
                except ImportError as e:
                    error_msg = str(e)
                    if "partially initialized" in error_msg or "circular" in error_msg.lower():
                        failed_imports.append(f"{module_name}: Circular import - {error_msg}")
                    else:
                        failed_imports.append(f"{module_name}: Import error - {error_msg}")
                except Exception as e:
                    failed_imports.append(f"{module_name}: Unexpected error - {str(e)}")
            
            if failed_imports:
                return TestResult(
                    "Route Imports",
                    TestStatus.FAIL,
                    f"Failed to import routes:\n" + "\n".join(f"  - {err}" for err in failed_imports)
                )
            return True
        
        return self.run_test("Route Imports", _test)
    
    def test_utils_import(self) -> TestResult:
        """Test that api.utils can be imported and has required functions"""
        def _test():
            try:
                import api.utils
                # Check for required functions
                required_funcs = ['get_bot_instance', 'set_bot_instance']
                missing = [f for f in required_funcs if not hasattr(api.utils, f)]
                if missing:
                    return TestResult(
                        "Utils Import",
                        TestStatus.FAIL,
                        f"api.utils missing required functions: {', '.join(missing)}"
                    )
                return True
            except ImportError as e:
                return TestResult(
                    "Utils Import",
                    TestStatus.FAIL,
                    f"Failed to import api.utils: {str(e)}\n{traceback.format_exc()}"
                )
            except Exception as e:
                return TestResult(
                    "Utils Import",
                    TestStatus.FAIL,
                    f"Unexpected error importing api.utils: {str(e)}\n{traceback.format_exc()}"
                )
        
        return self.run_test("Utils Import", _test)
    
    def test_circular_import_patterns(self) -> TestResult:
        """Check for common circular import patterns in route files"""
        route_files = [
            "api/routes/bot.py",
            "api/routes/stats.py",
            "api/routes/settings.py",
            "api/routes/trades.py",
            "api/routes/system.py",
            "api/routes/messages.py",
            "api/routes/ai.py",
            "api/routes/tax.py",
            "api/routes/logs.py",
        ]
        
        problematic_imports = []
        
        def _test():
            for route_file in route_files:
                file_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    route_file
                )
                if not os.path.exists(file_path):
                    continue
                
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        # Check for problematic import pattern
                        if 'from api.main import get_bot_instance' in content:
                            problematic_imports.append(
                                f"{route_file}: Uses 'from api.main import get_bot_instance' "
                                f"(should use 'from api.utils import get_bot_instance')"
                            )
                except Exception as e:
                    problematic_imports.append(f"{route_file}: Error reading file - {str(e)}")
            
            if problematic_imports:
                return TestResult(
                    "Circular Import Patterns",
                    TestStatus.FAIL,
                    "Found problematic import patterns that may cause circular imports:\n" +
                    "\n".join(f"  - {err}" for err in problematic_imports)
                )
            return True
        
        return self.run_test("Circular Import Patterns", _test)
    
    def test_bot_manager_import(self) -> TestResult:
        """Test that bot_manager can be imported"""
        def _test():
            try:
                import api.bot_manager
                return True
            except ImportError as e:
                return TestResult(
                    "Bot Manager Import",
                    TestStatus.FAIL,
                    f"Failed to import api.bot_manager: {str(e)}\n{traceback.format_exc()}"
                )
            except Exception as e:
                return TestResult(
                    "Bot Manager Import",
                    TestStatus.FAIL,
                    f"Unexpected error importing api.bot_manager: {str(e)}\n{traceback.format_exc()}"
                )
        
        return self.run_test("Bot Manager Import", _test)
    
    def test_critical_modules_initialization(self) -> TestResult:
        """Test that critical modules can be initialized without errors"""
        if not _api_deps_available():
            return self.run_test("Critical Modules Initialization", lambda: TestResult(
                "Critical Modules Initialization",
                TestStatus.SKIP,
                "API dependencies not installed (pip install -r requirements-api.txt)"
            ))
        def _test():
            errors = []
            
            # Test api.utils initialization
            try:
                import api.utils
                # Try to call get_bot_instance (should return None if bot not started, but shouldn't error)
                bot = api.utils.get_bot_instance()
            except Exception as e:
                errors.append(f"api.utils initialization: {str(e)}")
            
            # Test that we can import all routes together (simulates what api.main does)
            try:
                from api.routes import bot, stats, settings, trades, system, messages, ai, tax, logs
            except ImportError as e:
                error_msg = str(e)
                if "partially initialized" in error_msg or "circular" in error_msg.lower():
                    errors.append(f"Circular import when importing all routes: {error_msg}")
                else:
                    errors.append(f"Error importing routes: {error_msg}")
            except Exception as e:
                errors.append(f"Unexpected error importing routes: {str(e)}")
            
            if errors:
                return TestResult(
                    "Critical Modules Initialization",
                    TestStatus.FAIL,
                    "Failed to initialize critical modules:\n" + "\n".join(f"  - {err}" for err in errors)
                )
            return True
        
        return self.run_test("Critical Modules Initialization", _test)
    
    def run(self) -> List[TestResult]:
        """Run all import validation tests"""
        self.log("Starting import validation tests...")
        
        tests = [
            self.test_circular_import_patterns,  # Run first - fastest check
            self.test_utils_import,
            self.test_route_imports,
            self.test_bot_manager_import,
            self.test_api_main_import,  # Run last - most comprehensive
            self.test_critical_modules_initialization,
        ]
        
        for test_func in tests:
            try:
                result = test_func()
                if result.status == TestStatus.FAIL:
                    self.log(f"FAILED: {result.name} - {result.message}", "ERROR")
                elif result.status == TestStatus.SKIP:
                    self.log(f"SKIPPED: {result.name} - {result.message}", "INFO")
                else:
                    self.log(f"PASSED: {result.name}", "INFO")
            except Exception as e:
                self.log(f"ERROR running test: {str(e)}", "ERROR")
                self.results.append(TestResult(
                    test_func.__name__,
                    TestStatus.FAIL,
                    f"Test execution error: {str(e)}\n{traceback.format_exc()}"
                ))
        
        self.log(f"Import validation complete: {len([r for r in self.results if r.status == TestStatus.PASS])}/{len(self.results)} passed")
        return self.results
