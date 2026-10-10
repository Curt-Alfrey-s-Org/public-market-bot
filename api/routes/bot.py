"""
Bot Control Routes
Handles bot start/stop/shutdown and mode selection
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel
from api.utils import get_bot_instance
from api.auth import require_admin  # control endpoints: admin JWT only (not the API key)
from api.models.responses import StatusResponse, ErrorResponse
from api.bot_manager import start_bot, stop_bot, shutdown_bot, is_bot_running, get_bot_status as get_manager_status, BrainUnavailableError
from api.runtime_env import runtime_env_file, writable_runtime_env_file, read_runtime_env, not_persisted_reason
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter()

class ModeRequest(BaseModel):
    mode: str


class StartRequest(BaseModel):
    """Optional body for POST /start: use this mode when starting (overrides .env)."""
    mode: Optional[str] = None


def _env_file_path() -> Optional[str]:
    """Runtime env file (single source for multi-worker consistency), or None when changes
    must not be written to disk (container without BOT_RUNTIME_ENV_FILE). See api/runtime_env.py."""
    path = runtime_env_file()
    return str(path) if path is not None else None


def _get_mode_from_env_file() -> Optional[str]:
    """Read current mode from the runtime env file so all API workers report the same value when bot is not running."""
    env_file = _env_file_path()
    if not env_file or not os.path.exists(env_file):
        return None
    env = read_runtime_env()
    if not env:
        return None
    paper_mode = env.get('PAPER_TRADING_MODE', 'true').lower() == 'true'
    sandbox_mode = env.get('SCHWAB_SANDBOX_MODE', 'false').lower() == 'true'
    dry_run = env.get('DRY_RUN_MODE', 'false').lower() == 'true'
    if dry_run:
        return 'dryrun-live'
    if not paper_mode:
        return 'live'
    if sandbox_mode:
        return 'sandbox'
    return 'yfinance'


def _apply_mode_to_env(mode: str) -> None:
    """Set os.environ and .env file for the given mode. Used by POST /mode and POST /start."""
    valid = ['sandbox', 'live', 'yfinance', 'dryrun-live']
    if mode not in valid:
        return
    if mode == 'live':
        os.environ['PAPER_TRADING_MODE'] = 'false'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        os.environ['SCHWAB_API_ENABLED'] = 'on'
        os.environ['DRY_RUN_MODE'] = 'false'
        os.environ['WEB_GUI_CONTINUOUS_TRADING'] = 'true'
        os.environ['WEB_GUI_DEBUG'] = 'false'
        os.environ['ENABLE_PDT_RULES'] = 'true'
    elif mode == 'sandbox':
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
        os.environ['SCHWAB_API_ENABLED'] = 'on'
        os.environ['DRY_RUN_MODE'] = 'false'
        os.environ['WEB_GUI_CONTINUOUS_TRADING'] = 'true'
        os.environ['WEB_GUI_DEBUG'] = 'false'
        os.environ['ENABLE_PDT_RULES'] = 'false'
    elif mode == 'yfinance':
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        os.environ['SCHWAB_API_ENABLED'] = 'off'
        os.environ['DRY_RUN_MODE'] = 'false'
        os.environ['WEB_GUI_CONTINUOUS_TRADING'] = 'true'
        os.environ['WEB_GUI_DEBUG'] = 'true'
        os.environ['ENABLE_PDT_RULES'] = 'false'
    elif mode == 'dryrun-live':
        os.environ['PAPER_TRADING_MODE'] = 'false'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        os.environ['SCHWAB_API_ENABLED'] = 'on'
        os.environ['DRY_RUN_MODE'] = 'true'
        os.environ['WEB_GUI_CONTINUOUS_TRADING'] = 'true'
        os.environ['WEB_GUI_DEBUG'] = 'true'
        os.environ['ENABLE_PDT_RULES'] = 'true'
    env_path = writable_runtime_env_file()
    if env_path is None:
        if runtime_env_file() is None:
            logger.info(f"Mode {mode} applied to this API process only (not persisted): {not_persisted_reason()}")
        return
    env_file = str(env_path)
    mode_settings = {
        'live': {'PAPER_TRADING_MODE': 'false', 'SCHWAB_SANDBOX_MODE': 'false', 'SCHWAB_API_ENABLED': 'on', 'DRY_RUN_MODE': 'false', 'WEB_GUI_CONTINUOUS_TRADING': 'true', 'WEB_GUI_DEBUG': 'false', 'ENABLE_PDT_RULES': 'true'},
        'sandbox': {'PAPER_TRADING_MODE': 'true', 'SCHWAB_SANDBOX_MODE': 'true', 'SCHWAB_API_ENABLED': 'on', 'DRY_RUN_MODE': 'false', 'WEB_GUI_CONTINUOUS_TRADING': 'true', 'WEB_GUI_DEBUG': 'false', 'ENABLE_PDT_RULES': 'false'},
        'yfinance': {'PAPER_TRADING_MODE': 'true', 'SCHWAB_SANDBOX_MODE': 'false', 'SCHWAB_API_ENABLED': 'off', 'DRY_RUN_MODE': 'false', 'WEB_GUI_CONTINUOUS_TRADING': 'true', 'WEB_GUI_DEBUG': 'true', 'ENABLE_PDT_RULES': 'false'},
        'dryrun-live': {'PAPER_TRADING_MODE': 'false', 'SCHWAB_SANDBOX_MODE': 'false', 'SCHWAB_API_ENABLED': 'on', 'DRY_RUN_MODE': 'true', 'WEB_GUI_CONTINUOUS_TRADING': 'true', 'WEB_GUI_DEBUG': 'true', 'ENABLE_PDT_RULES': 'true'},
    }
    settings_to_update = mode_settings.get(mode, {})
    settings_found = {k: False for k in settings_to_update}
    try:
        with open(env_file, 'r') as f:
            lines = f.readlines()
        new_lines = []
        for line in lines:
            updated_line = False
            for key, val in settings_to_update.items():
                if line.strip().startswith(f'{key}='):
                    new_lines.append(f"{key}={val}\n")
                    settings_found[key] = True
                    updated_line = True
                    break
            if not updated_line:
                new_lines.append(line)
        for key, val in settings_to_update.items():
            if not settings_found[key]:
                new_lines.append(f"{key}={val}\n")
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        logger.info(f"Applied mode {mode} to runtime env file {env_file}")
    except Exception as e:
        logger.warning(f"Could not update runtime env file for mode {mode}: {e}")


@router.get("/status", response_model=StatusResponse)
async def get_bot_status():
    """Get bot status"""
    import os
    
    try:
        bot = get_bot_instance()
        if not bot:
            # Read mode from .env file so all workers report the same value (avoids multi-worker drift)
            mode = _get_mode_from_env_file()
            if mode is None:
                paper_mode = os.getenv('PAPER_TRADING_MODE', 'true').lower() == 'true'
                sandbox_mode = os.getenv('SCHWAB_SANDBOX_MODE', 'false').lower() == 'true'
                dry_run = os.getenv('DRY_RUN_MODE', 'false').lower() == 'true'
                if dry_run:
                    mode = 'dryrun-live'
                elif not paper_mode:
                    mode = 'live'
                elif sandbox_mode:
                    mode = 'sandbox'
                else:
                    mode = 'yfinance'
            return StatusResponse(
                running=False,
                mode=mode
            )
        
        # Get mode from bot instance
        mode = 'unknown'
        if hasattr(bot, 'mode') and bot.mode:
            mode = bot.mode
        elif hasattr(bot, 'trading_mode') and bot.trading_mode:
            mode = bot.trading_mode
        elif hasattr(bot, 'get_mode'):
            mode = bot.get_mode()
        else:
            # Fallback: determine from environment
            paper_mode = os.getenv('PAPER_TRADING_MODE', 'true').lower() == 'true'
            sandbox_mode = os.getenv('SCHWAB_SANDBOX_MODE', 'false').lower() == 'true'
            dry_run = os.getenv('DRY_RUN_MODE', 'false').lower() == 'true'
            
            if dry_run:
                mode = 'dryrun-live'
            elif not paper_mode:
                mode = 'live'
            elif sandbox_mode:
                mode = 'sandbox'
            else:
                mode = 'yfinance'
        
        status_dict = get_manager_status()
        return StatusResponse(
            running=status_dict.get("running", getattr(bot, 'running', False)),
            mode=mode,
            no_trade_reasons=status_dict.get("no_trade_reasons") or None
        )
    except Exception as e:
        logger.error(f"Error getting bot status: {e}", exc_info=True)
        mode = _get_mode_from_env_file()
        if mode is None:
            paper_mode = os.getenv('PAPER_TRADING_MODE', 'true').lower() == 'true'
            sandbox_mode = os.getenv('SCHWAB_SANDBOX_MODE', 'false').lower() == 'true'
            dry_run = os.getenv('DRY_RUN_MODE', 'false').lower() == 'true'
            if dry_run:
                mode = 'dryrun-live'
            elif not paper_mode:
                mode = 'live'
            elif sandbox_mode:
                mode = 'sandbox'
            else:
                mode = 'yfinance'
        return StatusResponse(
            running=False,
            mode=mode
        )

@router.post("/start", dependencies=[Depends(require_admin)])
async def start_bot_endpoint(request: Optional[StartRequest] = Body(None)):
    """Start the bot. Optional body: { \"mode\": \"yfinance\" } to use that mode when starting (overrides .env)."""
    try:
        if is_bot_running():
            return {"message": "Bot is already running", "status": "running", "running": True}
        # If UI sends current mode, apply it before start so Start always runs the displayed mode
        if request is not None and getattr(request, 'mode', None):
            mode = request.mode.strip().lower()
            if mode in ('sandbox', 'live', 'yfinance', 'dryrun-live'):
                _apply_mode_to_env(mode)
                logger.info(f"Start requested with mode={mode}; applied to env before start")
        success = start_bot()
        if success:
            return {"message": "Bot started successfully", "status": "started", "running": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to start bot")
    except BrainUnavailableError as e:
        logger.error(f"Start blocked — AI brain unavailable: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {str(e)}")

@router.post("/stop", dependencies=[Depends(require_admin)])
async def stop_bot_endpoint():
    """Stop the bot (pauses trading but keeps instance alive)"""
    try:
        if not is_bot_running():
            return {"message": "Bot is not running", "status": "stopped", "running": False}
        
        success = stop_bot()
        if success:
            return {"message": "Bot stopped successfully", "status": "stopped", "running": False}
        else:
            raise HTTPException(status_code=500, detail="Failed to stop bot")
    except Exception as e:
        logger.error(f"Error stopping bot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stop bot: {str(e)}")

@router.post("/shutdown", dependencies=[Depends(require_admin)])
async def shutdown_bot_endpoint():
    """Shutdown the bot completely (stops and cleans up)"""
    try:
        # Shutdown works whether bot is running or stopped
        # It will stop if running, then clean up the instance
        success = shutdown_bot()
        if success:
            return {"message": "Bot shutdown complete", "status": "shutdown", "running": False}
        else:
            # Even if stop_bot() returns False (bot already stopped), 
            # shutdown_bot() should still clean up, so this shouldn't happen
            # But handle it gracefully
            return {"message": "Bot shutdown complete (was already stopped)", "status": "shutdown", "running": False}
    except Exception as e:
        logger.error(f"Error shutting down bot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to shutdown bot: {str(e)}")

@router.post("/shutdown-server", dependencies=[Depends(require_admin)])
async def shutdown_server_endpoint():
    """Shutdown the API server completely (stops bot and API). Process exits so terminal returns."""
    import os
    import signal
    import threading
    import time
    
    try:
        logger.info("API server shutdown requested from GUI")
        
        def shutdown_delayed():
            # Give HTTP response time to reach the client first
            time.sleep(0.5)
            
            # Now shutdown the bot (this can take up to 10 seconds)
            logger.info("Shutting down bot...")
            try:
                shutdown_bot()
            except Exception as e:
                logger.error(f"Error during bot shutdown: {e}", exc_info=True)
                # Continue with server shutdown even if bot shutdown fails
            
            # Wait a moment after bot shutdown before terminating process
            time.sleep(0.5)
            
            logger.info("Shutting down API server...")
            try:
                my_pid = os.getpid()
                parent_pid = os.getppid()
                parent_is_uvicorn = False

                # With uvicorn --reload: we are the worker, parent is the reloader. We must kill
                # the parent so the terminal returns to the shell prompt (start_api.sh exits).
                if parent_pid != 1:
                    try:
                        # Prefer psutil (works on Linux, macOS, Windows)
                        try:
                            import psutil
                            parent = psutil.Process(parent_pid)
                            cmdline = " ".join(parent.cmdline() or [])
                            parent_is_uvicorn = "uvicorn" in cmdline.lower()
                        except (ImportError, psutil.NoSuchProcess, psutil.AccessDenied):
                            # Fallback: Linux /proc
                            cmdline_path = f"/proc/{parent_pid}/cmdline"
                            if os.path.exists(cmdline_path):
                                with open(cmdline_path, "rb") as f:
                                    cmdline = f.read().replace(b"\x00", b" ").decode("utf-8", errors="ignore")
                                parent_is_uvicorn = "uvicorn" in cmdline.lower()

                        if parent_is_uvicorn:
                            os.kill(parent_pid, signal.SIGTERM)
                            for _ in range(25):
                                time.sleep(0.2)
                                try:
                                    os.kill(parent_pid, 0)
                                except ProcessLookupError:
                                    break
                            else:
                                try:
                                    os.kill(parent_pid, signal.SIGKILL)
                                    time.sleep(0.3)
                                except (ProcessLookupError, OSError):
                                    pass
                    except (OSError, PermissionError):
                        pass

                # Send SIGTERM to our process group so the whole server tree exits and the
                # terminal returns to the shell prompt without needing Ctrl+C.
                try:
                    if hasattr(os, "killpg") and hasattr(os, "getpgrp"):
                        pgid = os.getpgrp()
                        os.killpg(pgid, signal.SIGTERM)
                        time.sleep(0.5)
                except (OSError, PermissionError, ProcessLookupError):
                    pass

                # Force-exit this process so the terminal is no longer running the server
                os._exit(0)
            except Exception as e:
                logger.error(f"Error during shutdown: {e}", exc_info=True)
                try:
                    os._exit(0)
                except Exception:
                    os.kill(os.getpid(), signal.SIGKILL)
        
        shutdown_thread = threading.Thread(target=shutdown_delayed, daemon=False)
        shutdown_thread.start()
        
        return {
            "message": "API server shutdown initiated. The server will close in a moment.",
            "status": "shutting_down"
        }
    except Exception as e:
        logger.error(f"Error shutting down server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to shutdown server: {str(e)}")

@router.post("/mode", dependencies=[Depends(require_admin)])
async def set_bot_mode(request: ModeRequest):
    """Set bot trading mode - updates environment variables and bot instance
    Mode can only be changed when bot is NOT running"""
    import os
    
    bot = get_bot_instance()
    
    # Prevent mode change when bot is running
    if is_bot_running():
        raise HTTPException(
            status_code=400, 
            detail="Cannot change mode while bot is running. Please stop the bot first."
        )
    
    mode = request.mode
    if not mode:
        raise HTTPException(status_code=400, detail="Mode parameter is required")
    
    valid_modes = ['sandbox', 'live', 'yfinance', 'dryrun-live']
    if mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Must be one of: {valid_modes}")
    
    try:
        # Update environment and .env so mode persists and is used when bot starts
        _apply_mode_to_env(mode)
        logger.info(f"Updated .env file with mode: {mode}")
        
        # If bot instance exists but is NOT running, shutdown it so it reinitializes with new settings
        # This ensures the bot picks up ALL the updated environment variables
        if bot and not is_bot_running():
            logger.info(f"Shutting down existing bot instance to reinitialize with mode: {mode}")
            from api.bot_manager import shutdown_bot
            shutdown_bot()
            logger.info(f"Bot will be reinitialized with new mode settings when started")
        else:
            logger.info(f"Mode preference set to: {mode} (will apply when bot starts)")
        
        return {
            "message": f"Mode changed to {mode}. {'Bot instance updated.' if bot and not is_bot_running() else 'Mode will apply when bot starts.'}",
            "mode": mode,
            "status": "success",
            "bot_available": bot is not None,
            "requires_restart": False  # Mode is set before start, no restart needed
        }
    except Exception as e:
        logger.error(f"Error setting bot mode: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to set mode: {str(e)}")
