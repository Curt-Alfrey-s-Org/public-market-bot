#!/bin/bash
# Master startup script for Market Pie5 Bot (both trading bot and API server)
# Runs the trading bot in the foreground and API server in the background

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

# Check requirements
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found"
    exit 1
fi

if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "❌ .env file not found - copy from .env.example"
    exit 1
fi

echo "=========================================="
echo "Market Pie5 Bot - Full Startup"
echo "=========================================="
echo ""

# Kill any existing API servers
echo "🛑 Cleaning up old processes..."
pkill -f "uvicorn api.main" || true
sleep 1

# Start API server in background
echo "🚀 Starting API server on port 8000..."
cd "$PROJECT_DIR"
$VENV_DIR/bin/python3 -m uvicorn api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info \
    > api_server.log 2>&1 &

API_PID=$!
echo "   ✓ API PID: $API_PID"
sleep 2

# Verify API is running
if ! kill -0 $API_PID 2>/dev/null; then
    echo "❌ API server failed to start"
    cat api_server.log
    exit 1
fi

echo "   ✓ API is running"
echo ""

# Start trading bot in foreground
echo "🤖 Starting trading bot..."
echo "   📊 Dashboard: http://localhost:8000/"
echo "   📚 API Docs: http://localhost:8000/docs"
echo ""

trap "echo ''; echo 'Shutting down...'; kill $API_PID 2>/dev/null || true" EXIT

$VENV_DIR/bin/python3 main.py
