"""
Bot state persistence for restart recovery.
Saves/loads last_cycle_at, current_symbols, no_trade_streak, cycle_number.
Used with BOT_RECOVERY_WINDOW_MINUTES to resume or start fresh.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from api.utils.timeutils import utcnow as _naive_utcnow

logger = logging.getLogger(__name__)

# Project root: parent of api/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _state_path() -> Path:
    path = os.getenv("BOT_STATE_FILE", "").strip()
    if path:
        return Path(path).resolve()
    return _PROJECT_ROOT / "bot_state.json"


def save_bot_state(
    last_cycle_at: str,
    current_symbols: List[str],
    no_trade_streak: Dict[str, int],
    cycle_number: int,
) -> None:
    """Persist bot state to JSON (end of each cycle)."""
    path = _state_path()
    try:
        data = {
            "last_cycle_at": last_cycle_at,
            "current_symbols": current_symbols,
            "no_trade_streak": no_trade_streak,
            "cycle_number": cycle_number,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Saved bot state to {path} (cycle #{cycle_number}, {len(current_symbols)} symbols)")
    except Exception as e:
        logger.warning(f"Failed to save bot state to {path}: {e}")


def load_bot_state() -> Optional[Dict[str, Any]]:
    """Load persisted state if present. Returns None if missing or invalid."""
    path = _state_path()
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        if "last_cycle_at" not in data or "current_symbols" not in data:
            return None
        return data
    except Exception as e:
        logger.warning(f"Failed to load bot state from {path}: {e}")
        return None


def should_resume(state: Dict[str, Any], recovery_minutes: int) -> bool:
    """
    True if we should resume from saved state (within recovery window).
    False if we should start fresh (stale or no state).
    """
    try:
        last_at = state.get("last_cycle_at")
        if not last_at:
            return False
        if isinstance(last_at, str):
            # ISO format: support Z (UTC) or naive local
            s = last_at.strip().replace("Z", "+00:00")
            if "+" in s or s.endswith("-") or (len(s) >= 6 and s[-3] in "+-"):
                dt = datetime.fromisoformat(s)
            else:
                dt = datetime.fromisoformat(s)
            # Normalize to naive UTC for comparison
            if dt.tzinfo:
                from datetime import timezone
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            now = _naive_utcnow()
            delta_minutes = (now - dt).total_seconds() / 60
            return 0 <= delta_minutes <= recovery_minutes
        return False
    except Exception as e:
        logger.debug(f"should_resume check failed: {e}")
        return False
