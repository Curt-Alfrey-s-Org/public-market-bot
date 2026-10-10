#!/bin/bash
# Bot Health Monitor Script
# Usage: ./bot_monitor.sh [--continuous]
# Checks bot status, logs, and key metrics

# Configuration
BOT_DIR="${BOT_DIR:-$HOME/market-bot/market-pie5-bot}"
LOG_FILE="${BOT_DIR}/bot_phase1_run.log"
TRADE_HISTORY="${BOT_DIR}/trade_history.json"
CONTINUOUS=${1:-""}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_bot_status() {
    echo "=========================================="
    echo "BOT HEALTH CHECK - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=========================================="
    
    # Check if bot process is running
    BOT_PID=$(pgrep -f "python3.*main.py" || true)
    if [ -n "$BOT_PID" ]; then
        echo -e "${GREEN}✓ Bot Process: RUNNING${NC} (PID: ${BOT_PID})"
        
        # CPU and memory usage
        CPU=$(ps -p "$BOT_PID" -o %cpu= 2>/dev/null || echo "N/A")
        MEM=$(ps -p "$BOT_PID" -o %mem= 2>/dev/null || echo "N/A")
        echo "  CPU: ${CPU}% | Memory: ${MEM}%"
        
        # Uptime
        START_TIME=$(ps -p "$BOT_PID" -o lstart= 2>/dev/null || echo "Unknown")
        echo "  Started: ${START_TIME}"
    else
        echo -e "${RED}✗ Bot Process: NOT RUNNING${NC}"
        
        # Check for emergency stop marker
        if [ -f "${BOT_DIR}/.emergency_stop" ]; then
            echo -e "${YELLOW}⚠ Emergency stop marker found:${NC}"
            cat "${BOT_DIR}/.emergency_stop"
        fi
    fi
    
    echo ""
    
    # Check log file
    if [ -f "$LOG_FILE" ]; then
        echo "Log File Status:"
        LOG_SIZE=$(du -h "$LOG_FILE" | cut -f1)
        LOG_LINES=$(wc -l < "$LOG_FILE")
        LAST_MODIFIED=$(stat -c %y "$LOG_FILE" 2>/dev/null || stat -f "%Sm" "$LOG_FILE" 2>/dev/null)
        echo "  Size: ${LOG_SIZE} | Lines: ${LOG_LINES}"
        echo "  Last modified: ${LAST_MODIFIED}"
        
        # Check for recent activity (last 5 minutes)
        RECENT_ACTIVITY=$(find "$LOG_FILE" -mmin -5 2>/dev/null)
        if [ -n "$RECENT_ACTIVITY" ]; then
            echo -e "  ${GREEN}✓ Recent activity detected${NC}"
        else
            echo -e "  ${YELLOW}⚠ No activity in last 5 minutes${NC}"
        fi
        
        # Recent errors
        ERROR_COUNT=$(tail -1000 "$LOG_FILE" | grep -c "ERROR\|CRITICAL" || true)
        if [ "$ERROR_COUNT" -gt 0 ]; then
            echo -e "  ${RED}⚠ Recent errors: ${ERROR_COUNT}${NC}"
            echo "  Last 3 errors:"
            tail -1000 "$LOG_FILE" | grep "ERROR\|CRITICAL" | tail -3 | sed 's/^/    /'
        else
            echo -e "  ${GREEN}✓ No recent errors${NC}"
        fi
    else
        echo -e "${RED}✗ Log file not found: ${LOG_FILE}${NC}"
    fi
    
    echo ""
    
    # Check trade history
    if [ -f "$TRADE_HISTORY" ]; then
        TRADE_COUNT=$(jq '. | length' "$TRADE_HISTORY" 2>/dev/null || echo "0")
        echo "Trade History:"
        echo "  Total trades: ${TRADE_COUNT}"
        
        if [ "$TRADE_COUNT" -gt 0 ]; then
            LAST_TRADE=$(jq -r '.[-1] | "\(.timestamp) - \(.symbol) \(.action) @ \(.price)"' "$TRADE_HISTORY" 2>/dev/null)
            echo "  Last trade: ${LAST_TRADE}"
        fi
    fi
    
    echo ""
    
    # System resources
    echo "System Resources:"
    LOAD=$(uptime | awk -F'load average:' '{ print $2 }')
    echo "  Load average:${LOAD}"
    
    DISK_USAGE=$(df -h "$BOT_DIR" | tail -1 | awk '{print $5}')
    echo "  Disk usage: ${DISK_USAGE}"
    
    FREE_MEM=$(free -h | grep Mem | awk '{print $7}')
    echo "  Free memory: ${FREE_MEM}"
    
    echo "=========================================="
}

# Main execution
if [ "$CONTINUOUS" == "--continuous" ]; then
    echo "Starting continuous monitoring (Ctrl+C to stop)..."
    while true; do
        clear
        check_bot_status
        sleep 60
    done
else
    check_bot_status
fi
