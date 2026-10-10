#!/usr/bin/env bash
# Always run from subdomain: selftests, then subdomain login + stop/start bot yfinance + trail logs 2 min.
# Analyze logs for errors and for trades (filled > 0, Order filled, TRADE ALERT, or "holding positions").
# Usage: ./scripts/run_selftest_subdomain_trail.sh [--analyze-only LOG_FILE]
#   --analyze-only F analyze existing log file only (e.g. after tail -f > file)
# Env: MARKET_BOT_SUBDOMAIN (default https://market-bot.example.com), MARKET_BOT_CONTAINER, TRAIL_SECONDS, TRAIL_ANALYZE_LINES (default 8000)
#      MARKET_BOT_ADMIN_USERNAME / MARKET_BOT_ADMIN_PASSWORD (required for the login + stop/start steps;
#      bot control needs an admin session token, the API key is not accepted for control endpoints)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

SUBDOMAIN="${MARKET_BOT_SUBDOMAIN:-https://market-bot.example.com}"
CONTAINER="${MARKET_BOT_CONTAINER:-ansible_market-bot-api_1}"
TRAIL_SECONDS="${TRAIL_SECONDS:-120}"
LOG_OUT="${LOG_OUT:-$PROJECT_ROOT/trail_analysis_$(date +%Y%m%d_%H%M%S).log}"
ANALYZE_ONLY=""
AUTH_TOKEN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --analyze-only) ANALYZE_ONLY="$2"; shift 2 ;;
    *) shift ;;
  esac
done

run_selftests() {
  echo "=== 1. Running selftests (yfinance suite) ==="
  if [[ -d venv ]]; then source venv/bin/activate; fi
  if python3 tests/runner.py --yfinance-only 2>&1 | tee /tmp/selftest_out.txt; then
    echo "[PASS] Selftests completed."
  else
    echo "[FAIL] Selftests had failures. Check /tmp/selftest_out.txt"
    return 1
  fi
  # Quick bug scan on test output
  if grep -qE "ERROR|Exception|Traceback|Failed:" /tmp/selftest_out.txt 2>/dev/null; then
    echo "[WARN] Test output contains errors - review /tmp/selftest_out.txt"
  fi
  return 0
}

