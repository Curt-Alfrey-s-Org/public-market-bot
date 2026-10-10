"""
FastAPI Application - Main Entry Point
Provides REST API endpoints for React frontend to interact with trading bot
"""

from dotenv import load_dotenv
load_dotenv()

# ========== NEW: Import and validate environment configuration ==========
try:
    from api.config import settings
    # Fail fast (with the variable name) if JWT_SECRET is missing in production.
    from api.security_config import get_jwt_secret
    get_jwt_secret()
except Exception as e:
    import sys
    print(f"❌ CONFIGURATION ERROR: {e}", file=sys.stderr)
    sys.exit(1)
# ===========================================================================

from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import sys
import logging

# ========== NEW: Setup secret redaction for logging ==========
try:
    from api.logging_utils import setup_secret_logging
    setup_secret_logging()
except Exception as e:
    logging.warning(f"Could not setup secret logging: {e}")
# ==========================================================

# Import logging middleware (conditional on DEBUG mode)
DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'
if DEBUG_MODE:
    try:
        from api.middleware.logging import LoggingMiddleware
    except ImportError:
        LoggingMiddleware = None
else:
    LoggingMiddleware = None

# Add parent directory to path to import bot modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes import bot, stats, settings as routes_settings, trades, system, messages, ai, tax, logs, pending_trades, assets, reports, auth, network, users, health, metrics, admin_ai_monitor, ai_narrative, ai_jobs
from api.routes import v1  # Import v1 routes for mobile API
from api.models import responses
from database import engine, SessionLocal, Base
from api.models.user import User
from api.models.auth_token import EmailVerificationToken
from api.models.audit import AuditLog
from sqlalchemy.orm import Session
from api.startup import initialize_bot_data, get_startup_status

# Configure logging based on environment
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'

# In debug mode, use DEBUG level
if DEBUG_MODE:
    LOG_LEVEL = 'DEBUG'

# Set up logging with detailed format
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Ensure bot and API logs go to trading_bot.log so the Logs page shows current entries
try:
    from pathlib import Path
    _project_root = Path(__file__).resolve().parent.parent
    _log_file = _project_root / 'trading_bot.log'
    _file_handler = logging.FileHandler(_log_file, encoding='utf-8')
    _file_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    _file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logging.getLogger().addHandler(_file_handler)
except Exception as _e:
    import sys
    print(f"Could not add trading_bot.log handler: {_e}", file=sys.stderr)

logger = logging.getLogger(__name__)
logger.info(f"Logging configured - Level: {LOG_LEVEL}, Debug Mode: {DEBUG_MODE}")

API_KEY_HEADER = "X-API-Key"
BOT_API_KEY = settings.bot_api_key  # Use validated settings


