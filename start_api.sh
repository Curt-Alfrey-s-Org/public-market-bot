#!/bin/bash
# Start FastAPI server (local 192 net only by default)
# Usage: ./start_api.sh
# Set API_HOST=0.0.0.0 to allow all interfaces, or API_HOST=192.0.2.21 for a specific IP.

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set API port (default 8002; 8000 often assigned to other services e.g. Yacht)
export API_PORT=${API_PORT:-8002}

# Bind host: API_HOST env, or auto-detect 192.0.2.21 for local network only
get_host() {
  echo "${API_HOST:-0.0.0.0}"
}
API_BIND=$(get_host)

echo "Market Bot API starting on http://${API_BIND}:${API_PORT}"
echo "  Open in browser to control bot (start/stop). Set API_HOST=0.0.0.0 to allow all interfaces."
python3 -m uvicorn api.main:app --host "$API_BIND" --port $API_PORT --reload
