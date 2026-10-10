#!/bin/bash
# Emergency Stop Script for market-pie5-bot
# Usage: ./emergency_stop.sh [reason]
# This script immediately stops all bot processes and logs the action

set -e

# Configuration
BOT_DIR="${BOT_DIR:-$HOME/market-bot/market-pie5-bot}"
LOG_FILE="${BOT_DIR}/emergency_stops.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
REASON="${1:-Manual emergency stop}"

echo "=========================================="
echo "EMERGENCY STOP INITIATED"
echo "Time: ${TIMESTAMP}"
echo "Reason: ${REASON}"
echo "=========================================="

# Log the emergency stop
echo "[${TIMESTAMP}] EMERGENCY STOP: ${REASON}" >> "${LOG_FILE}"

# Find and kill all bot processes
echo "Finding bot processes..."
PIDS=$(pgrep -f "python3.*main.py" || true)

if [ -z "$PIDS" ]; then
    echo "✓ No bot processes found running"
    echo "[${TIMESTAMP}] No processes to kill" >> "${LOG_FILE}"
else
    echo "Found processes: ${PIDS}"
    echo "Stopping bot processes..."
    
    for PID in $PIDS; do
        echo "  Killing PID: ${PID}"
        kill -TERM "$PID" 2>/dev/null || true
        echo "[${TIMESTAMP}] Killed PID ${PID}" >> "${LOG_FILE}"
    done
    
    # Wait 5 seconds for graceful shutdown
    sleep 5
    
    # Force kill if still running
    REMAINING=$(pgrep -f "python3.*main.py" || true)
    if [ -n "$REMAINING" ]; then
        echo "Force killing remaining processes..."
        for PID in $REMAINING; do
            kill -9 "$PID" 2>/dev/null || true
            echo "[${TIMESTAMP}] Force killed PID ${PID}" >> "${LOG_FILE}"
        done
    fi
    
    echo "✓ All bot processes stopped"
fi

# Check final status
sleep 2
FINAL_CHECK=$(pgrep -f "python3.*main.py" || true)
if [ -z "$FINAL_CHECK" ]; then
    echo "✓ EMERGENCY STOP COMPLETE"
    echo "[${TIMESTAMP}] Emergency stop successful" >> "${LOG_FILE}"
    
    # Create emergency stop marker file
    touch "${BOT_DIR}/.emergency_stop"
    echo "${TIMESTAMP}: ${REASON}" > "${BOT_DIR}/.emergency_stop"
    
    exit 0
else
    echo "✗ ERROR: Some processes still running: ${FINAL_CHECK}"
    echo "[${TIMESTAMP}] ERROR: Failed to stop all processes" >> "${LOG_FILE}"
    exit 1
fi