# Database setup
def get_db():
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan: run startup self-tests, then yield; shutdown runs after yield."""
    import time
    import threading
    from datetime import datetime

    startup_start = time.time()
    try:
        from api.services.health_check import set_startup_time
        set_startup_time(startup_start)
    except ImportError:
        pass
    logger.info(f"[STARTUP] API startup began at {datetime.now().isoformat()}")

    # ALFa AI brain (LiteLLM) config check: name any missing variable up front so
    # a bot that cannot start (BOT_REQUIRE_BRAIN=true) is explained in the logs.
    try:
        from api.bot_manager import brain_config_error
        _brain_err = brain_config_error()
        if _brain_err:
            logger.error("[STARTUP] %s", _brain_err)
    except Exception as e:  # never block API startup on this check
        logger.warning("[STARTUP] Could not check ALFa AI brain configuration: %s", e)

    try:
        logger.info("[STARTUP] Running startup self-tests...")
        
        # Create database tables (ignore "index already exists" on existing DBs)
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("[STARTUP] Database tables created/verified")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("[STARTUP] Database tables/indexes already exist (ok)")
            else:
                raise

        # ALFa AI support tables (telemetry + captured errors). Not ORM models,
        # so created idempotently here alongside create_all. Best-effort.
        try:
            from api.services.ai_tables import ensure_ai_tables
            ensure_ai_tables(engine)
        except Exception as e:
            logger.warning("[STARTUP] Could not ensure ALFa AI tables: %s", e)
        
        test_start = time.time()
        test_results = []
        passed = 0
        failed = 0

        # Test 1: Python Syntax Check (Critical Modules)
        syntax_start = time.time()
        try:
            import subprocess
            from pathlib import Path
            import sys
            project_root = Path(__file__).parent.parent
            critical_modules = ['api/bot_manager.py', 'api/routes/bot.py', 'api/routes/system.py']
            syntax_errors = []
            for module_path in critical_modules:
                full_path = project_root / module_path
                if full_path.exists():
                    try:
                        result = subprocess.run(
                            [sys.executable, '-m', 'py_compile', str(full_path)],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode != 0:
                            syntax_errors.append(f"{module_path}: {result.stderr[:80]}")
                    except Exception as e:
                        syntax_errors.append(f"{module_path}: {str(e)[:80]}")
            syntax_elapsed = (time.time() - syntax_start) * 1000
            if syntax_errors:
                error_msg = "; ".join(syntax_errors[:2])
                test_results.append({"name": "Python Syntax Check", "passed": False, "duration_ms": syntax_elapsed, "error": error_msg})
                failed += 1
                logger.info(f"[SELFTEST] ✗ Python Syntax Check ({syntax_elapsed:.0f}ms): {error_msg}")
            else:
                test_results.append({"name": "Python Syntax Check", "passed": True, "duration_ms": syntax_elapsed})
                passed += 1
                logger.info(f"[SELFTEST] ✓ Python Syntax Check ({syntax_elapsed:.0f}ms)")
        except Exception as e:
            syntax_elapsed = (time.time() - syntax_start) * 1000
            test_results.append({"name": "Python Syntax Check", "passed": False, "duration_ms": syntax_elapsed, "error": str(e)[:80]})
            failed += 1
            logger.info(f"[SELFTEST] ✗ Python Syntax Check ({syntax_elapsed:.0f}ms): {e}")

        # Test 2: Bot Manager Initialization
        bot_mgr_start = time.time()
        try:
            from api.bot_manager import get_bot_instance, is_bot_running
            is_running = is_bot_running()
            bot_instance = get_bot_instance()
            bot_mgr_elapsed = (time.time() - bot_mgr_start) * 1000
            test_results.append({"name": "Bot Manager Init", "passed": True, "duration_ms": bot_mgr_elapsed})
            passed += 1
            logger.info(f"[SELFTEST] ✓ Bot Manager Init ({bot_mgr_elapsed:.0f}ms)")
        except UnboundLocalError as e:
            bot_mgr_elapsed = (time.time() - bot_mgr_start) * 1000
            error_msg = f"UnboundLocalError: {str(e)[:80]}. Check for duplicate imports inside functions."
            test_results.append({"name": "Bot Manager Init", "passed": False, "duration_ms": bot_mgr_elapsed, "error": error_msg})
            failed += 1
            logger.info(f"[SELFTEST] ✗ Bot Manager Init ({bot_mgr_elapsed:.0f}ms): {error_msg}")
        except NameError as e:
            bot_mgr_elapsed = (time.time() - bot_mgr_start) * 1000
            error_msg = f"NameError: {str(e)[:80]}. Check for undefined variables or missing imports."
            test_results.append({"name": "Bot Manager Init", "passed": False, "duration_ms": bot_mgr_elapsed, "error": error_msg})
            failed += 1
            logger.info(f"[SELFTEST] ✗ Bot Manager Init ({bot_mgr_elapsed:.0f}ms): {error_msg}")
        except Exception as e:
            bot_mgr_elapsed = (time.time() - bot_mgr_start) * 1000
            test_results.append({"name": "Bot Manager Init", "passed": False, "duration_ms": bot_mgr_elapsed, "error": str(e)[:80]})
            failed += 1
            logger.info(f"[SELFTEST] ✗ Bot Manager Init ({bot_mgr_elapsed:.0f}ms): {e}")

        # Test 3: Module Imports
        import_start = time.time()
        try:
            import api.main as _api_main
            from api.routes import bot, stats, settings, trades, system, messages, ai, tax, logs, reports
            import_elapsed = (time.time() - import_start) * 1000
            test_results.append({"name": "Module Imports", "passed": True, "duration_ms": import_elapsed})
            passed += 1
            logger.info(f"[SELFTEST] ✓ Module Imports ({import_elapsed:.0f}ms)")
        except Exception as e:
            import_elapsed = (time.time() - import_start) * 1000
            test_results.append({"name": "Module Imports", "passed": False, "duration_ms": import_elapsed, "error": str(e)})
            failed += 1
            logger.info(f"[SELFTEST] ✗ Module Imports ({import_elapsed:.0f}ms): {e}")

        # Test 4: API App Structure
        app_start = time.time()
        try:
            if hasattr(app, 'routes') and len(app.routes) > 0:
                app_elapsed = (time.time() - app_start) * 1000
                test_results.append({"name": "API App Structure", "passed": True, "duration_ms": app_elapsed})
                passed += 1
                logger.info(f"[SELFTEST] ✓ API App Structure ({app_elapsed:.0f}ms)")
            else:
                raise Exception("No routes registered")
        except Exception as e:
            app_elapsed = (time.time() - app_start) * 1000
            test_results.append({"name": "API App Structure", "passed": False, "duration_ms": app_elapsed, "error": str(e)})
            failed += 1
            logger.info(f"[SELFTEST] ✗ API App Structure ({app_elapsed:.0f}ms): {e}")

        # Test 5: Route Registration
        routes_start = time.time()
        try:
            route_paths = [route.path for route in app.routes]
            expected_routes = ['/api/health', '/api/bot/status', '/api/stats', '/api/trades', '/api/messages']
            found_routes = [path for path in expected_routes if any(path in rp for rp in route_paths)]
            if len(found_routes) >= 3:
                routes_elapsed = (time.time() - routes_start) * 1000
                test_results.append({"name": "Route Registration", "passed": True, "duration_ms": routes_elapsed})
                passed += 1
                logger.debug(f"[STARTUP]   ✓ Route Registration ({routes_elapsed:.2f}ms)")
            else:
                raise Exception(f"Only {len(found_routes)}/{len(expected_routes)} routes found")
        except Exception as e:
            routes_elapsed = (time.time() - routes_start) * 1000
            test_results.append({"name": "Route Registration", "passed": False, "duration_ms": routes_elapsed, "error": str(e)})
            failed += 1
            logger.warning(f"[STARTUP]   ✗ Route Registration ({routes_elapsed:.2f}ms): {e}")

        # Test 6: CORS Configuration
        cors_start = time.time()
        try:
            has_cors = any('CORSMiddleware' in str(middleware) for middleware in app.user_middleware)
            cors_elapsed = (time.time() - cors_start) * 1000
            if has_cors:
                test_results.append({"name": "CORS Configuration", "passed": True, "duration_ms": cors_elapsed})
                passed += 1
                logger.info(f"[SELFTEST] ✓ CORS Configuration ({cors_elapsed:.0f}ms)")
            else:
                raise Exception("CORS middleware not found")
        except Exception as e:
            cors_elapsed = (time.time() - cors_start) * 1000
            test_results.append({"name": "CORS Configuration", "passed": False, "duration_ms": cors_elapsed, "error": str(e)})
            failed += 1
            logger.info(f"[SELFTEST] ✗ CORS Configuration ({cors_elapsed:.0f}ms): {e}")

        # Test 7: Shutdown Endpoint Exists
        shutdown_route_start = time.time()
        try:
            route_paths = [route.path for route in app.routes]
            if any('/api/bot/shutdown' in path or '/api/bot/shutdown-server' in path for path in route_paths):
                shutdown_route_elapsed = (time.time() - shutdown_route_start) * 1000
                test_results.append({"name": "Shutdown Endpoint", "passed": True, "duration_ms": shutdown_route_elapsed})
                passed += 1
                logger.info(f"[SELFTEST] ✓ Shutdown Endpoint ({shutdown_route_elapsed:.0f}ms)")
            else:
                raise Exception("Shutdown routes not found")
        except Exception as e:
            shutdown_route_elapsed = (time.time() - shutdown_route_start) * 1000
            test_results.append({"name": "Shutdown Endpoint", "passed": False, "duration_ms": shutdown_route_elapsed, "error": str(e)})
            failed += 1
            logger.info(f"[SELFTEST] ✗ Shutdown Endpoint ({shutdown_route_elapsed:.0f}ms): {e}")

        # Test 8: System Endpoint
        system_route_start = time.time()
        try:
            route_paths = [route.path for route in app.routes]
            if any('/api/system' in path and path != '/api/system/health' for path in route_paths):
                system_route_elapsed = (time.time() - system_route_start) * 1000
                test_results.append({"name": "System Endpoint", "passed": True, "duration_ms": system_route_elapsed})
                passed += 1
                logger.info(f"[SELFTEST] ✓ System Endpoint ({system_route_elapsed:.0f}ms)")
            else:
                raise Exception("System route not found")
        except Exception as e:
            system_route_elapsed = (time.time() - system_route_start) * 1000
            test_results.append({"name": "System Endpoint", "passed": False, "duration_ms": system_route_elapsed, "error": str(e)})
            failed += 1
            logger.info(f"[SELFTEST] ✗ System Endpoint ({system_route_elapsed:.0f}ms): {e}")

        # Test 9: YFinance Probe (only in pure simulation or API-disabled mode)
        yfin_probe_start = time.time()
        try:
            paper_mode = os.getenv('PAPER_TRADING_MODE', 'true').lower() == 'true'
            sandbox_mode = os.getenv('SCHWAB_SANDBOX_MODE', 'false').lower() == 'true'
            api_enabled = os.getenv('SCHWAB_API_ENABLED', 'on').lower() in ('on', 'true', '1', 'yes')

            pure_simulation = (not api_enabled) or (paper_mode and not sandbox_mode)
            if pure_simulation:
                try:
                    import yfinance as yf
                except Exception as e:
                    raise Exception(f"yfinance not available: {e}")

                try:
                    ticker = yf.Ticker('AAPL')
                    price = None
                    try:
                        price = ticker.fast_info.get('lastPrice')
                    except Exception:
                        info = getattr(ticker, 'info', {})
                        price = info.get('currentPrice') or info.get('regularMarketPrice')
                    if price is None or (isinstance(price, (int, float)) and price <= 0):
                        raise Exception("Invalid AAPL price from yfinance")
                    yfin_probe_elapsed = (time.time() - yfin_probe_start) * 1000
                    test_results.append({"name": "YFinance Probe", "passed": True, "duration_ms": yfin_probe_elapsed})
                    passed += 1
                    logger.info(f"[SELFTEST] ✓ YFinance Probe ({yfin_probe_elapsed:.0f}ms)")
                except Exception as e:
                    yfin_probe_elapsed = (time.time() - yfin_probe_start) * 1000
                    test_results.append({"name": "YFinance Probe", "passed": False, "duration_ms": yfin_probe_elapsed, "error": str(e)})
                    failed += 1
                    logger.info(f"[SELFTEST] ✗ YFinance Probe ({yfin_probe_elapsed:.0f}ms): {e}")
            else:
                # Skip probe when sandbox/live mode is active
                yfin_probe_elapsed = (time.time() - yfin_probe_start) * 1000
                test_results.append({"name": "YFinance Probe (Skipped)", "passed": True, "duration_ms": yfin_probe_elapsed})
                logger.debug(f"[SELFTEST] ▷ YFinance Probe skipped ({yfin_probe_elapsed:.0f}ms) - not in pure simulation/API-disabled mode")
        except Exception as e:
            yfin_probe_elapsed = (time.time() - yfin_probe_start) * 1000
            test_results.append({"name": "YFinance Probe", "passed": False, "duration_ms": yfin_probe_elapsed, "error": str(e)})
            failed += 1
            logger.info(f"[SELFTEST] ✗ YFinance Probe ({yfin_probe_elapsed:.0f}ms): {e}")

        test_elapsed = time.time() - test_start
        total = passed + failed
        all_passed = failed == 0
        if all_passed:
            logger.info(f"[SELFTEST] ✓ Startup self-tests passed: {passed}/{total} in {test_elapsed:.3f}s")
        else:
            logger.info(f"[SELFTEST] ⚠ Startup self-tests: {passed}/{total} passed, {failed} failed in {test_elapsed:.3f}s")
            for test_result in test_results:
                if not test_result["passed"]:
                    duration = test_result.get('duration_ms', 0)
                    error = test_result.get('error', 'Unknown error')
                    logger.info(f"[SELFTEST] ✗ {test_result['name']} ({duration:.0f}ms): {error}")

        from api.utils import get_bot_instance
        bot = get_bot_instance()
        if bot and hasattr(bot, 'stored_messages'):
            bot.stored_messages.add_message(
                f"Startup self-test completed: {passed}/{total} tests passed in {test_elapsed:.2f}s",
                category='info' if all_passed else 'warning'
            )
    except Exception as e:
        logger.error(f"[STARTUP] Error running startup tests: {e}", exc_info=True)

    startup_elapsed = time.time() - startup_start
    logger.info(f"[STARTUP] API startup completed in {startup_elapsed:.3f}s at {datetime.now().isoformat()}")

    def run_http_tests_delayed():
        """Run HTTP tests after a delay to ensure API is ready"""
        time.sleep(5)  # Wait 5 seconds for API to be fully ready
        try:
            from api.routes.system import _run_http_self_tests
            import api.routes.system as system_module
            http_results = _run_http_self_tests()
            if http_results:
                system_module._http_tests_results = http_results
                system_module._http_tests_run = True
                logger.info(f"[STARTUP] HTTP self-tests completed: {http_results['passed']}/{http_results['total']} passed")
        except Exception as e:
            logger.debug(f"[STARTUP] HTTP self-tests not ready yet: {e}")

    threading.Thread(target=run_http_tests_delayed, daemon=True).start()

    # Initialize bot data (Phase 1.1: Startup Recovery)
    try:
        logger.info("[STARTUP] Starting bot data initialization...")
        init_result = await initialize_bot_data()
        logger.info(
            f"[STARTUP] Bot data initialization complete. "
            f"Initialized: {init_result['initialized']}, "
            f"Symbols: {init_result['symbol_count']}, "
            f"Timestamp: {init_result['timestamp']}"
        )
    except Exception as e:
        logger.error(
            f"[STARTUP] Bot data initialization error: {str(e)[:200]}. "
            f"Bot will continue but may be degraded."
        )

    # ========== Start ALFa AI error-monitor background triage ==========
    _error_triage_task = None
    _error_triage_stop = None
    try:
        import asyncio as _asyncio
        from api.services.error_monitor import (
            is_error_monitor_enabled,
            background_triage_loop,
        )
        if is_error_monitor_enabled():
            _error_triage_stop = threading.Event()
            _error_triage_task = _asyncio.create_task(
                background_triage_loop(_error_triage_stop)
            )
            logger.info("[STARTUP] ALFa AI error-monitor triage task started")
    except Exception as e:
        logger.warning("[STARTUP] Could not start error-monitor triage task: %s", e)

    yield  # Application runs here

    # ========== Graceful Shutdown Handler ==========
    logger.info("=== SERVER SHUTTING DOWN ===")

    # Stop the error-monitor background task
    try:
        if _error_triage_stop is not None:
            _error_triage_stop.set()
        if _error_triage_task is not None:
            _error_triage_task.cancel()
            try:
                await _error_triage_task
            except Exception:
                pass
    except Exception as e:
        logger.warning("[SHUTDOWN] Error stopping triage task: %s", e)
    
    try:
        # Save bot state to persistent storage if it exists
        try:
            from api.bot_manager import get_bot_instance
            bot_instance = get_bot_instance()
            if bot_instance and hasattr(bot_instance, 'save_state'):
                logger.info("[SHUTDOWN] Saving bot state...")
                bot_instance.save_state()
        except Exception as e:
            logger.warning(f"[SHUTDOWN] Could not save bot state: {e}")
        
        # All database connections are closed automatically when SessionLocal sessions close
        logger.info("[SHUTDOWN] Database connections closed")
        
    except Exception as e:
        logger.error(f"[SHUTDOWN] Error during graceful shutdown: {e}")
    
    finally:
        logger.info("=== SHUTDOWN COMPLETE ===")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Market Pie5 Bot API",
    description="REST API and WebSocket server for Market Pie5 Trading Bot",
    version="1.0.0",
    lifespan=lifespan,
)

# ========== PHASE 2-B: Register Global Error Handlers ==========
try:
    from api.middleware.error_handler import (
        http_exception_handler,
        validation_exception_handler,
        value_error_handler,
        generic_exception_handler
    )
    from fastapi.exceptions import HTTPException, RequestValidationError
    
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("[PHASE 2-B] Global error handlers registered successfully")
except Exception as e:
    logger.warning(f"[PHASE 2-B] Could not register error handlers: {e}")
# ==============================================================

# ========== PHASE 2-D: Register Rate Limiting with slowapi ==========
try:
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from api.middleware.rate_limit import limiter, rate_limit_exceeded_handler
    
    # Add limiter state to app
    app.state.limiter = limiter
    
    # Register custom rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    
    logger.info("[PHASE 2-D] Rate limiting (slowapi) registered successfully")
except Exception as e:
    logger.warning(f"[PHASE 2-D] Could not register rate limiting: {e}")
# ====================================================================

# Add request/response logging middleware (only in DEBUG mode)
if DEBUG_MODE and LoggingMiddleware:
    app.add_middleware(LoggingMiddleware)
    logger.info("Request/response logging middleware enabled (DEBUG mode)")

# ========== API auth gate (security review 2026-09-25, finding 8) ==========
# Every /api/* request except health and login/registration must present either
#   - a valid Bearer JWT from /api/auth/login or /api/v1/auth/login (browser and
#     mobile sessions), or
#   - X-API-Key == BOT_API_KEY (server-to-server/scripts only; the frontend
#     no longer ships this key).
# This gate only authenticates. Control endpoints (bot start/stop/shutdown,
# /api/bot/mode, pending-trade approve/reject, settings writes, trade reset,
# network access, run-tests) additionally require an admin JWT via
# Depends(require_admin) on the route, so the API key alone cannot drive them.
# Roles come only from the signed token; a client-sent X-User-Role header is
# ignored and cannot grant (or be used to claim) any privilege.
_AUTH_EXEMPT_PREFIXES = ("/api/auth", "/api/v1/auth")


def _is_auth_exempt(path: str) -> bool:
    if path == "/api/health" or path.startswith("/api/health/"):
        return True
    return any(path == p or path.startswith(p + "/") for p in _AUTH_EXEMPT_PREFIXES)


def _api_key_matches(provided: str) -> bool:
    import hmac

    if not BOT_API_KEY or not provided:
        return False
    return hmac.compare_digest(provided.encode("utf-8"), BOT_API_KEY.encode("utf-8"))


class RequireAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        path = request.url.path
        if request.method == "OPTIONS" or not path.startswith("/api/") or _is_auth_exempt(path):
            return await call_next(request)

        from api.auth import authenticate_bearer_token

        bearer_present = False
        auth_header = (request.headers.get("Authorization") or "").strip()
        if auth_header[:7].lower() == "bearer ":
            bearer_present = True
            payload = authenticate_bearer_token(auth_header[7:].strip())
            if payload is not None:
                request.state.auth_role = payload.get("role")
                request.state.auth_method = "jwt"
                return await call_next(request)

        if _api_key_matches((request.headers.get(API_KEY_HEADER) or "").strip()):
            # API key authenticates the caller but never implies a user role;
            # admin-only routes still demand an admin JWT.
            request.state.auth_role = None
            request.state.auth_method = "api_key"
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={
                "detail": (
                    "Invalid or expired session. Please log in again."
                    if bearer_present
                    else "Not authenticated. Sign in to use the API."
                )
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


app.add_middleware(RequireAuthMiddleware)
# ===========================================================================

# CORS middleware - allow React frontend (local, 192 net, subdomains)
_cors_origins = [
    "http://localhost:5173",  # Vite default dev server
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
_cors_extra = os.getenv("CORS_ORIGINS", "").strip()
if _cors_extra:
    _cors_origins.extend(o.strip() for o in _cors_extra.split(",") if o.strip())
# Regex: 192.0.2.21, localhost, and any subdomain/domain (e.g. market-bot.example.com)
_cors_regex = r"^https?://(192\.168\.\d{1,3}\.\d{1,3}|localhost|[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?)(:\d+)?$"
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=_cors_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request correlation IDs (matches error handler JSON + X-Request-ID on responses)
try:
    from api.middleware.request_id import RequestIdMiddleware

    app.add_middleware(RequestIdMiddleware)
    logger.info("Request ID middleware enabled")
except Exception as e:
    logger.warning("Request ID middleware not available: %s", e)

# Prometheus HTTP metrics (optional; requires prometheus-client)
try:
    from api.middleware.prometheus import PrometheusMiddleware

    app.add_middleware(PrometheusMiddleware)
    logger.info("Prometheus metrics middleware enabled")
except ImportError as e:
    logger.warning("Prometheus middleware not available: %s", e)

# Import bot instance utilities to avoid circular imports
from api.utils import set_bot_instance, get_bot_instance

# Include routers
app.include_router(bot.router, prefix="/api/bot", tags=["bot"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(routes_settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(pending_trades.router, prefix="/api/pending-trades", tags=["pending-trades"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(ai_narrative.router, prefix="/api/ai", tags=["ai-narrative"])
app.include_router(tax.router, prefix="/api/tax", tags=["tax"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(assets.router, prefix="/api/assets", tags=["assets"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, tags=["users"])
app.include_router(network.router, prefix="/api", tags=["network"])
app.include_router(health.router, prefix="/api")
app.include_router(admin_ai_monitor.router, prefix="/api/admin/ai-monitor", tags=["ai-monitor"])
app.include_router(ai_jobs.router, prefix="/api/admin/ai-jobs", tags=["ai-jobs"])
app.include_router(metrics.router)  # GET /metrics (no /api prefix; scrape without API key)

# Include V1 API routes (mobile-friendly endpoints)
app.include_router(v1.auth.router, prefix="/api/v1/auth", tags=["auth-v1"])
app.include_router(v1.bot.router, prefix="/api/v1/bot", tags=["bot-v1"])
app.include_router(v1.trades.router, prefix="/api/v1/trades", tags=["trades-v1"])
app.include_router(v1.stats.router, prefix="/api/v1/stats", tags=["stats-v1"])
app.include_router(v1.reports.router, prefix="/api/v1/reports", tags=["reports-v1"])
app.include_router(v1.settings.router, prefix="/api/v1/settings", tags=["settings-v1"])
app.include_router(v1.config.router, prefix="/api/v1/config", tags=["config-v1"])

logger.info("✓ V1 API routes registered under /api/v1/ prefix")

# Optional static frontend served by the API itself (legacy fallback).
# Production serves the UI from the separate market-bot-frontend nginx container
# (frontend/Dockerfile + frontend/nginx.conf), which only proxies /api/ and /ws here.
# The old committed build in api/static/ was removed from git (review 2026-09-25:
# it trusted a client-side role). If api/static/ is absent, the API serves no UI:
# "/" returns a small JSON banner and other non-API paths return 404.
static_dir = Path(__file__).parent / "static"
_index_html = static_dir / "index.html"
_assets_dir = static_dir / "assets"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"Static files mounted at /static from {static_dir}")
    # Built frontend references /assets/ (Vite default) - mount assets for JS/CSS
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="spa_assets")
        logger.info(f"SPA assets mounted at /assets from {_assets_dir}")
else:
    logger.info(
        f"No API-served frontend at {static_dir} (expected: the UI is served by the frontend container)"
    )

_API_BANNER = {"message": "Market Pie5 Bot API", "version": "1.0.0", "docs": "/docs", "health": "/api/health"}


def _serve_index_html():
    """Serve index.html for SPA (root and client-side routes) when a build is present."""
    if _index_html.exists():
        return FileResponse(str(_index_html), media_type="text/html")
    return None


# Root endpoint - serve dashboard if present, else a small API banner
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - serves the dashboard when api/static exists, else an API banner."""
    return _serve_index_html() or JSONResponse(status_code=200, content=_API_BANNER)


