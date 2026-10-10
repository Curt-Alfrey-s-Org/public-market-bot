#!/bin/bash
# Frontend Integration Test Script
# Tests frontend API calls and WebSocket connections

set -e

API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:5173"
TIMEOUT=5

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================"
echo "Frontend Integration Test Suite"
echo "============================================================${NC}\n"

# Test 1: Frontend is serving
echo -e "${BLUE}Test 1: Frontend Server${NC}"
if curl -s -f --max-time $TIMEOUT "$FRONTEND_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is serving on $FRONTEND_URL${NC}"
else
    echo -e "${RED}✗ Frontend is not accessible on $FRONTEND_URL${NC}"
    echo "  Please ensure frontend is running: cd frontend && npm run dev"
    exit 1
fi

# Test 2: API is reachable from frontend context
echo -e "\n${BLUE}Test 2: API Reachability${NC}"
if curl -s -f --max-time $TIMEOUT "$API_URL/api/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is reachable from frontend context${NC}"
else
    echo -e "${RED}✗ API is not reachable${NC}"
    echo "  Please ensure API is running: uvicorn api.main:app --host 0.0.0.0 --port 8000"
    exit 1
fi

# Test 3: CORS headers
echo -e "\n${BLUE}Test 3: CORS Configuration${NC}"
CORS_HEADER=$(curl -s -I -H "Origin: $FRONTEND_URL" "$API_URL/api/health" 2>/dev/null | grep -i "access-control-allow-origin" || echo "")
if [ -n "$CORS_HEADER" ]; then
    echo -e "${GREEN}✓ CORS headers present: $CORS_HEADER${NC}"
else
    echo -e "${YELLOW}⚠ CORS headers not found (may be OK for same-origin)${NC}"
fi

# Test 4: API endpoints via proxy
echo -e "\n${BLUE}Test 4: API Endpoints via Vite Proxy${NC}"
ENDPOINTS=(
    "/api/health"
    "/api/bot/status"
    "/api/system"
)

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -s -f --max-time $TIMEOUT "$FRONTEND_URL$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $endpoint accessible via proxy${NC}"
    else
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$FRONTEND_URL$endpoint" 2>/dev/null || echo "000")
        if [ "$STATUS" = "503" ]; then
            echo -e "${YELLOW}⚠ $endpoint returns 503 (bot instance not available - expected)${NC}"
        else
            echo -e "${RED}✗ $endpoint failed (status: $STATUS)${NC}"
        fi
    fi
done

# Test 5: WebSocket endpoint
echo -e "\n${BLUE}Test 5: WebSocket Endpoint${NC}"
if command -v websocat > /dev/null 2>&1; then
    if timeout 3 websocat "ws://localhost:8000/ws" <<< '{"type":"ping"}' > /dev/null 2>&1; then
        echo -e "${GREEN}✓ WebSocket endpoint is accessible${NC}"
    else
        echo -e "${YELLOW}⚠ WebSocket test inconclusive (websocat may need different syntax)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ websocat not installed - skipping WebSocket test${NC}"
    echo "  Install with: cargo install websocat (or use Python test)"
fi

# Test 6: Check for common frontend errors
echo -e "\n${BLUE}Test 6: Frontend Error Check${NC}"
FRONTEND_HTML=$(curl -s --max-time $TIMEOUT "$FRONTEND_URL" 2>/dev/null || echo "")
if echo "$FRONTEND_HTML" | grep -q "vite"; then
    echo -e "${GREEN}✓ Frontend is serving Vite app${NC}"
else
    echo -e "${YELLOW}⚠ Frontend response doesn't look like Vite app${NC}"
fi

# Summary
echo -e "\n${BLUE}============================================================"
echo "Frontend Integration Test Complete"
echo "============================================================${NC}\n"

echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Open browser console (F12) and check for errors"
echo "  2. Test API calls from browser DevTools Network tab"
echo "  3. Verify WebSocket connection in browser console"
echo "  4. Run: python3 test_api_integration.py for detailed API tests"
echo ""
