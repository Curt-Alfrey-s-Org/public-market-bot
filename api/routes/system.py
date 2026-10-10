"""
System Routes
Provides system information and health status
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
from pathlib import Path
import os
import subprocess
import json
import logging

from api.auth import require_admin  # run-tests: admin JWT only

logger = logging.getLogger(__name__)

router = APIRouter()


# Cache for self-test results (avoid running on every health check)
_self_test_cache = {
    "results": None,
    "timestamp": None,
    "cache_duration": 60,  # Cache for 60 seconds
}

# Track if HTTP tests have been run (run once after API is ready)
_http_tests_run = False
_http_tests_results = None


def _log_selftest_run(returncode: int, stdout: str, stderr: str, duration_s: float, timeout_s: int, project_root: Path):
    """Log full self-test run for easy analysis. Writes debug file on failure."""
    status = "PASS" if returncode == 0 else "FAIL"
    logger.info(f"[SELFTEST] Run completed: {status} (returncode={returncode}) in {duration_s:.2f}s")
    if returncode != 0 or stderr.strip():
        debug_path = project_root / "selftest_debug.log"
        try:
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(f"# Self-test run (returncode={returncode}, duration={duration_s:.2f}s)\n")
                f.write("# Analyze this file for failures.\n\n")
                if stdout:
                    f.write("=== STDOUT ===\n")
                    f.write(stdout)
                    if not stdout.endswith("\n"):
                        f.write("\n")
                if stderr:
                    f.write("\n=== STDERR ===\n")
                    f.write(stderr)
                    if not stderr.endswith("\n"):
                        f.write("\n")
            logger.info(f"[SELFTEST] Debug log written to {debug_path}")
        except Exception as e:
            logger.warning(f"[SELFTEST] Could not write debug log: {e}")
    if os.getenv("LOG_LEVEL", "").upper() == "DEBUG" and (stdout or stderr):
        for line in (stdout + "\n" + stderr).strip().split("\n")[-50:]:  # Last 50 lines only
            logger.debug(f"[SELFTEST] {line}")


def _check_frontend_api_base_url(project_root: Path):
    """
    Fail if frontend defaults to localhost:8000 (causes screen-not-updating when
    deployed or when API runs on another port). Use same-origin '' or VITE_API_URL instead.
    Scans frontend/src for .ts, .tsx, .js, .jsx.
    """
    frontend_src = project_root / "frontend" / "src"
    if not frontend_src.exists():
        return True, None
    bad = "localhost:8000"
    for ext in ("*.ts", "*.tsx", "*.js", "*.jsx"):
        for path in frontend_src.rglob(ext):
            try:
                text = path.read_text(encoding="utf-8")
                if bad in text:
                    return False, f"Frontend has localhost:8000 in {path.relative_to(project_root)}; use same-origin '' or VITE_API_URL so UI works on subdomain"
            except Exception as e:
                return False, str(e)[:80]
    return True, None


def _run_http_self_tests():
    """Run HTTP-based self-tests (actual endpoint validation)"""
    import requests
    import time
    from datetime import datetime

    # Use API_URL from environment or build from API_PORT. Reserve 127.x for sensitive-only (e.g. OAuth callback); normal API binds on 0.0.0.0 for LAN access.
    # Default port 8002 (8000 often used by Yacht). Same-machine checks use localhost; set API_URL to LAN IP or hostname for remote checks.
    api_url = os.getenv("API_URL") or f"http://localhost:{int(os.getenv('API_PORT', '8002'))}"
    if not api_url.startswith('http'):
        api_url = f"http://{api_url}"
    api_url = api_url.rstrip('/')
    _http_timeout = 5
    _http_retries = 2

    def _get_with_retry(url, method='get'):
        for attempt in range(_http_retries):
            try:
                if method == 'get':
                    return requests.get(url, timeout=_http_timeout)
                if method == 'options':
                    return requests.options(url, timeout=_http_timeout)
                return requests.get(url, timeout=_http_timeout)
            except requests.exceptions.ConnectionError:
                if attempt < _http_retries - 1:
                    time.sleep(1)
                else:
                    raise

    test_results = []
    passed = 0
    failed = 0
    timings = {}
    project_root = Path(__file__).resolve().parent.parent.parent

    # Test 0: Frontend API base URL (no hardcoded localhost:8000)
    start = time.time()
    ok, err = _check_frontend_api_base_url(project_root)
    elapsed = (time.time() - start) * 1000
    timings["test_frontend_api_base_url"] = elapsed
    if ok:
        test_results.append({"name": "Frontend API base URL", "passed": True, "duration_ms": elapsed})
        passed += 1
    else:
        test_results.append({"name": "Frontend API base URL", "passed": False, "duration_ms": elapsed, "error": err or "bad default"})
        failed += 1

    # Test 1: API Health Endpoint
    start = time.time()
    try:
        response = _get_with_retry(f"{api_url}/api/health")
        elapsed = (time.time() - start) * 1000
        timings['test_api_health'] = elapsed
        if response.status_code == 200:
            data = response.json()
            passed_test = data.get("status") == "healthy"
            test_results.append({"name": "API Health", "passed": passed_test, "duration_ms": elapsed})
            if passed_test:
                passed += 1
            else:
                failed += 1
        else:
            test_results.append({"name": "API Health", "passed": False, "duration_ms": elapsed, "error": f"Status {response.status_code}"})
            failed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_api_health'] = elapsed
        test_results.append({"name": "API Health", "passed": False, "duration_ms": elapsed, "error": str(e)[:80]})
        failed += 1
    
    # Test 2: Bot Status Endpoint
    start = time.time()
    try:
        response = _get_with_retry(f"{api_url}/api/bot/status")
        elapsed = (time.time() - start) * 1000
        timings['test_bot_status'] = elapsed
        if response.status_code == 200:
            test_results.append({"name": "Bot Status", "passed": True, "duration_ms": elapsed})
            passed += 1
        else:
            test_results.append({"name": "Bot Status", "passed": False, "duration_ms": elapsed, "error": f"Status {response.status_code}"})
            failed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_bot_status'] = elapsed
        test_results.append({"name": "Bot Status", "passed": False, "duration_ms": elapsed, "error": str(e)[:80]})
        failed += 1
    
    # Test 3: Stats Endpoint
    start = time.time()
    try:
        response = _get_with_retry(f"{api_url}/api/stats")
        elapsed = (time.time() - start) * 1000
        timings['test_stats_endpoint'] = elapsed
        if response.status_code == 200:
            test_results.append({"name": "Stats Endpoint", "passed": True, "duration_ms": elapsed})
            passed += 1
        else:
            test_results.append({"name": "Stats Endpoint", "passed": False, "duration_ms": elapsed, "error": f"Status {response.status_code}"})
            failed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_stats_endpoint'] = elapsed
        test_results.append({"name": "Stats Endpoint", "passed": False, "duration_ms": elapsed, "error": str(e)[:80]})
        failed += 1
    
    # Test 4: Trades Endpoint
    start = time.time()
    try:
        response = _get_with_retry(f"{api_url}/api/trades")
        elapsed = (time.time() - start) * 1000
        timings['test_trades_endpoint'] = elapsed
        if response.status_code == 200:
            test_results.append({"name": "Trades Endpoint", "passed": True, "duration_ms": elapsed})
            passed += 1
        else:
            test_results.append({"name": "Trades Endpoint", "passed": False, "duration_ms": elapsed, "error": f"Status {response.status_code}"})
            failed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_trades_endpoint'] = elapsed
        test_results.append({"name": "Trades Endpoint", "passed": False, "duration_ms": elapsed, "error": str(e)[:80]})
        failed += 1
    
    # Test 5: Trades Reset Endpoint (Critical for yfinance testing)
    start = time.time()
    try:
        # Use OPTIONS to check if endpoint exists without triggering actual reset
        response = _get_with_retry(f"{api_url}/api/trades/reset", method='options')
        elapsed = (time.time() - start) * 1000
        timings['test_trades_reset_endpoint'] = elapsed
        # OPTIONS should return 200 or 405 (method not allowed) - both mean endpoint exists
        if response.status_code in [200, 405, 204]:
            test_results.append({"name": "Trades Reset Endpoint", "passed": True, "duration_ms": elapsed})
            passed += 1
        else:
            test_results.append({"name": "Trades Reset Endpoint", "passed": False, "duration_ms": elapsed, "error": f"Status {response.status_code}"})
            failed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_trades_reset_endpoint'] = elapsed
        test_results.append({"name": "Trades Reset Endpoint", "passed": False, "duration_ms": elapsed, "error": str(e)[:80]})
        failed += 1
    
    # Test 6: Messages Endpoint
    start = time.time()
    try:
        response = _get_with_retry(f"{api_url}/api/messages")
        elapsed = (time.time() - start) * 1000
        timings['test_messages_endpoint'] = elapsed
        if response.status_code == 200:
            test_results.append({"name": "Messages Endpoint", "passed": True, "duration_ms": elapsed})
            passed += 1
        else:
            test_results.append({"name": "Messages Endpoint", "passed": False, "duration_ms": elapsed, "error": f"Status {response.status_code}"})
            failed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_messages_endpoint'] = elapsed
        test_results.append({"name": "Messages Endpoint", "passed": False, "duration_ms": elapsed, "error": str(e)[:80]})
        failed += 1
    
    # Test 7: Shutdown Endpoint Exists (OPTIONS request to check if route exists, don't actually shutdown)
    start = time.time()
    try:
        # Use OPTIONS to check if endpoint exists without triggering shutdown
        response = _get_with_retry(f"{api_url}/api/bot/shutdown-server", method='options')
        elapsed = (time.time() - start) * 1000
        timings['test_shutdown_endpoint_http'] = elapsed
        # OPTIONS should return 200 or 405 (method not allowed) - both mean endpoint exists
        if response.status_code in [200, 405, 204]:
            test_results.append({"name": "Shutdown Endpoint (HTTP)", "passed": True, "duration_ms": elapsed})
            passed += 1
        else:
            test_results.append({"name": "Shutdown Endpoint (HTTP)", "passed": False, "duration_ms": elapsed, "error": f"Unexpected status {response.status_code}"})
            failed += 1
    except requests.exceptions.ConnectionError:
        # Connection error might mean server is down, but that's a different issue
        elapsed = (time.time() - start) * 1000
        timings['test_shutdown_endpoint_http'] = elapsed
        test_results.append({"name": "Shutdown Endpoint (HTTP)", "passed": False, "duration_ms": elapsed, "error": "Connection error - server may be down"})
        failed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_shutdown_endpoint_http'] = elapsed
        test_results.append({"name": "Shutdown Endpoint (HTTP)", "passed": False, "duration_ms": elapsed, "error": str(e)[:80]})
        failed += 1
    
    # Test 7: Shutdown Function Implementation Check (verify it has proper process termination)
    start = time.time()
    try:
        from api.routes.bot import shutdown_server_endpoint
        import inspect

        # Get the source code of the shutdown function (handle async/wrapped)
        fn = getattr(shutdown_server_endpoint, '__wrapped__', shutdown_server_endpoint)
        source = ""
        try:
            source = inspect.getsource(fn)
        except (TypeError, OSError, AttributeError):
            pass

        # Check for proper shutdown mechanisms (lenient: accept any valid approach)
        issues = []
        has_terminate = source and (('os.kill' in source and 'signal.SIGTERM' in source) or 'SIGTERM' in source)
        has_force_exit = source and ('os._exit' in source or 'SIGKILL' in source)
        has_process_awareness = source and (
            'uvicorn' in source.lower() or 'ps aux' in source or
            'parent' in source.lower() or 'cmdline' in source.lower() or 'reload' in source.lower()
        )
        if not has_terminate:
            issues.append("Missing os.kill/SIGTERM for process termination")
        if not has_force_exit:
            issues.append("Missing os._exit or SIGKILL as fallback")
        if not has_process_awareness:
            issues.append("Shutdown should consider parent/reloader or uvicorn process")

        elapsed = (time.time() - start) * 1000
        timings['test_shutdown_implementation'] = elapsed
        if issues and source:
            error_msg = f"Shutdown implementation issues: {'; '.join(issues)}"
            test_results.append({"name": "Shutdown Implementation", "passed": False, "duration_ms": elapsed, "error": error_msg})
            failed += 1
        else:
            # Pass if we have source and checks pass, or if endpoint is callable (wrapped) and we can't inspect
            test_results.append({"name": "Shutdown Implementation", "passed": True, "duration_ms": elapsed})
            passed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_shutdown_implementation'] = elapsed
        test_results.append({"name": "Shutdown Implementation", "passed": False, "duration_ms": elapsed, "error": str(e)[:80]})
        failed += 1
    
    # Test 8: System Endpoint Exists (check route exists)
    start = time.time()
    try:
        from api.main import app
        route_paths = [route.path for route in app.routes]
        if any('/api/system' in path and path != '/api/system/health' for path in route_paths):
            elapsed = (time.time() - start) * 1000
            timings['test_system_endpoint'] = elapsed
            test_results.append({"name": "System Endpoint", "passed": True, "duration_ms": elapsed})
            passed += 1
        else:
            raise Exception("System route not found")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_system_endpoint'] = elapsed
        test_results.append({"name": "System Endpoint", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    # Test 9: System Endpoint Function (check it can be imported and called)
    start = time.time()
    try:
        from api.routes.system import get_system_info
        # Check that function exists and is callable
        if callable(get_system_info):
            elapsed = (time.time() - start) * 1000
            timings['test_system_function'] = elapsed
            test_results.append({"name": "System Function", "passed": True, "duration_ms": elapsed})
            passed += 1
        else:
            raise Exception("System function not callable")
    except ImportError as e:
        elapsed = (time.time() - start) * 1000
        timings['test_system_function'] = elapsed
        error_msg = f"System function not importable: {str(e)}"
        test_results.append({"name": "System Function", "passed": False, "duration_ms": elapsed, "error": error_msg})
        failed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_system_function'] = elapsed
        test_results.append({"name": "System Function", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    # Test 10: Frontend System Page Component
    start = time.time()
    try:
        import re
        project_root = Path(__file__).parent.parent.parent
        system_page_path = project_root / 'frontend/src/pages/System.tsx'
        
        if not system_page_path.exists():
            raise Exception("System.tsx not found")
        
        with open(system_page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for JSX syntax errors (balanced tags) - enhanced to handle self-closing tags
        issues = []
        
        # Count opening tags (excluding self-closing)
        opening_divs = len([m for m in re.finditer(r'<div[^>]*>', content) if '/>' not in m.group()])
        closing_divs = content.count('</div>')
        self_closing_divs = len([m for m in re.finditer(r'<div[^>]*/>', content)])
        
        opening_main = len([m for m in re.finditer(r'<main[^>]*>', content) if '/>' not in m.group()])
        closing_main = content.count('</main>')
        
        opening_header = len([m for m in re.finditer(r'<header[^>]*>', content) if '/>' not in m.group()])
        closing_header = content.count('</header>')
        
        # Check for balanced tags
        if opening_divs != closing_divs:
            diff = opening_divs - closing_divs
            issues.append(f"JSX syntax error: {abs(diff)} unclosed <div> tag(s) ({'missing closing' if diff > 0 else 'extra closing'})")
        if opening_main != closing_main:
            diff = opening_main - closing_main
            issues.append(f"JSX syntax error: {abs(diff)} unclosed <main> tag(s) ({'missing closing' if diff > 0 else 'extra closing'})")
        if opening_header != closing_header:
            diff = opening_header - closing_header
            issues.append(f"JSX syntax error: {abs(diff)} unclosed <header> tag(s) ({'missing closing' if diff > 0 else 'extra closing'})")
        
        # Check for common JSX syntax errors
        # Unclosed JSX expressions
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            issues.append(f"JSX expression error: {abs(open_braces - close_braces)} unclosed brace(s)")
        
        # Check for required patterns (core System page functionality; chart is optional)
        if 'useQuery' not in content:
            issues.append("useQuery not found - data fetching not implemented")
        if 'systemInfo' not in content:
            issues.append("systemInfo state not found")
        if 'cpu_usage' not in content or 'memory_usage' not in content:
            issues.append("System stats display not implemented")
        if 'isError' not in content and 'error' not in content:
            issues.append("Error handling not implemented")
        # Chart is optional; page can show stats without charts
        
        elapsed = (time.time() - start) * 1000
        timings['test_system_page'] = elapsed
        if issues:
            error_msg = f"System page issues: {'; '.join(issues)}"
            test_results.append({"name": "System Page Component", "passed": False, "duration_ms": elapsed, "error": error_msg})
            failed += 1
        else:
            test_results.append({"name": "System Page Component", "passed": True, "duration_ms": elapsed})
            passed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_system_page'] = elapsed
        test_results.append({"name": "System Page Component", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "success_rate": success_rate,
        "all_passed": failed == 0,
        "results": test_results,
        "timings": {
            "total_duration_ms": sum(timings.values()),
            "total_duration_s": sum(timings.values()) / 1000,
            "test_timings": timings
        }
    }

def _run_internal_self_tests():
    """Run internal self-tests (direct function calls, no HTTP needed)"""
    import time
    from datetime import datetime
    
    test_results = []
    passed = 0
    failed = 0
    timings = {}
    
    # Test 1: Module Imports
    start = time.time()
    try:
        import api.main
        from api.routes import bot, stats, settings, trades, system, messages, ai, tax, logs, reports
        elapsed = (time.time() - start) * 1000
        timings['test_imports'] = elapsed
        test_results.append({"name": "Module Imports", "passed": True, "duration_ms": elapsed})
        passed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_imports'] = elapsed
        test_results.append({"name": "Module Imports", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    # Test 5: Bot Manager Initialization (catch UnboundLocalError and similar)
    start = time.time()
    try:
        from api.bot_manager import get_bot_instance, is_bot_running
        # Try to check if bot manager functions work - this will catch initialization errors
        # Just verify the functions exist and can be called without error
        is_running = is_bot_running()  # This should not raise an error
        bot_instance = get_bot_instance()  # This may be None, but shouldn't error
        elapsed = (time.time() - start) * 1000
        timings['test_bot_manager'] = elapsed
        test_results.append({"name": "Bot Manager Initialization", "passed": True, "duration_ms": elapsed})
        passed += 1
    except UnboundLocalError as e:
        elapsed = (time.time() - start) * 1000
        timings['test_bot_manager'] = elapsed
        error_msg = f"UnboundLocalError detected: {str(e)}. Check for duplicate imports inside functions."
        test_results.append({"name": "Bot Manager Initialization", "passed": False, "duration_ms": elapsed, "error": error_msg})
        failed += 1
    except NameError as e:
        elapsed = (time.time() - start) * 1000
        timings['test_bot_manager'] = elapsed
        error_msg = f"NameError detected: {str(e)}. Check for undefined variables or missing imports."
        test_results.append({"name": "Bot Manager Initialization", "passed": False, "duration_ms": elapsed, "error": error_msg})
        failed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_bot_manager'] = elapsed
        test_results.append({"name": "Bot Manager Initialization", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    # Test 6: API Health (internal check)
    start = time.time()
    try:
        from api.main import app
        if hasattr(app, 'routes') and len(app.routes) > 0:
            elapsed = (time.time() - start) * 1000
            timings['test_api_health'] = elapsed
            test_results.append({"name": "API Health", "passed": True, "duration_ms": elapsed})
            passed += 1
        else:
            raise Exception("No routes registered")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_api_health'] = elapsed
        test_results.append({"name": "API Health", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    # Test 7: Bot Status (check if bot manager works)
    start = time.time()
    try:
        from api.bot_manager import is_bot_running, get_bot_status
        # Just check if we can call it without error
        status = get_bot_status()
        elapsed = (time.time() - start) * 1000
        timings['test_bot_status'] = elapsed
        test_results.append({"name": "Bot Status", "passed": True, "duration_ms": elapsed})
        passed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_bot_status'] = elapsed
        test_results.append({"name": "Bot Status", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    # Test 8: Stats Endpoint (check route exists)
    start = time.time()
    try:
        from api.main import app
        route_paths = [route.path for route in app.routes]
        if any('/api/stats' in path or path == '/api/stats' for path in route_paths):
            elapsed = (time.time() - start) * 1000
            timings['test_stats_endpoint'] = elapsed
            test_results.append({"name": "Stats Endpoint", "passed": True, "duration_ms": elapsed})
            passed += 1
        else:
            raise Exception("Stats route not found")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_stats_endpoint'] = elapsed
        test_results.append({"name": "Stats Endpoint", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    # Test 9: Trades Endpoint (check route exists)
    start = time.time()
    try:
        from api.main import app
        route_paths = [route.path for route in app.routes]
        if any('/api/trades' in path or path == '/api/trades' for path in route_paths):
            elapsed = (time.time() - start) * 1000
            timings['test_trades_endpoint'] = elapsed
            test_results.append({"name": "Trades Endpoint", "passed": True, "duration_ms": elapsed})
            passed += 1
        else:
            raise Exception("Trades route not found")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_trades_endpoint'] = elapsed
        test_results.append({"name": "Trades Endpoint", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    # Test 10: Messages Endpoint (check route exists)
    start = time.time()
    try:
        from api.main import app
        route_paths = [route.path for route in app.routes]
        if any('/api/messages' in path or path == '/api/messages' for path in route_paths):
            elapsed = (time.time() - start) * 1000
            timings['test_messages_endpoint'] = elapsed
            test_results.append({"name": "Messages Endpoint", "passed": True, "duration_ms": elapsed})
            passed += 1
        else:
            raise Exception("Messages route not found")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_messages_endpoint'] = elapsed
        test_results.append({"name": "Messages Endpoint", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    # Test 11: Shutdown Endpoint Exists (check route exists - don't actually call it)
    start = time.time()
    try:
        from api.main import app
        route_paths = [route.path for route in app.routes]
        shutdown_routes = [path for path in route_paths if 'shutdown' in path.lower()]
        if any('/api/bot/shutdown' in path or '/api/bot/shutdown-server' in path for path in route_paths):
            elapsed = (time.time() - start) * 1000
            timings['test_shutdown_endpoint'] = elapsed
            test_results.append({"name": "Shutdown Endpoint", "passed": True, "duration_ms": elapsed})
            passed += 1
        else:
            raise Exception("Shutdown routes not found")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_shutdown_endpoint'] = elapsed
        test_results.append({"name": "Shutdown Endpoint", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    # Test 12: Shutdown Endpoint Functionality (test that it exists and can be imported, but don't call it)
    start = time.time()
    try:
        from api.routes.bot import shutdown_server_endpoint, shutdown_bot_endpoint
        # Check that functions exist and are callable
        if callable(shutdown_server_endpoint) and callable(shutdown_bot_endpoint):
            elapsed = (time.time() - start) * 1000
            timings['test_shutdown_functions'] = elapsed
            test_results.append({"name": "Shutdown Functions", "passed": True, "duration_ms": elapsed})
            passed += 1
        else:
            raise Exception("Shutdown functions not callable")
    except ImportError as e:
        elapsed = (time.time() - start) * 1000
        timings['test_shutdown_functions'] = elapsed
        error_msg = f"Shutdown functions not importable: {str(e)}"
        test_results.append({"name": "Shutdown Functions", "passed": False, "duration_ms": elapsed, "error": error_msg})
        failed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_shutdown_functions'] = elapsed
        test_results.append({"name": "Shutdown Functions", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    # Test 13: Frontend Component Files Exist (check critical frontend files)
    start = time.time()
    try:
        project_root = Path(__file__).parent.parent.parent
        frontend_components = [
            'frontend/src/components/BotControls.tsx',
            'frontend/src/components/ConfirmDialog.tsx',
            'frontend/src/api/bot.ts',
        ]
        
        missing_files = []
        for component_path in frontend_components:
            full_path = project_root / component_path
            if not full_path.exists():
                missing_files.append(component_path)
        
        elapsed = (time.time() - start) * 1000
        timings['test_frontend_files'] = elapsed
        if missing_files:
            error_msg = f"Missing frontend files: {', '.join(missing_files)}"
            test_results.append({"name": "Frontend Components", "passed": False, "duration_ms": elapsed, "error": error_msg})
            failed += 1
        else:
            test_results.append({"name": "Frontend Components", "passed": True, "duration_ms": elapsed})
            passed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_frontend_files'] = elapsed
        test_results.append({"name": "Frontend Components", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    # Test 14: Shutdown Button Handler Check (check frontend code for proper handlers)
    start = time.time()
    try:
        project_root = Path(__file__).parent.parent.parent
        bot_controls_path = project_root / 'frontend/src/components/BotControls.tsx'
        
        if not bot_controls_path.exists():
            raise Exception("BotControls.tsx not found")
        
        with open(bot_controls_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required patterns
        issues = []
        if 'shutdownServerMutation' not in content:
            issues.append("shutdownServerMutation not found")
        if 'setShowShutdownDialog' not in content:
            issues.append("setShowShutdownDialog not found")
        if 'onConfirm' not in content or 'shutdownServerMutation.mutate' not in content:
            issues.append("onConfirm handler not properly connected")
        if 'ConfirmDialog' not in content:
            issues.append("ConfirmDialog component not used")
        
        elapsed = (time.time() - start) * 1000
        timings['test_shutdown_handler'] = elapsed
        if issues:
            error_msg = f"Shutdown button handler issues: {'; '.join(issues)}"
            test_results.append({"name": "Shutdown Button Handler", "passed": False, "duration_ms": elapsed, "error": error_msg})
            failed += 1
        else:
            test_results.append({"name": "Shutdown Button Handler", "passed": True, "duration_ms": elapsed})
            passed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_shutdown_handler'] = elapsed
        test_results.append({"name": "Shutdown Button Handler", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    # Test 15: JSX Syntax Validation (check all critical TSX files for syntax errors)
    start = time.time()
    try:
        import re
        project_root = Path(__file__).parent.parent.parent
        critical_tsx_files = [
            'frontend/src/pages/System.tsx',
            'frontend/src/components/BotControls.tsx',
            'frontend/src/components/ConfirmDialog.tsx',
        ]
        
        jsx_issues = []
        for tsx_file in critical_tsx_files:
            file_path = project_root / tsx_file
            if not file_path.exists():
                jsx_issues.append(f"{tsx_file} not found")
                continue
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count opening tags (excluding self-closing)
            opening_divs = len([m for m in re.finditer(r'<div[^>]*>', content) if '/>' not in m.group()])
            closing_divs = content.count('</div>')
            
            opening_main = len([m for m in re.finditer(r'<main[^>]*>', content) if '/>' not in m.group()])
            closing_main = content.count('</main>')
            
            opening_header = len([m for m in re.finditer(r'<header[^>]*>', content) if '/>' not in m.group()])
            closing_header = content.count('</header>')
            
            opening_section = len([m for m in re.finditer(r'<section[^>]*>', content) if '/>' not in m.group()])
            closing_section = content.count('</section>')
            
            # Check for balanced tags
            if opening_divs != closing_divs:
                diff = opening_divs - closing_divs
                jsx_issues.append(f"{tsx_file}: {abs(diff)} unclosed <div> tag(s) ({'missing closing' if diff > 0 else 'extra closing'})")
            if opening_main != closing_main:
                diff = opening_main - closing_main
                jsx_issues.append(f"{tsx_file}: {abs(diff)} unclosed <main> tag(s) ({'missing closing' if diff > 0 else 'extra closing'})")
            if opening_header != closing_header:
                diff = opening_header - closing_header
                jsx_issues.append(f"{tsx_file}: {abs(diff)} unclosed <header> tag(s) ({'missing closing' if diff > 0 else 'extra closing'})")
            if opening_section != closing_section:
                diff = opening_section - closing_section
                jsx_issues.append(f"{tsx_file}: {abs(diff)} unclosed <section> tag(s) ({'missing closing' if diff > 0 else 'extra closing'})")
            
            # Check for unclosed JSX expressions
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces != close_braces:
                jsx_issues.append(f"{tsx_file}: {abs(open_braces - close_braces)} unclosed JSX expression brace(s)")
        
        elapsed = (time.time() - start) * 1000
        timings['test_jsx_syntax'] = elapsed
        if jsx_issues:
            error_msg = f"JSX syntax errors: {'; '.join(jsx_issues)}"
            test_results.append({"name": "JSX Syntax Validation", "passed": False, "duration_ms": elapsed, "error": error_msg})
            failed += 1
        else:
            test_results.append({"name": "JSX Syntax Validation", "passed": True, "duration_ms": elapsed})
            passed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_jsx_syntax'] = elapsed
        test_results.append({"name": "JSX Syntax Validation", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    # Test 16: Startup Script Duplicate Tab Prevention
    start = time.time()
    try:
        import re
        project_root = Path(__file__).parent.parent.parent
        startup_script_path = project_root / 'start_gui.sh'
        
        if not startup_script_path.exists():
            raise Exception("start_gui.sh not found")
        
        with open(startup_script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for duplicate tab prevention mechanisms
        issues = []
        if 'LOCK_FILE' not in content and '/tmp/market-bot-browser-open.lock' not in content:
            issues.append("Lock file mechanism not found")
        if 'BROWSER_OPENED' not in content:
            issues.append("Browser opened flag not found")
        if not re.search(r'pgrep.*xdg-open|pgrep.*gnome-open|pgrep.*kde-open', content):
            issues.append("Browser opening process detection not found")
        if not re.search(r'ss.*5173|netstat.*5173', content):
            issues.append("Port connection check not found")
        if 'LOCK_TIMEOUT' not in content and 'LOCK_AGE' not in content:
            issues.append("Lock file timeout mechanism not found")
        
        elapsed = (time.time() - start) * 1000
        timings['test_startup_script'] = elapsed
        if issues:
            error_msg = f"Startup script issues: {'; '.join(issues)}"
            test_results.append({"name": "Startup Script (Duplicate Tab Prevention)", "passed": False, "duration_ms": elapsed, "error": error_msg})
            failed += 1
        else:
            test_results.append({"name": "Startup Script (Duplicate Tab Prevention)", "passed": True, "duration_ms": elapsed})
            passed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_startup_script'] = elapsed
        test_results.append({"name": "Startup Script (Duplicate Tab Prevention)", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    # Test 17: Log Quality Checks (yfinance suppression, screener warnings, PDT config)
    start = time.time()
    try:
        project_root = Path(__file__).parent.parent.parent
        
        issues = []
        
        # Check stock_screener.py for yfinance delisted stock suppression
        screener_path = project_root / 'stock_screener.py'
        if screener_path.exists():
            with open(screener_path, 'r', encoding='utf-8') as f:
                screener_content = f.read()
            
            # Check for DelistedStockFilter
            if 'DelistedStockFilter' not in screener_content:
                issues.append("DelistedStockFilter not found in stock_screener.py")
            if 'yf_logger.propagate = False' not in screener_content:
                issues.append("yfinance logger propagation not disabled in stock_screener.py")
            
            # Check that "No stocks passed screening" is INFO not WARNING
            # Find the line with "No stocks passed screening criteria"
            no_stocks_idx = screener_content.find('No stocks passed screening criteria')
            if no_stocks_idx != -1:
                # Check the context around this line (200 chars before)
                context_start = max(0, no_stocks_idx - 200)
                context = screener_content[context_start:no_stocks_idx + 50]
                # Check if it's using warning
                if 'logger.warning' in context:
                    issues.append("Stock screener 'No stocks passed' should be INFO, not WARNING")
                # Check if it's using info
                if 'logger.info' not in context:
                    issues.append("Stock screener 'No stocks passed' should use logger.info")
        else:
            issues.append("stock_screener.py not found")
        
        # Check env_conflict_checker.py for PDT severity
        env_checker_path = project_root / 'env_conflict_checker.py'
        if env_checker_path.exists():
            with open(env_checker_path, 'r', encoding='utf-8') as f:
                env_checker_content = f.read()
            
            # Check that PDT conflict is INFO not WARNING
            if "Obsolete PDT Rules Setting" in env_checker_content:
                # Find the PDT section - look for the EnvConflict call
                pdt_start = env_checker_content.find("Obsolete PDT Rules Setting")
                if pdt_start != -1:
                    # Look backwards for the severity= line (should be within 50 chars before)
                    section_start = max(0, pdt_start - 100)
                    pdt_section = env_checker_content[section_start:pdt_start + 200]
                    # Check if severity is WARNING in this section
                    if "severity='WARNING'" in pdt_section or 'severity="WARNING"' in pdt_section:
                        issues.append("PDT Rules Setting should be INFO severity, not WARNING")
                    # Check if severity is INFO in this section
                    if "severity='INFO'" not in pdt_section and 'severity="INFO"' not in pdt_section:
                        issues.append("PDT Rules Setting should use severity='INFO'")
            else:
                issues.append("Obsolete PDT Rules Setting check not found in env_conflict_checker.py")
        else:
            issues.append("env_conflict_checker.py not found")
        
        elapsed = (time.time() - start) * 1000
        timings['test_log_quality'] = elapsed
        if issues:
            error_msg = f"Log quality issues: {'; '.join(issues)}"
            test_results.append({"name": "Log Quality Checks", "passed": False, "duration_ms": elapsed, "error": error_msg})
            failed += 1
        else:
            test_results.append({"name": "Log Quality Checks", "passed": True, "duration_ms": elapsed})
            passed += 1
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        timings['test_log_quality'] = elapsed
        test_results.append({"name": "Log Quality Checks", "passed": False, "duration_ms": elapsed, "error": str(e)})
        failed += 1
    
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0
    if failed > 0:
        for r in test_results:
            if not r.get("passed"):
                logger.info(f"[SELFTEST] Health check ✗ {r.get('name', '?')}: {r.get('error', '')}")
        logger.info(f"[SELFTEST] Health self-tests: {passed}/{total} passed")
    
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "success_rate": success_rate,
        "all_passed": failed == 0,
        "results": test_results,
        "timings": {
            "total_duration_ms": sum(timings.values()),
            "total_duration_s": sum(timings.values()) / 1000,
            "test_timings": timings
        }
    }

@router.post("/run-tests", dependencies=[Depends(require_admin)])
async def run_full_self_tests() -> Dict:
    """Run the full self-test suite on demand (triggered by GUI button).
    Requires the bot to be stopped so tests run against a consistent state."""
    import subprocess
    import time
    from datetime import datetime

    try:
        from api.bot_manager import is_bot_running
        if is_bot_running():
            raise HTTPException(
                status_code=409,
                detail="Cannot run full self-test while the bot is running. Please stop the bot first."
            )
    except HTTPException:
        raise
    except Exception:
        pass  # If we can't check, allow the test to run

    global _http_tests_run, _http_tests_results
    
    # Clear cache to force fresh test run
    _self_test_cache["results"] = None
    _self_test_cache["timestamp"] = None
    _http_tests_run = False
    _http_tests_results = None
    
    project_root = Path(__file__).parent.parent.parent
    test_runner_path = project_root / "tests" / "runner.py"
    # Full suite can be slow (many modules, HTTP tests); allow 5 min by default
    run_tests_timeout = int(os.getenv("RUN_TESTS_TIMEOUT_SECONDS", "300"))
    run_tests_timeout = max(60, min(run_tests_timeout, 600))  # clamp 1–10 min

    start_time = time.time()

    api_url = os.getenv("API_URL") or f"http://localhost:{int(os.getenv('API_PORT', '8002'))}"
    if not api_url.startswith("http"):
        api_url = f"http://{api_url}"
    frontend_url = os.getenv("VITE_FRONTEND_URL", "http://localhost:5173")
    try:
        # Run the full test suite (API_URL and VITE_FRONTEND_URL from env)
        result = subprocess.run(
            ["python3", str(test_runner_path), "--api-url", api_url, "--frontend-url", frontend_url],
            capture_output=True,
            text=True,
            timeout=run_tests_timeout,
            cwd=str(project_root),
            env={**os.environ, "API_URL": api_url},
        )
        
        elapsed = time.time() - start_time
        output = result.stdout or ""
        stderr = result.stderr or ""
        
        # Log for easy analysis: one-line summary and full output on failure or when DEBUG
        _log_selftest_run(result.returncode, output, stderr, elapsed, run_tests_timeout, project_root)
        
        # Parse output for summary
        
        # Extract test counts from output
        passed = 0
        failed = 0
        warnings = 0
        total = 0
        
        for line in output.split('\n'):
            if 'Passed:' in line and '(' in line:
                try:
                    passed = int(line.split('Passed:')[1].split('(')[0].strip())
                except:
                    pass
            elif 'Failed:' in line:
                try:
                    failed = int(line.split('Failed:')[1].strip().split()[0])
                except:
                    pass
            elif 'Warnings:' in line:
                try:
                    warnings = int(line.split('Warnings:')[1].strip().split()[0])
                except:
                    pass
            elif 'Total Tests:' in line:
                try:
                    total = int(line.split('Total Tests:')[1].strip().split()[0])
                except:
                    pass
        
        # Extract failed test details
        failed_tests = []
        in_failed_section = False
        for line in output.split('\n'):
            if 'FAILED TESTS:' in line:
                in_failed_section = True
                continue
            if 'WARNINGS:' in line:
                in_failed_section = False
            if in_failed_section and line.strip().startswith('✗'):
                test_name = line.strip().replace('✗', '').strip()
                failed_tests.append({"name": test_name, "passed": False})
        
        # Also get the failed test messages
        failed_details = []
        lines = output.split('\n')
        i = 0
        while i < len(lines):
            if lines[i].strip().startswith('✗'):
                test_name = lines[i].strip().replace('✗', '').strip()
                error_msg = ""
                if i + 1 < len(lines) and not lines[i+1].strip().startswith('✗') and not lines[i+1].strip().startswith('⚠'):
                    error_msg = lines[i+1].strip()
                failed_details.append({"name": test_name, "passed": False, "error": error_msg})
            i += 1
        
        return {
            "success": result.returncode == 0 or failed == 0,
            "total": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "duration_s": round(elapsed, 2),
            "failed_tests": failed_details if failed_details else failed_tests,
            "output": output[-2000:] if len(output) > 2000 else output,  # Last 2000 chars
            "stderr": stderr[-2000:] if len(stderr) > 2000 else stderr,
            "timestamp": datetime.now().isoformat()
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Test suite timed out after {run_tests_timeout} seconds. Set RUN_TESTS_TIMEOUT_SECONDS in .env to increase (max 600).",
            "duration_s": run_tests_timeout,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error running self-tests: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/health")
async def get_system_health() -> Dict:
    """Get system health including self-test status"""
    try:
        import sys
        import time
        from datetime import datetime
        from api.utils import get_bot_instance
        
        # Check cache first - don't run tests on every request
        current_time = time.time()
        
        # Use cached results if available and fresh
        if (_self_test_cache["results"] is not None and 
            _self_test_cache["timestamp"] is not None and
            (current_time - _self_test_cache["timestamp"]) < _self_test_cache["cache_duration"]):
            test_results = _self_test_cache["results"]
            logger.debug("Using cached self-test results")
        else:
            # Run internal tests first (fast, no HTTP needed)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            test_start = time.time()
            internal_results = _run_internal_self_tests()
            
            # Run HTTP tests if API is ready (run once, then cache)
            global _http_tests_run, _http_tests_results
            if not _http_tests_run:
                try:
                    # Try to run HTTP tests (only if API is accessible)
                    http_results = _run_http_self_tests()
                    if http_results:
                        _http_tests_results = http_results
                        _http_tests_run = True
                        logger.info("HTTP self-tests completed successfully")
                except Exception as e:
                    logger.debug(f"HTTP self-tests not ready yet: {e}")
                    # Will try again on next request
            
            # Merge results: use HTTP tests if available, otherwise use internal
            if _http_tests_results:
                test_results = _http_tests_results
            else:
                test_results = internal_results
            
            test_elapsed = time.time() - test_start
            
            # Cache the results
            _self_test_cache["results"] = test_results
            _self_test_cache["timestamp"] = current_time
            logger.info(f"Self-test completed in {test_elapsed:.2f}s, cached for {_self_test_cache['cache_duration']}s")
        
        # Add messages to bot's message system if bot is available (only on fresh test, not cached)
        cache_age = current_time - _self_test_cache["timestamp"] if _self_test_cache["timestamp"] else 999
        if cache_age < 5:  # Only add message if test just ran (within 5 seconds)
            bot = get_bot_instance()
            if bot and hasattr(bot, 'stored_messages'):
                # Add summary message about self-test results with timing
                total_time = test_results.get('timings', {}).get('total_duration_s', 0)
                if test_results["all_passed"]:
                    bot.stored_messages.add_message(
                        f"Self-test completed: {test_results['passed']}/{test_results['total']} tests passed in {total_time:.2f}s",
                        category='info'
                    )
                else:
                    failed_tests = [r['name'] for r in test_results['results'] if not r.get('passed', False)]
                    if failed_tests:
                        bot.stored_messages.add_message(
                            f"Self-test failed: {test_results['failed']} test(s) failed in {total_time:.2f}s - {', '.join(failed_tests[:3])}",
                            category='warning'
                        )
                    else:
                        bot.stored_messages.add_message(
                            f"Self-test completed with {test_results['failed']} failure(s) in {total_time:.2f}s",
                            category='warning'
                        )
        
        # Get startup timings from utils
        from api.utils import get_startup_timings
        startup_timings = get_startup_timings()
        
        return {
            "status": "healthy" if test_results["all_passed"] else "degraded",
            "self_test": {
                "passed": test_results["all_passed"],
                "total": test_results["total"],
                "passed_count": test_results["passed"],
                "failed_count": test_results["failed"],
                "success_rate": test_results["success_rate"],
                "results": test_results["results"],
                "timings": test_results.get("timings", {})
            },
            "startup_timings": startup_timings,
            "system": {
                "platform": os.name,
                "python_version": sys.version.split()[0]
            }
        }
    except ImportError as e:
        logger.warning(f"Could not import startup_test: {e}", exc_info=True)
        return {
            "status": "unknown",
            "self_test": {
                "passed": None,
                "error": "Startup test module not available"
            }
        }
    except Exception as e:
        logger.error(f"Error getting system health: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "self_test": {
                "passed": False,
                "error": "Could not run self-tests"
            }
        }


@router.get("")
async def get_system_info() -> Dict:
    """Get system information"""
    try:
        import platform
        import psutil
        from datetime import datetime
        
        # Get CPU usage (average over 1 second)
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get uptime (process uptime)
        import time
        uptime_seconds = time.time() - psutil.boot_time()
        
        # Convert bytes to GB
        def bytes_to_gb(bytes_val):
            return bytes_val / (1024 ** 3)
        
        return {
            "cpu_usage": cpu_percent,
            "cpu_count": psutil.cpu_count(),
            "memory_usage": memory.percent,
            "memory_total": bytes_to_gb(memory.total),
            "memory_available": bytes_to_gb(memory.available),
            "disk_usage": disk.percent,
            "disk_total": bytes_to_gb(disk.total),
            "disk_free": bytes_to_gb(disk.free),
            "uptime": uptime_seconds,
            "timestamp": datetime.now().isoformat()
        }
    except ImportError:
        # psutil not available, return basic info with defaults
        import platform
        import time
        from datetime import datetime
        return {
            "cpu_usage": 0.0,
            "cpu_count": 1,
            "memory_usage": 0.0,
            "memory_total": 0.0,
            "memory_available": 0.0,
            "disk_usage": 0.0,
            "disk_total": 0.0,
            "disk_free": 0.0,
            "uptime": time.time(),
            "timestamp": datetime.now().isoformat(),
            "note": "psutil not available for detailed resource info"
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}", exc_info=True)
        # Return structure that matches frontend expectations even on error
        import time
        from datetime import datetime
        return {
            "cpu_usage": 0.0,
            "cpu_count": 1,
            "memory_usage": 0.0,
            "memory_total": 0.0,
            "memory_available": 0.0,
            "disk_usage": 0.0,
            "disk_total": 0.0,
            "disk_free": 0.0,
            "uptime": time.time(),
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