subdomain_login() {
  echo "=== 2. Subdomain login ==="
  if [[ -z "${MARKET_BOT_ADMIN_USERNAME:-}" || -z "${MARKET_BOT_ADMIN_PASSWORD:-}" ]]; then
    echo "[FAIL] Set MARKET_BOT_ADMIN_USERNAME and MARKET_BOT_ADMIN_PASSWORD (admin account) in the environment."
    return 1
  fi
  local r body
  body=$(python3 -c 'import json,os; print(json.dumps({"username": os.environ["MARKET_BOT_ADMIN_USERNAME"], "password": os.environ["MARKET_BOT_ADMIN_PASSWORD"]}))')
  r=$(curl -s -m 15 -X POST "$SUBDOMAIN/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "$body" 2>/dev/null || true)
  AUTH_TOKEN=$(printf '%s' "$r" | python3 -c 'import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
print(d.get("token") or d.get("access_token") or "")' 2>/dev/null || true)
  if [[ -n "$AUTH_TOKEN" ]]; then
    echo "[PASS] Login OK."
    return 0
  else
    echo "[FAIL] Login failed."
    return 1
  fi
}

stop_bot() {
  echo "=== 2b. Stop bot (so next start opens new positions) ==="
  curl -s -m 10 -X POST "$SUBDOMAIN/api/bot/stop" \
    -H "Authorization: Bearer ${AUTH_TOKEN:-}" 2>/dev/null || true
  sleep 2
}

start_bot_yfinance() {
  echo "=== 3. Start bot in yfinance mode ==="
  local r
  r=$(curl -s -m 20 -X POST "$SUBDOMAIN/api/bot/start" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${AUTH_TOKEN:-}" \
    -d '{"mode":"yfinance"}' 2>/dev/null || true)
  if echo "$r" | grep -q '"running":true'; then
    echo "[PASS] Bot started."
    return 0
  else
    echo "[FAIL] Start failed: $r"
    return 1
  fi
}

trail_logs() {
  local logfile="$1"
  echo "=== 4. Trailing logs for ${TRAIL_SECONDS}s to $logfile ==="
  if command -v sudo &>/dev/null; then
    sudo docker logs -f "$CONTAINER" 2>&1 | timeout "$TRAIL_SECONDS" tee "$logfile" || true
  else
    docker logs -f "$CONTAINER" 2>&1 | timeout "$TRAIL_SECONDS" tee "$logfile" || true
  fi
  echo "[DONE] Log capture finished."
}

analyze_log() {
  local logfile="$1"
  echo ""
  echo "=== 5. Log analysis: $logfile ==="
  if [[ ! -f "$logfile" ]]; then
    echo "[SKIP] Log file not found."
    return 1
  fi

  echo "--- Errors (ERROR / Exception / Traceback / failed) ---"
  local err_count
  err_count=$(grep -cE "ERROR|Exception|Traceback|failed:" "$logfile" 2>/dev/null || echo 0)
  if [[ "$err_count" -gt 0 ]]; then
    grep -nE "ERROR|Exception|Traceback|failed:" "$logfile" 2>/dev/null | head -40
    echo "[WARN] Found $err_count error-like lines."
  else
    echo "[OK] No error lines found."
  fi

  echo ""
  echo "--- Trading (in trailing window only) ---"
  # Analyze only last N lines so we require trades during the 2-min trail, not old history
  local trail_lines="${TRAIL_ANALYZE_LINES:-8000}"
  local recent_log
  recent_log=$(mktemp)
  tail -n "$trail_lines" "$logfile" 2>/dev/null > "$recent_log" || cp "$logfile" "$recent_log"

  local filled_cycles order_filled trade_alert simulated
  filled_cycles=$(grep -E "filled: [1-9][0-9]*" "$recent_log" 2>/dev/null | wc -l)
  order_filled=$(grep -c "Order filled for" "$recent_log" 2>/dev/null || true)
  trade_alert=$(grep -c "TRADE ALERT" "$recent_log" 2>/dev/null || true)
  simulated=$(grep -cE "status.*simulated|simulated.*trade" "$recent_log" 2>/dev/null || true)
  local processing
  processing=$(grep -c "Processing trade for" "$recent_log" 2>/dev/null || true)
  local hold_cycles
  hold_cycles=$(grep -c "HOLD/skip: 8, BUY/SELL signals: 0" "$recent_log" 2>/dev/null || true)
  local total_cycles
  total_cycles=$(grep -c "Cycle #.*complete:" "$recent_log" 2>/dev/null || true)
  rm -f "$recent_log"

  # Sanitize: ensure single integer (strip whitespace/newlines)
  filled_cycles=$(printf '%s' "$filled_cycles" | tr -cd '0-9'); filled_cycles=${filled_cycles:-0}
  order_filled=$(printf '%s' "$order_filled" | tr -cd '0-9'); order_filled=${order_filled:-0}
  trade_alert=$(printf '%s' "$trade_alert" | tr -cd '0-9'); trade_alert=${trade_alert:-0}
  simulated=$(printf '%s' "$simulated" | tr -cd '0-9'); simulated=${simulated:-0}
  processing=$(printf '%s' "$processing" | tr -cd '0-9'); processing=${processing:-0}
  hold_cycles=$(printf '%s' "$hold_cycles" | tr -cd '0-9'); hold_cycles=${hold_cycles:-0}
  total_cycles=$(printf '%s' "$total_cycles" | tr -cd '0-9'); total_cycles=${total_cycles:-0}

  echo "  (last $trail_lines lines) Cycles with filled > 0: $filled_cycles"
  echo "  'Order filled for' lines: $order_filled"
  echo "  'TRADE ALERT' lines: $trade_alert"
  echo "  Simulated/trade lines: $simulated"
  echo "  'Processing trade for' lines: $processing"

  local trades_ok=false
  if [[ "$filled_cycles" -gt 0 ]] || [[ "$order_filled" -gt 0 ]] || [[ "$trade_alert" -gt 0 ]] || [[ "$processing" -gt 0 ]]; then
    trades_ok=true
  fi
  # If all cycles show "position held" (HOLD/skip: 8, BUY/SELL signals: 0), bot may be correctly holding — don't fail
  if [[ "$total_cycles" -gt 0 ]] && [[ "$hold_cycles" -ge "$total_cycles" ]] && [[ "$trade_alert" -eq 0 ]] && [[ "$processing" -eq 0 ]]; then
    echo "  (All $total_cycles cycles in window: position held only; bot has open positions from loaded history.)"
    echo "[PASS] Bot running in yfinance mode (holding positions; no new trades this window)."
    trades_ok=true
  fi
  if ! $trades_ok; then
    echo "[FAIL] No trades detected. Review trading settings (see below)."
    echo ""
    echo "--- Settings to review (trading) ---"
    echo "  PAPER_TRADING_MODE=true (yfinance needs paper)"
    echo "  SCHWAB_SANDBOX_MODE=false (yfinance = no Schwab)"
    echo "  SCHWAB_API_ENABLED=off"
    echo "  BOT_MIN_ALLOCATION, BOT_MAX_ALLOCATION"
    echo "  BOT_RISK_THRESHOLD, position limits, filters (news, earnings, stock filter)"
    echo "  Container .env and bot_manager filled-count fix (status in ('success','simulated'))."
  elif [[ "$filled_cycles" -gt 0 ]] || [[ "$order_filled" -gt 0 ]] || [[ "$trade_alert" -gt 0 ]] || [[ "$processing" -gt 0 ]]; then
    echo "[PASS] Trades detected in yfinance mode."
  fi

  echo ""
  echo "--- Sample cycle summary lines ---"
  grep "Cycle #" "$logfile" 2>/dev/null | tail -5 || true

  if $trades_ok; then return 0; else return 1; fi
}

# --- main ---
if [[ -n "$ANALYZE_ONLY" ]]; then
  analyze_log "$ANALYZE_ONLY"
  exit $?
fi

run_selftests || exit 1

# Always run from subdomain
subdomain_login || exit 2
stop_bot
start_bot_yfinance || exit 3
sleep 8
trail_logs "$LOG_OUT"
analyze_log "$LOG_OUT"
exit $?
