"""
Startup Recovery Module

Auto-loads market data on bot restart if database is empty.
Fetches initial data from yfinance with 60s timeout and graceful degradation.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Default symbols to fetch if none are configured
DEFAULT_SYMBOLS = ["AAPL", "SPY", "QQQ"]

# Startup status tracking
_startup_status: Dict[str, Any] = {
    "initialized": False,
    "timestamp": None,
    "symbol_count": 0,
    "error": None,
}


def get_startup_status() -> Dict[str, Any]:
    """
    Get current startup status.

    Returns:
        Dict with:
        - initialized: bool - whether bot data initialized
        - timestamp: str|null - ISO timestamp of last initialization
        - symbol_count: int - number of symbols initialized
        - error: str|null - error message if initialization failed
    """
    return _startup_status.copy()


async def initialize_bot_data() -> Dict[str, Any]:
    """
    Initialize bot market data on startup.

    Checks if bot_state.json exists and has data, or if database has market snapshots.
    If empty: fetches initial yfinance data (AAPL, SPY, QQQ) with 60s timeout.
    If successful: logs "Bot data initialized" with timestamp.
    If fails: logs warning but doesn't crash, returns 503 status later.

    Returns:
        Dict with:
        - initialized: bool - whether data was initialized
        - timestamp: str - ISO timestamp of initialization
        - symbol_count: int - number of symbols loaded/fetched
    """
    global _startup_status

    try:
        logger.info("[STARTUP] Beginning bot data initialization...")
        start_time = datetime.now()

        # Check if bot_state.json exists and has data
        bot_state_path = Path(__file__).parent.parent / "bot_state.json"
        if bot_state_path.exists():
            try:
                with open(bot_state_path, 'r') as f:
                    bot_state = json.load(f)
                if bot_state and isinstance(bot_state, dict) and len(bot_state) > 0:
                    logger.info(
                        f"[STARTUP] Bot state file found with {len(bot_state)} entries. "
                        f"Skipping data fetch."
                    )
                    _startup_status = {
                        "initialized": True,
                        "timestamp": start_time.isoformat(),
                        "symbol_count": len(bot_state),
                        "error": None,
                    }
                    return _startup_status
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(
                    f"[STARTUP] Could not read bot_state.json: {str(e)[:100]}. "
                    f"Proceeding with yfinance fetch."
                )

        # Check if database has data (optional - depends on your DB setup)
        try:
            from database import SessionLocal
            db = SessionLocal()
            try:
                # Try to count existing trade records or market data
                # This is a placeholder - adjust based on your actual schema
                result = db.execute("SELECT COUNT(*) FROM trades LIMIT 1")
                count = result.scalar() or 0
                if count > 0:
                    logger.info(
                        f"[STARTUP] Database contains {count} trade records. "
                        f"Skipping yfinance fetch."
                    )
                    _startup_status = {
                        "initialized": True,
                        "timestamp": start_time.isoformat(),
                        "symbol_count": count,
                        "error": None,
                    }
                    return _startup_status
            finally:
                db.close()
        except Exception as e:
            logger.debug(f"[STARTUP] Could not check database: {str(e)[:100]}")

        # Fetch initial data from yfinance
        logger.info(
            f"[STARTUP] Database is empty. Fetching initial market data from yfinance "
            f"for {DEFAULT_SYMBOLS}..."
        )

        try:
            import yfinance
            
            fetched_symbols = []
            fetch_start = datetime.now()

            for symbol in DEFAULT_SYMBOLS:
                try:
                    # Fetch with 60s timeout
                    ticker = yfinance.Ticker(symbol)
                    history = await asyncio.wait_for(
                        asyncio.to_thread(lambda s=symbol: yfinance.Ticker(s).history(period="1d", interval="1m")),
                        timeout=60.0
                    )
                    if history is not None and len(history) > 0:
                        fetched_symbols.append(symbol)
                        logger.debug(
                            f"[STARTUP] Fetched {len(history)} data points for {symbol}"
                        )
                    else:
                        logger.warning(
                            f"[STARTUP] No data returned from yfinance for {symbol}"
                        )
                except asyncio.TimeoutError:
                    logger.warning(
                        f"[STARTUP] yfinance fetch timeout for {symbol} (60s limit exceeded)"
                    )
                except Exception as e:
                    logger.warning(
                        f"[STARTUP] Could not fetch data for {symbol}: {str(e)[:100]}"
                    )

            fetch_elapsed = (datetime.now() - fetch_start).total_seconds()

            if fetched_symbols:
                logger.info(
                    f"[STARTUP] Bot data initialized. Fetched {len(fetched_symbols)} symbols "
                    f"({', '.join(fetched_symbols)}) in {fetch_elapsed:.1f}s. "
                    f"Timestamp: {start_time.isoformat()}"
                )
                _startup_status = {
                    "initialized": True,
                    "timestamp": start_time.isoformat(),
                    "symbol_count": len(fetched_symbols),
                    "error": None,
                }
                return _startup_status
            else:
                logger.warning(
                    f"[STARTUP] Failed to fetch any symbols in {fetch_elapsed:.1f}s. "
                    f"Bot will continue but may be degraded."
                )
                _startup_status = {
                    "initialized": False,
                    "timestamp": start_time.isoformat(),
                    "symbol_count": 0,
                    "error": "Failed to fetch yfinance data",
                }
                return _startup_status

        except ImportError:
            logger.error(
                "[STARTUP] yfinance not installed. Cannot fetch initial data. "
                "Bot will continue with degraded functionality."
            )
            _startup_status = {
                "initialized": False,
                "timestamp": start_time.isoformat(),
                "symbol_count": 0,
                "error": "yfinance not installed",
            }
            return _startup_status

    except Exception as e:
        logger.error(
            f"[STARTUP] Unexpected error during initialization: {str(e)[:200]}. "
            f"Bot will continue but may be degraded."
        )
        _startup_status = {
            "initialized": False,
            "timestamp": datetime.now().isoformat(),
            "symbol_count": 0,
            "error": str(e)[:100],
        }
        return _startup_status


def set_startup_time(timestamp: float) -> None:
    """
    Set startup time (called from main.py lifespan).

    Args:
        timestamp: Start time as float (time.time())
    """
    _startup_status["timestamp"] = datetime.fromtimestamp(timestamp).isoformat()
    logger.debug(f"[STARTUP] Set startup time: {_startup_status['timestamp']}")
