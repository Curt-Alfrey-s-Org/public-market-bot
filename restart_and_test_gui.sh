#!/bin/bash
# Restart GUI services and run integration tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================================"
echo "GUI Restart and Test Script"
echo "============================================================${NC}\n"

# Step 1: Kill existing processes
echo -e "${YELLOW}Step 1: Stopping existing services...${NC}"
pkill -f "uvicorn api.main" 2>/dev/null && echo -e "${GREEN}✓ Stopped API${NC}" || echo -e "${YELLOW}⚠ No API process found${NC}"
pkill -f "vite" 2>/dev/null && echo -e "${GREEN}✓ Stopped Frontend${NC}" || echo -e "${YELLOW}⚠ No Frontend process found${NC}"
sleep 2

# Step 2: Verify ports are free
echo -e "\n${YELLOW}Step 2: Verifying ports are free...${NC}"
if lsof -i :8000 > /dev/null 2>&1; then
    echo -e "${RED}✗ Port 8000 is still in use${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Port 8000 is free${NC}"
fi

if lsof -i :5173 > /dev/null 2>&1; then
    echo -e "${RED}✗ Port 5173 is still in use${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Port 5173 is free${NC}"
fi

# Step 3: Start API
echo -e "\n${YELLOW}Step 3: Starting API server...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    exit 1
fi

source venv/bin/activate

# Start API in background
cd "$SCRIPT_DIR"
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/market-bot-api.log 2>&1 &
API_PID=$!
echo -e "${GREEN}✓ API started (PID: $API_PID)${NC}"

# Wait for API to be ready
echo -e "${YELLOW}Waiting for API to be ready...${NC}"
API_READY=0
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is ready!${NC}"
        API_READY=1
        break
    fi
    sleep 1
    echo -n "."
done
echo ""

if [ $API_READY -eq 0 ]; then
    echo -e "${RED}✗ API failed to start${NC}"
    echo -e "${YELLOW}Check logs: tail -f /tmp/market-bot-api.log${NC}"
    exit 1
fi

# Step 4: Start Frontend
echo -e "\n${YELLOW}Step 4: Starting Frontend server...${NC}"
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    cd frontend
    npm install
    cd "$SCRIPT_DIR"
fi

cd frontend
nohup npm run dev > /tmp/market-bot-frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"

# Wait for frontend to be ready
echo -e "${YELLOW}Waiting for Frontend to be ready...${NC}"
FRONTEND_READY=0
for i in {1..30}; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is ready!${NC}"
        FRONTEND_READY=1
        break
    fi
    sleep 1
    echo -n "."
done
echo ""

if [ $FRONTEND_READY -eq 0 ]; then
    echo -e "${RED}✗ Frontend failed to start${NC}"
    echo -e "${YELLOW}Check logs: tail -f /tmp/market-bot-frontend.log${NC}"
    exit 1
fi

# Step 5: Run Integration Tests
echo -e "\n${YELLOW}Step 5: Running Integration Tests...${NC}"
cd "$SCRIPT_DIR"

echo -e "\n${BLUE}--- API Integration Tests ---${NC}"
python3 test_api_integration.py

echo -e "\n${BLUE}--- Frontend Integration Tests ---${NC}"
bash test_frontend_integration.sh

# Step 6: Summary
echo -e "\n${BLUE}============================================================"
echo "Summary"
echo "============================================================${NC}"
echo -e "${GREEN}✓ API running on http://localhost:8000 (PID: $API_PID)${NC}"
echo -e "${GREEN}✓ Frontend running on http://localhost:5173 (PID: $FRONTEND_PID)${NC}"
echo -e "\n${YELLOW}To view logs:${NC}"
echo "  API: tail -f /tmp/market-bot-api.log"
echo "  Frontend: tail -f /tmp/market-bot-frontend.log"
echo -e "\n${YELLOW}To stop services:${NC}"
echo "  pkill -f 'uvicorn api.main'"
echo "  pkill -f 'vite'"
echo ""