# SPA catch-all: serve index.html for client-side routes (/dashboard, /trades, /settings, etc.)
@app.get("/{path:path}", include_in_schema=False)
async def spa_catchall(path: str):
    """Serve index.html for SPA routes - React Router handles client-side routing."""
    # Only serve HTML for paths that are not API, assets, static, ws, docs
    from fastapi import HTTPException
    if path.startswith(("api/", "assets/", "static/", "docs", "openapi", "redoc", "ws")):
        raise HTTPException(status_code=404, detail="Not found")
    response = _serve_index_html()
    if response is None:
        # No API-served frontend (normal in production): nothing to serve.
        raise HTTPException(status_code=404, detail="Not found")
    return response

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    logger.info("WebSocket client connected")
    
    try:
        logger.debug("WebSocket: Starting update loop")
        import asyncio
        tick = 0
        while True:
            # Send periodic updates so the Dashboard can show live numbers and curves
            bot = get_bot_instance()
            if bot:
                # Determine mode
                mode = 'unknown'
                if hasattr(bot, 'mode') and bot.mode:
                    mode = bot.mode
                else:
                    import os
                    paper_mode = os.getenv('PAPER_TRADING_MODE', 'true').lower() == 'true'
                    sandbox_mode = os.getenv('SCHWAB_SANDBOX_MODE', 'false').lower() == 'true'
                    if not paper_mode:
                        mode = 'live'
                    elif sandbox_mode:
                        mode = 'sandbox'
                    else:
                        mode = 'yfinance'
                running = hasattr(bot, 'running') and bot.running
                # Always send status so client can show running/mode
                await websocket.send_json({
                    "type": "status",
                    "data": {"running": running, "mode": mode}
                })
                # When bot is running, send stats pulse every 5 ticks (~5s) so UI refetches without constant updates
                if running and tick % 5 == 0:
                    await websocket.send_json({"type": "stats", "data": {}})
            tick += 1
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)

def _get_bind_host() -> str:
    """Bind address from API_HOST. Default listens on all interfaces.

    Uvicorn host: https://www.uvicorn.org/settings/#host
    """
    return os.getenv("API_HOST", "0.0.0.0")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", "8001"))
    host = _get_bind_host()
    log_level = "debug" if DEBUG_MODE else "info"
    logger.info(f"API binding to http://{host}:{port} — access dashboard and control bot from browser")
    uvicorn.run(app, host=host, port=port, log_level=log_level)
