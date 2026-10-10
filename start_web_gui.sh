#!/bin/bash
# Start Web GUI for market-pie5-bot
# Starts API backend (port 8001 default) and React frontend (port 5173)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   market-pie5-bot Web GUI Launcher                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    if [ ! -z "$API_PID" ]; then
        echo "Stopping API (PID: $API_PID)..."
        kill $API_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "Stopping Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}✓ Shutdown complete${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo "Run: bash master_setup.sh"
    exit 1
fi

# Check if frontend exists
if [ ! -d "frontend" ]; then
    echo -e "${RED}✗ Frontend directory not found${NC}"
    exit 1
fi

# Activate venv
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Start API backend
echo ""
API_PORT=${API_PORT:-8001}
echo -e "${BLUE}Starting API backend (port $API_PORT)...${NC}"
python3 -m uvicorn api.main:app --host 0.0.0.0 --port $API_PORT --reload > api.log 2>&1 &
API_PID=$!
echo -e "${GREEN}✓ API started (PID: $API_PID)${NC}"

# Wait for API to be ready
echo "Waiting for API to be ready..."
for i in {1..10}; do
    if curl -s http://localhost:${API_PORT:-8002}/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is ready${NC}"
        break
    fi
    sleep 1
done

# Start frontend
echo ""
echo -e "${BLUE}Starting React frontend (port 5173)...${NC}"
cd frontend
# Use 'npm run dev' (Vite's standard command, respects port in vite.config.ts)
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✓ market-pie5-bot Web GUI is running!                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}URLs:${NC}"
echo -e "  Frontend:  ${GREEN}http://localhost:5173${NC}"
echo -e "  API Docs:  ${GREEN}http://localhost:${API_PORT:-8002}/docs${NC}"
echo -e "  API Health: ${GREEN}http://localhost:${API_PORT:-8002}/api/health${NC}"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  API:      tail -f api.log"
echo -e "  Frontend: tail -f frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both services${NC}"
echo ""

# Wait for processes
wait