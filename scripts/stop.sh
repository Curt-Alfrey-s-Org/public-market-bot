#!/usr/bin/env bash
# Stop Market-Pie5-Bot API and frontend.
#
# Usage: ./scripts/stop.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

API_PORT="${API_PORT:-8002}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

echo "Stopping Market Bot..."

# Stop API (uvicorn)
if pkill -f "uvicorn api.main" 2>/dev/null; then
  echo "  Stopped API (uvicorn)"
else
  echo "  No API process found"
fi

# Stop processes on API port
if command -v lsof >/dev/null 2>&1; then
  PID=$(lsof -ti ":$API_PORT" 2>/dev/null || true)
  if [ -n "$PID" ]; then
    kill $PID 2>/dev/null || kill -9 $PID 2>/dev/null || true
    echo "  Stopped process on port $API_PORT"
  fi
fi

# Stop frontend (by port - Vite uses 5173)
if command -v lsof >/dev/null 2>&1; then
  PID=$(lsof -ti ":$FRONTEND_PORT" 2>/dev/null || true)
  if [ -n "$PID" ]; then
    kill $PID 2>/dev/null || kill -9 $PID 2>/dev/null || true
    echo "  Stopped frontend (port $FRONTEND_PORT)"
  fi
fi

echo "Done."
