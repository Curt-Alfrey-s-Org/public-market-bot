"""
Logs Routes
Provides access to bot logs with JSON parsing, filtering, and querying
"""

import asyncio
import json
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Project root (same as api/main.py) so trading_bot.log path is consistent
def _log_file_path():
    return Path(__file__).resolve().parent.parent.parent / "trading_bot.log"

def _read_tail_lines(path: Path, max_lines: int = 5000) -> list:
    """Read last max_lines from file without loading entire file (avoids blocking on huge logs)."""
    try:
        with open(path, 'rb') as f:
            f.seek(0, 2)
            size = f.tell()
            if size == 0:
                return []
            read_size = min(size, 2 * 1024 * 1024)  # Last ~2MB
            f.seek(max(0, size - read_size))
            data = f.read().decode('utf-8', errors='ignore')
        lines = data.splitlines()
        return lines[-max_lines:] if len(lines) > max_lines else lines
    except Exception as e:
        logger.warning(f"Error reading log tail: {e}")
        return []

def _try_parse_json_log(line: str) -> Optional[Dict[str, Any]]:
    """Try to parse line as JSON log (python-json-logger format)."""
    try:
        return json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return None

def _parse_log_entry(line: str) -> Dict[str, Any]:
    """
    Parse a log line into a structured entry.
    Attempts JSON parsing first (structlog/python-json-logger format).
    Falls back to text format parsing.
    """
    # Try JSON format first
    json_data = _try_parse_json_log(line)
    if json_data:
        return {
            "raw": line,
            "timestamp": json_data.get("asctime") or json_data.get("timestamp") or "",
            "level": json_data.get("levelname") or json_data.get("level") or "INFO",
            "logger": json_data.get("name") or json_data.get("logger") or "",
            "message": json_data.get("message") or "",
            "symbol": json_data.get("symbol"),
            "status": json_data.get("status"),
            "event": json_data.get("event"),
            "context": {k: v for k, v in json_data.items() 
                       if k not in ["asctime", "timestamp", "levelname", "level", "name", "logger", "message"]},
            "is_json": True
        }
    
    # Fallback to text format: YYYY-MM-DD HH:MM:SS - logger - LEVEL - message
    line = line.strip()
    entry = {
        "raw": line,
        "timestamp": "",
        "level": "INFO",
        "logger": "",
        "message": line,
        "symbol": None,
        "status": None,
        "event": None,
        "context": {},
        "is_json": False
    }
    
    # Try to extract timestamp and level from text format
    parts = line.split(' - ', 3)
    if len(parts) >= 3:
        entry["timestamp"] = parts[0] if len(parts) > 0 else ""
        entry["logger"] = parts[1] if len(parts) > 1 else ""
        level_part = parts[2] if len(parts) > 2 else ""
        entry["message"] = parts[3] if len(parts) > 3 else line
        
        # Extract level
        for log_level in ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']:
            if log_level in level_part:
                entry["level"] = log_level
                break
        
        # Try to extract symbol and status from message (for backward compat with text logs)
        msg_lower = entry["message"].lower()
        if "symbol=" in msg_lower:
            try:
                symbol_start = msg_lower.index("symbol=") + 7
                symbol_end = msg_lower.find(" ", symbol_start)
                if symbol_end == -1:
                    symbol_end = msg_lower.find(",", symbol_start)
                if symbol_end == -1:
                    symbol_end = len(msg_lower)
                entry["symbol"] = entry["message"][symbol_start:symbol_end].strip()
            except (ValueError, IndexError):
                pass
        
        if "status=" in msg_lower:
            try:
                status_start = msg_lower.index("status=") + 7
                status_end = msg_lower.find(" ", status_start)
                if status_end == -1:
                    status_end = msg_lower.find(",", status_start)
                if status_end == -1:
                    status_end = len(msg_lower)
                entry["status"] = entry["message"][status_start:status_end].strip()
            except (ValueError, IndexError):
                pass
    
    return entry

