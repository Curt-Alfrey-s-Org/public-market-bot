#!/bin/bash
# Fix API Connection Issues
# Kills existing API processes and restarts properly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Fixing API Connection"
echo "=========================================="
echo ""

# Step 1: Kill existing API processes
echo "1. Stopping existing API processes..."
pkill -f "uvicorn api.main" 2>/dev/null && echo "   ✓ Stopped API" || echo "   ⚠ No API process found"
sleep 2

# Step 2: Check if port is free
echo ""
echo "2. Checking port 8000..."
if lsof -i :8000 > /dev/null 2>&1; then
    echo "   ✗ Port 8000 is still in use"
    echo "   Attempting to free port..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

if lsof -i :8000 > /dev/null 2>&1; then
    echo "   ✗ Port 8000 is still in use - manual intervention needed"
    exit 1
else
    echo "   ✓ Port 8000 is free"
fi

# Step 3: Start API
echo ""
echo "3. Starting API server..."
if [ ! -d "venv" ]; then
    echo "   ✗ Virtual environment not found"
    exit 1
fi

source venv/bin/activate

# Start API in background with proper logging
cd "$SCRIPT_DIR"
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/market-bot-api.log 2>&1 &
API_PID=$!
echo "   ✓ API started (PID: $API_PID)"

# Step 4: Wait for API to be ready
echo ""
echo "4. Waiting for API to be ready..."
API_READY=0
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "   ✓ API is ready!"
        API_READY=1
        break
    fi
    sleep 1
    echo -n "."
done
echo ""

if [ $API_READY -eq 0 ]; then
    echo "   ✗ API failed to start"
    echo ""
    echo "   Check logs: tail -f /tmp/market-bot-api.log"
    echo "   Check for permission errors or port conflicts"
    exit 1
fi

# Step 5: Test API endpoints
echo ""
echo "5. Testing API endpoints..."
if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    echo "   ✓ Health check passed"
else
    echo "   ✗ Health check failed"
fi

if curl -s http://localhost:8000/api/bot/status > /dev/null 2>&1; then
    echo "   ✓ Bot status endpoint accessible"
else
    echo "   ⚠ Bot status endpoint not accessible (bot may not be started)"
fi

echo ""
echo "=========================================="
echo "API is now running on http://localhost:8000"
echo "=========================================="
echo ""
echo "To view API logs: tail -f /tmp/market-bot-api.log"
echo "To stop API: pkill -f 'uvicorn api.main'"
echo ""
echo "Next steps:"
echo "  1. Start the bot from the web GUI (http://localhost:5173)"
echo "  2. Or use: curl -X POST http://localhost:8000/api/bot/start"
echo ""
