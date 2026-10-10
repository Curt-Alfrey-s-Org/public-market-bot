#!/bin/bash
# Start both FastAPI backend and React frontend

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Startup timing
STARTUP_START=$(date +%s.%N)
echo -e "${BLUE}Starting Market Bot GUI...${NC}"
echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] Startup began${NC}"

# Check if virtual environment exists
VENV_START=$(date +%s.%N)
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment${NC}"
        exit 1
    fi
    VENV_END=$(date +%s.%N)
    VENV_ELAPSED=$(python3 -c "print(round($VENV_END - $VENV_START, 3))" 2>/dev/null || echo "0")
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓ Virtual environment created in ${VENV_ELAPSED}s${NC}"
else
    VENV_END=$(date +%s.%N)
    VENV_ELAPSED=$(python3 -c "print(round($VENV_END - $VENV_START, 3))" 2>/dev/null || echo "0")
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓ Virtual environment ready (${VENV_ELAPSED}s)${NC}"
fi

# Activate virtual environment
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to activate virtual environment${NC}"
    exit 1
fi

# Check if uvicorn is installed
DEPS_START=$(date +%s.%N)
if ! command -v uvicorn > /dev/null 2>&1; then
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] uvicorn not found. Installing dependencies...${NC}"
    pip install -r requirements-api.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install Python dependencies${NC}"
        exit 1
    fi
    DEPS_END=$(date +%s.%N)
    DEPS_ELAPSED=$(python3 -c "print(round($DEPS_END - $DEPS_START, 3))" 2>/dev/null || echo "0")
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓ Dependencies installed in ${DEPS_ELAPSED}s${NC}"
else
    DEPS_END=$(date +%s.%N)
    DEPS_ELAPSED=$(python3 -c "print(round($DEPS_END - $DEPS_START, 3))" 2>/dev/null || echo "0")
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓ Dependencies ready (${DEPS_ELAPSED}s)${NC}"
fi

# Check if API is already running
if lsof -i :8000 > /dev/null 2>&1 || pgrep -f "uvicorn.*api.main:app" > /dev/null 2>&1; then
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠ API already running on port 8000${NC}"
    echo -e "${YELLOW}Killing existing API processes...${NC}"
    pkill -f "uvicorn.*api.main:app" 2>/dev/null
    sleep 2
fi

# Bind host: API_HOST env, or auto-detect 192.0.2.21 for local network only
get_api_host() {
  echo "${API_HOST:-0.0.0.0}"
}
API_BIND=$(get_api_host)

# Start FastAPI backend in background
API_START=$(date +%s.%N)
echo -e "${GREEN}[$(date '+%H:%M:%S')] Starting FastAPI backend on http://${API_BIND}:8000${NC}"
echo -e "${BLUE}[$(date '+%H:%M:%S')] Open http://${API_BIND}:8000 in browser to control bot (start/stop)${NC}"
cd "$SCRIPT_DIR"
uvicorn api.main:app --host "$API_BIND" --port 8000 --reload > /tmp/market-bot-api.log 2>&1 &
API_PID=$!
echo "API PID: $API_PID"

# Wait for API to be ready
echo -e "${YELLOW}[$(date '+%H:%M:%S')] Waiting for API to start...${NC}"
API_READY=0
for i in {1..30}; do
    if curl -s http://${API_BIND}:8000/api/health > /dev/null 2>&1; then
        API_END=$(date +%s.%N)
        API_ELAPSED=$(python3 -c "print(round($API_END - $API_START, 3))" 2>/dev/null || echo "0")
        echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓ API is ready! (${API_ELAPSED}s)${NC}"
        API_READY=1
        break
    fi
    sleep 1
done
if [ $API_READY -eq 0 ]; then
    API_ELAPSED=$(python3 -c "print($(date +%s.%N) - $API_START)" 2>/dev/null || echo "0")
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠ API may not be ready after ${API_ELAPSED}s, but continuing...${NC}"
fi

# Check if npm is available
if ! command -v npm > /dev/null 2>&1; then
    echo -e "${RED}npm is not installed or not in PATH${NC}"
    echo -e "${YELLOW}Please install Node.js and npm:${NC}"
    echo -e "${YELLOW}  sudo apt update && sudo apt install nodejs npm${NC}"
    exit 1
fi

