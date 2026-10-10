#!/bin/bash
# Diagnostic script for API connection issues

echo "=== API Connection Diagnostics ==="
echo ""

# Check if API process is running
echo "1. Checking API process..."
API_PID=$(pgrep -f "uvicorn.*api.main:app" | head -1)
if [ -z "$API_PID" ]; then
    echo "   ❌ API process NOT running"
    exit 1
else
    echo "   ✅ API process running (PID: $API_PID)"
fi

# Check port binding
echo ""
echo "2. Checking port 8000 binding..."
if command -v ss &> /dev/null; then
    PORT_CHECK=$(ss -tlnp 2>/dev/null | grep ":8000" || echo "")
elif command -v netstat &> /dev/null; then
    PORT_CHECK=$(netstat -tlnp 2>/dev/null | grep ":8000" || echo "")
else
    PORT_CHECK=""
fi

if [ -z "$PORT_CHECK" ]; then
    echo "   ❌ Port 8000 NOT bound"
    echo "   This means the API process exists but isn't listening"
else
    echo "   ✅ Port 8000 is bound:"
    echo "   $PORT_CHECK"
fi

# Test API endpoints
echo ""
echo "3. Testing API endpoints..."
HEALTH_RESPONSE=$(curl -s --connect-timeout 2 --max-time 3 http://localhost:8000/api/health 2>&1)
if [ $? -eq 0 ] && echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "   ✅ /api/health responding"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "   ❌ /api/health NOT responding"
    echo "   Error: $HEALTH_RESPONSE"
fi

STATUS_RESPONSE=$(curl -s --connect-timeout 2 --max-time 3 http://localhost:8000/api/bot/status 2>&1)
if [ $? -eq 0 ]; then
    echo "   ✅ /api/bot/status responding"
else
    echo "   ❌ /api/bot/status NOT responding"
    echo "   Error: $STATUS_RESPONSE"
fi

# Check API logs
echo ""
echo "4. Recent API errors (last 20 lines)..."
if [ -f "trading_bot.log" ]; then
    tail -20 trading_bot.log | grep -i "error\|exception\|failed\|traceback" | tail -5 || echo "   No recent errors in log"
else
    echo "   ⚠️  trading_bot.log not found"
fi

# Check process details
echo ""
echo "5. API process details..."
ps aux | grep "$API_PID" | grep -v grep || echo "   Process not found"

# Recommendations
echo ""
echo "=== Recommendations ==="
if [ -z "$PORT_CHECK" ]; then
    echo "1. API process is running but not listening on port 8000"
    echo "   → Try restarting the API: pkill -f uvicorn && ./start_api.sh"
    echo "   → Check for port conflicts: sudo lsof -i :8000"
    echo "   → Check API startup logs for errors"
fi

if [ -z "$HEALTH_RESPONSE" ] || ! echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "2. API is not responding to health checks"
    echo "   → Check firewall: sudo ufw status"
    echo "   → Check if API is binding to correct interface (0.0.0.0 vs 127.0.0.1)"
    echo "   → Check API logs for startup errors"
fi

echo ""
echo "=== End Diagnostics ==="
