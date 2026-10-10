#!/usr/bin/env bash
# Unified start script for Market-Pie5-Bot.
# Single entry point for API and frontend.
# Disk / Docker: ./scripts/cleanup_docker_disk.sh (df + builder prune); see also scripts/docker_cleanup.sh for container/image cleanup.
#
# Usage:
#   ./scripts/start.sh              # Full dev stack (API + frontend)
#   ./scripts/start.sh --dev        # Same as default
#   ./scripts/start.sh --api-only   # API only (foreground)
#
# Stop: ./scripts/stop.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$APP_ROOT"

API_PORT="${API_PORT:-8002}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# Parse flags
API_ONLY=
DEV=1
for arg in "$@"; do
  case "$arg" in
    --api-only) API_ONLY=1; DEV= ;;
    -h|--help)
      echo "Usage: ./scripts/start.sh [OPTIONS]"
      echo "  (no args)     Full dev stack (API + frontend)"
      echo "  --dev        Same as default"
      echo "  --api-only   API only (foreground)"
      echo ""
      echo "Stop: ./scripts/stop.sh"
      exit 0
      ;;
  esac
done

# Activate venv if present
if [ -d "$APP_ROOT/venv" ]; then
  source "$APP_ROOT/venv/bin/activate"
fi

# --- API only ---
if [ -n "$API_ONLY" ]; then
  echo "Starting Market Bot API on http://0.0.0.0:${API_PORT}"
  echo "  Frontend: cd frontend && npm run dev (in another terminal)"
  exec python3 -m uvicorn api.main:app --host 0.0.0.0 --port "$API_PORT" --reload
fi

# --- Full dev (API + frontend) ---
# Start API in background if not already running
if ! curl -s "http://localhost:${API_PORT}/api/health" >/dev/null 2>&1; then
  echo "Starting API in background on port ${API_PORT}..."
  nohup python3 -m uvicorn api.main:app --host 0.0.0.0 --port "$API_PORT" --reload >> /tmp/market-bot-api.log 2>&1 &
  API_PID=$!
  echo "  API PID: $API_PID (logs: /tmp/market-bot-api.log)"
  # Wait for API to be ready
  for i in $(seq 1 30); do
    if curl -s "http://localhost:${API_PORT}/api/health" >/dev/null 2>&1; then
      echo "  API ready."
      break
    fi
    [ "$i" -eq 30 ] && { echo "  API failed to start. Check /tmp/market-bot-api.log"; exit 1; }
    sleep 1
  done
else
  echo "API already running on port ${API_PORT}"
fi

echo ""
echo "Starting frontend on http://localhost:${FRONTEND_PORT}"
echo "  Open http://localhost:${FRONTEND_PORT} in your browser"
echo "  Stop all: ./scripts/stop.sh"
echo ""

cd "$APP_ROOT/frontend"
exec npm run dev