# Check if frontend dependencies are installed
FRONTEND_DEPS_START=$(date +%s.%N)
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] Frontend dependencies not found. Installing...${NC}"
    cd frontend
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install frontend dependencies${NC}"
        exit 1
    fi
    cd "$SCRIPT_DIR"
    FRONTEND_DEPS_END=$(date +%s.%N)
    FRONTEND_DEPS_ELAPSED=$(python3 -c "print(round($FRONTEND_DEPS_END - $FRONTEND_DEPS_START, 3))" 2>/dev/null || echo "0")
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓ Frontend dependencies installed in ${FRONTEND_DEPS_ELAPSED}s${NC}"
else
    FRONTEND_DEPS_END=$(date +%s.%N)
    FRONTEND_DEPS_ELAPSED=$(python3 -c "print(round($FRONTEND_DEPS_END - $FRONTEND_DEPS_START, 3))" 2>/dev/null || echo "0")
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓ Frontend dependencies ready (${FRONTEND_DEPS_ELAPSED}s)${NC}"
fi

# Check if frontend is already running
if lsof -i :5173 > /dev/null 2>&1 || pgrep -f "vite.*5173" > /dev/null 2>&1 || pgrep -f "npm.*run.*dev" > /dev/null 2>&1; then
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠ Frontend already running on port 5173${NC}"
    echo -e "${YELLOW}Killing existing frontend processes...${NC}"
    pkill -f "vite.*5173" 2>/dev/null
    pkill -f "npm.*run.*dev" 2>/dev/null
    sleep 2
fi

# Start React frontend
FRONTEND_START=$(date +%s.%N)
echo -e "${GREEN}[$(date '+%H:%M:%S')] Starting React frontend on http://localhost:5173${NC}"
cd frontend
npm run dev > /tmp/market-bot-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# Wait for frontend to be ready
echo -e "${YELLOW}[$(date '+%H:%M:%S')] Waiting for frontend to start...${NC}"
FRONTEND_READY=0
for i in {1..30}; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        FRONTEND_END=$(date +%s.%N)
        FRONTEND_ELAPSED=$(python3 -c "print(round($FRONTEND_END - $FRONTEND_START, 3))" 2>/dev/null || echo "0")
        echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓ Frontend is ready! (${FRONTEND_ELAPSED}s)${NC}"
        FRONTEND_READY=1
        break
    fi
    sleep 1
done
if [ $FRONTEND_READY -eq 0 ]; then
    FRONTEND_ELAPSED=$(python3 -c "print($(date +%s.%N) - $FRONTEND_START)" 2>/dev/null || echo "0")
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠ Frontend may not be ready after ${FRONTEND_ELAPSED}s, but continuing...${NC}"
fi

# Save PIDs to file for cleanup
echo "$API_PID" > /tmp/market-bot-api.pid
echo "$FRONTEND_PID" > /tmp/market-bot-frontend.pid

# Calculate total startup time
STARTUP_END=$(date +%s.%N)
STARTUP_ELAPSED=$(python3 -c "print(round($STARTUP_END - $STARTUP_START, 3))" 2>/dev/null || echo "0")
echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓ Market Bot GUI started!${NC}"
echo -e "${BLUE}Frontend: http://localhost:5173${NC}"
echo -e "${BLUE}API: http://${API_BIND}:8000${NC}"
echo -e "${BLUE}API Docs: http://${API_BIND}:8000/docs${NC}"
echo ""
echo -e "${GREEN}=== Startup Performance Summary ===${NC}"
echo -e "  Total Startup Time: ${STARTUP_ELAPSED}s"
echo -e "  Virtual Environment: ${VENV_ELAPSED}s"
echo -e "  Backend Dependencies: ${DEPS_ELAPSED}s"
echo -e "  API Startup: ${API_ELAPSED}s"
echo -e "  Frontend Dependencies: ${FRONTEND_DEPS_ELAPSED}s"
echo -e "  Frontend Startup: ${FRONTEND_ELAPSED}s"
echo ""

# Open browser after a short delay (only once)
sleep 3

# Use lock file to prevent multiple browser opens
LOCK_FILE="/tmp/market-bot-browser-open.lock"
LOCK_TIMEOUT=10  # Lock expires after 10 seconds

