#!/bin/bash
# Run Self-Test and Analyze Logs
# Automates the workflow from the run-selftest-after-changes rule

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================"
echo "Self-Test and Log Analysis"
echo "============================================================${NC}\n"

# Step 1: Check if API is running
echo -e "${YELLOW}Step 1: Checking API status...${NC}"
if curl -s http://localhost:8002/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is running${NC}"
else
    echo -e "${RED}✗ API is not running${NC}"
    echo -e "${YELLOW}Starting API...${NC}"
    ./fix_api_connection.sh || {
        echo -e "${RED}Failed to start API. Please start manually: ./start_api.sh${NC}"
        exit 1
    }
fi

# Step 2: Run self-test suite
echo -e "\n${YELLOW}Step 2: Running self-test suite...${NC}"
REPORT_FILE="test_report_$(date +%Y%m%d_%H%M%S).json"

if python3 tests/runner.py --api-url http://localhost:8002 --output "$REPORT_FILE"; then
    echo -e "${GREEN}✓ Tests completed${NC}"
else
    echo -e "${RED}✗ Tests failed or encountered errors${NC}"
    TEST_EXIT_CODE=$?
fi

# Step 3: Analyze test report
echo -e "\n${YELLOW}Step 3: Analyzing test results...${NC}"
if [ -f "$REPORT_FILE" ]; then
    if command -v jq > /dev/null 2>&1; then
        TOTAL=$(jq -r '.summary.total' "$REPORT_FILE")
        PASSED=$(jq -r '.summary.passed' "$REPORT_FILE")
        FAILED=$(jq -r '.summary.failed' "$REPORT_FILE")
        WARNINGS=$(jq -r '.summary.warnings' "$REPORT_FILE")
        SUCCESS_RATE=$(jq -r '.summary.success_rate' "$REPORT_FILE")
        
        echo -e "  Total Tests: ${TOTAL}"
        echo -e "  Passed: ${GREEN}${PASSED}${NC}"
        echo -e "  Failed: ${RED}${FAILED}${NC}"
        echo -e "  Warnings: ${YELLOW}${WARNINGS}${NC}"
        echo -e "  Success Rate: ${SUCCESS_RATE}%"
        
        if [ "$FAILED" -gt 0 ]; then
            echo -e "\n${RED}Failed Tests:${NC}"
            jq -r '.results[] | select(.status == "FAIL") | "  ✗ \(.name): \(.message)"' "$REPORT_FILE"
        fi
        
        if [ "$WARNINGS" -gt 0 ]; then
            echo -e "\n${YELLOW}Warnings:${NC}"
            jq -r '.results[] | select(.status == "WARN") | "  ⚠ \(.name): \(.message)"' "$REPORT_FILE"
        fi
    else
        echo -e "${YELLOW}⚠ jq not installed - showing raw summary${NC}"
        grep -A 10 '"summary"' "$REPORT_FILE" | head -15
    fi
else
    echo -e "${RED}✗ Test report not found${NC}"
fi

# Step 4: Analyze API logs
echo -e "\n${YELLOW}Step 4: Analyzing API logs...${NC}"
if [ -f "/tmp/market-bot-api.log" ]; then
    ERROR_COUNT=$(grep -i "error\|exception\|traceback" /tmp/market-bot-api.log | tail -20 | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo -e "${RED}✗ Found ${ERROR_COUNT} recent errors in API logs${NC}"
        echo -e "${YELLOW}Recent errors:${NC}"
        grep -i "error\|exception\|traceback" /tmp/market-bot-api.log | tail -5
    else
        echo -e "${GREEN}✓ No recent errors in API logs${NC}"
    fi
else
    echo -e "${YELLOW}⚠ API log file not found at /tmp/market-bot-api.log${NC}"
fi

# Step 5: Analyze bot logs
echo -e "\n${YELLOW}Step 5: Analyzing bot logs...${NC}"
if [ -f "trading_bot.log" ]; then
    ERROR_COUNT=$(grep -E "(ERROR|CRITICAL|WARNING)" trading_bot.log | tail -50 | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo -e "${YELLOW}Found ${ERROR_COUNT} recent errors/warnings in bot logs${NC}"
        echo -e "${YELLOW}Recent critical issues:${NC}"
        grep -E "(ERROR|CRITICAL)" trading_bot.log | tail -5
    else
        echo -e "${GREEN}✓ No recent errors in bot logs${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Bot log file not found at trading_bot.log${NC}"
fi

# Step 6: Summary
echo -e "\n${BLUE}============================================================"
echo "Summary"
echo "============================================================${NC}"

if [ -f "$REPORT_FILE" ] && command -v jq > /dev/null 2>&1; then
    FAILED=$(jq -r '.summary.failed' "$REPORT_FILE")
    if [ "$FAILED" -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
        echo -e "  Report: ${REPORT_FILE}"
    else
        echo -e "${RED}✗ ${FAILED} test(s) failed${NC}"
        echo -e "  Report: ${REPORT_FILE}"
        echo -e "  Review failed tests above and check logs"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ Could not determine test status${NC}"
    echo -e "  Report: ${REPORT_FILE}"
fi

echo -e "\n${YELLOW}Next steps:${NC}"
echo "  1. Review test report: cat $REPORT_FILE | jq"
echo "  2. Check API logs: tail -f /tmp/market-bot-api.log"
echo "  3. Check bot logs: tail -f trading_bot.log"
echo "  4. Fix any failures and re-run tests"
echo ""