def _parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse timestamp from various formats."""
    if not ts_str:
        return None
    
    formats = [
        "%Y-%m-%d %H:%M:%S,%f",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(ts_str.split(',')[0] if ',' in ts_str else ts_str, fmt)
        except ValueError:
            continue
    
    return None

@router.get("")
async def get_logs(
    limit: Optional[int] = Query(100, description="Number of log lines to return"),
    level: Optional[str] = Query(None, description="Filter by log level (INFO, WARNING, ERROR, CRITICAL, DEBUG)"),
    logger_name: Optional[str] = Query(None, description="Filter by logger name"),
    symbol: Optional[str] = Query(None, description="Filter by trading symbol (e.g., AAPL, BTCUSD)"),
    status: Optional[str] = Query(None, description="Filter by trade status (e.g., executed, pending, failed)"),
    search: Optional[str] = Query(None, description="Search text in log messages"),
    start_time: Optional[str] = Query(None, description="Start time (ISO 8601, e.g., 2024-02-15T10:30:00)"),
    end_time: Optional[str] = Query(None, description="End time (ISO 8601, e.g., 2024-02-15T11:30:00)"),
    sort_by: Optional[str] = Query("timestamp", description="Sort by: timestamp, level, logger"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc (desc = newest first)"),
):
    """
    Get bot logs with comprehensive filtering and querying.
    
    Examples:
    - /api/logs?limit=50 → Last 50 log lines
    - /api/logs?symbol=AAPL → Logs for AAPL trades
    - /api/logs?status=pending → Logs for pending trades
    - /api/logs?level=ERROR → Error logs only
    - /api/logs?symbol=AAPL&status=executed → AAPL trades that executed
    - /api/logs?start_time=2024-02-15T10:00:00&end_time=2024-02-15T11:00:00 → Time window
    """
    try:
        log_file = _log_file_path()
        if not log_file.exists():
            return {
                "logs": [],
                "total": 0,
                "filtered_count": 0,
                "file": str(log_file),
                "exists": False
            }

        # Read last ~2MB in thread pool to avoid blocking event loop on huge log files
        lines = await asyncio.to_thread(_read_tail_lines, log_file, max_lines=10000)

        # Parse log entries
        log_entries = [_parse_log_entry(line) for line in lines if line.strip()]

        # Apply filters
        filtered_entries = log_entries

        # Filter by level
        if level and level.upper() != 'ALL':
            level_upper = level.upper()
            filtered_entries = [e for e in filtered_entries if e["level"] == level_upper]
        
        # Filter by logger name
        if logger_name:
            logger_lower = logger_name.lower()
            filtered_entries = [e for e in filtered_entries if logger_lower in e["logger"].lower()]
        
        # Filter by symbol (case-insensitive)
        if symbol:
            symbol_upper = symbol.upper()
            filtered_entries = [e for e in filtered_entries 
                              if e["symbol"] and e["symbol"].upper() == symbol_upper]
        
        # Filter by status (case-insensitive)
        if status:
            status_lower = status.lower()
            filtered_entries = [e for e in filtered_entries 
                              if e["status"] and e["status"].lower() == status_lower]
        
        # Filter by search text in message
        if search:
            search_lower = search.lower()
            filtered_entries = [e for e in filtered_entries 
                              if search_lower in e["message"].lower() or search_lower in e["raw"].lower()]
        
        # Filter by time range
        start_dt = _parse_timestamp(start_time) if start_time else None
        end_dt = _parse_timestamp(end_time) if end_time else None
        
        if start_dt or end_dt:
            filtered_by_time = []
            for e in filtered_entries:
                entry_ts = _parse_timestamp(e["timestamp"])
                if entry_ts:
                    if start_dt and entry_ts < start_dt:
                        continue
                    if end_dt and entry_ts > end_dt:
                        continue
                filtered_by_time.append(e)
            filtered_entries = filtered_by_time
        
        # Sort entries
        if sort_by == "timestamp":
            filtered_entries.sort(key=lambda x: x["timestamp"] or "", reverse=(sort_order == "desc"))
        elif sort_by == "level":
            level_order = {"CRITICAL": 0, "ERROR": 1, "WARNING": 2, "INFO": 3, "DEBUG": 4}
            filtered_entries.sort(key=lambda x: level_order.get(x["level"], 99), reverse=(sort_order == "desc"))
        elif sort_by == "logger":
            filtered_entries.sort(key=lambda x: x["logger"] or "", reverse=(sort_order == "desc"))
        
        # Limit result set
        total_found = len(filtered_entries)
        filtered_entries = filtered_entries[:limit]
        
        return {
            "logs": filtered_entries,
            "total": len(log_entries),
            "filtered_count": total_found,
            "returned": len(filtered_entries),
            "limit": limit,
            "file": str(log_file),
            "exists": True,
            "filters_applied": {
                "level": level,
                "logger": logger_name,
                "symbol": symbol,
                "status": status,
                "search": search,
                "start_time": start_time,
                "end_time": end_time,
            }
        }
    except Exception as e:
        logger.error(f"Error reading logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {str(e)}")