# Check if lock file exists and is recent (within timeout)
BROWSER_OPENED=0
if [ -f "$LOCK_FILE" ]; then
    LOCK_AGE=$(($(date +%s) - $(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo 0)))
    if [ $LOCK_AGE -lt $LOCK_TIMEOUT ]; then
        BROWSER_OPENED=1
        echo -e "${YELLOW}Browser lock file exists (${LOCK_AGE}s old), skipping auto-open${NC}"
    else
        # Lock file is stale, remove it
        rm -f "$LOCK_FILE" 2>/dev/null
        echo -e "${YELLOW}Removed stale browser lock file${NC}"
    fi
fi

# Also check if browser opening process is still running
if [ $BROWSER_OPENED -eq 0 ]; then
    if pgrep -f "xdg-open.*localhost:5173" > /dev/null 2>&1 || \
       pgrep -f "gnome-open.*localhost:5173" > /dev/null 2>&1 || \
       pgrep -f "kde-open.*localhost:5173" > /dev/null 2>&1; then
        BROWSER_OPENED=1
        echo -e "${YELLOW}Browser opening process detected, skipping auto-open${NC}"
    fi
fi

# Check if frontend port has active connections (browser already connected)
if [ $BROWSER_OPENED -eq 0 ]; then
    if command -v ss > /dev/null 2>&1; then
        if ss -tn 2>/dev/null | grep -q ":5173.*ESTABLISHED"; then
            BROWSER_OPENED=1
            echo -e "${YELLOW}Active browser connection detected on port 5173, skipping auto-open${NC}"
        fi
    elif command -v netstat > /dev/null 2>&1; then
        if netstat -tn 2>/dev/null | grep -q ":5173.*ESTABLISHED"; then
            BROWSER_OPENED=1
            echo -e "${YELLOW}Active browser connection detected on port 5173, skipping auto-open${NC}"
        fi
    fi
fi

# Check if Firefox/Chrome is already running with localhost:5173
if [ $BROWSER_OPENED -eq 0 ]; then
    if pgrep -f "firefox.*localhost:5173" > /dev/null 2>&1 || \
       pgrep -f "chrome.*localhost:5173" > /dev/null 2>&1 || \
       pgrep -f "chromium.*localhost:5173" > /dev/null 2>&1; then
        BROWSER_OPENED=1
        echo -e "${YELLOW}Browser with localhost:5173 already running, skipping auto-open${NC}"
    fi
fi

if [ $BROWSER_OPENED -eq 0 ]; then
    # Create lock file before opening browser
    touch "$LOCK_FILE"
    echo -e "${GREEN}Opening browser...${NC}"
    
    # Open browser in background
    (
        if command -v xdg-open > /dev/null; then
            xdg-open http://localhost:5173 2>/dev/null
        elif command -v gnome-open > /dev/null; then
            gnome-open http://localhost:5173 2>/dev/null
        elif command -v kde-open > /dev/null; then
            kde-open http://localhost:5173 2>/dev/null
        elif command -v firefox > /dev/null; then
            firefox http://localhost:5173 2>/dev/null
        elif command -v google-chrome > /dev/null; then
            google-chrome http://localhost:5173 2>/dev/null
        elif command -v chromium-browser > /dev/null; then
            chromium-browser http://localhost:5173 2>/dev/null
        else
            echo -e "${YELLOW}Could not auto-open browser. Please open http://localhost:5173 manually${NC}"
            echo -e "${YELLOW}Or run: xdg-open http://localhost:5173${NC}"
        fi
        # Remove lock file after browser opens (with delay to allow browser to start)
        sleep 5
        rm -f "$LOCK_FILE" 2>/dev/null
    ) &
else
    echo -e "${YELLOW}Browser already open or opening, skipping auto-open${NC}"
fi

echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"

# Wait for user interrupt
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    # Kill API processes (including reloader)
    pkill -f "uvicorn.*api.main:app" 2>/dev/null
    # Kill frontend processes
    pkill -f "vite.*5173" 2>/dev/null
    pkill -f "npm.*run.*dev" 2>/dev/null
    # Kill any browser opening processes
    pkill -f "xdg-open.*localhost:5173" 2>/dev/null
    pkill -f "gnome-open.*localhost:5173" 2>/dev/null
    pkill -f "kde-open.*localhost:5173" 2>/dev/null
    # Clean up PID files and lock files
    rm -f /tmp/market-bot-api.pid /tmp/market-bot-frontend.pid "$LOCK_FILE" 2>/dev/null
    echo -e "${GREEN}Servers stopped${NC}"
    exit
}

trap cleanup INT TERM

wait
