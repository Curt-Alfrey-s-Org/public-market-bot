#!/bin/bash
# Probe and test Market Bot API in all modes
# Usage: ./probe_all_modes.sh [API_URL]
# Default API: http://127.0.0.1:8002
#
# Authentication (required): /api/* needs a JWT and the control endpoints
# (bot start/stop/mode) need an ADMIN JWT. Provide one of:
#   MARKET_BOT_ADMIN_TOKEN=<admin JWT>             (preferred), or
#   MARKET_BOT_ADMIN_USERNAME / MARKET_BOT_ADMIN_PASSWORD (the script logs in once).
# The token is passed to curl through a config on a file descriptor, never on the
# command line, and is never written to the log.

API_URL="${1:-http://127.0.0.1:8002}"
API_URL="${API_URL%/}"
OUT="/tmp/market_bot_probe_$(date +%Y%m%d_%H%M%S).txt"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT"; }

AUTH_TOKEN="change-me"
if [[ -z "$AUTH_TOKEN" ]]; then
  if [[ -z "${MARKET_BOT_ADMIN_USERNAME:-}" || -z "${MARKET_BOT_ADMIN_PASSWORD:-}" ]]; then
    echo "ERROR: set MARKET_BOT_ADMIN_TOKEN, or MARKET_BOT_ADMIN_USERNAME and MARKET_BOT_ADMIN_PASSWORD (admin account)." >&2
    exit 2
  fi
  login_body=$(python3 -c 'import json,os; print(json.dumps({"username": os.environ["MARKET_BOT_ADMIN_USERNAME"], "password": os.environ["MARKET_BOT_ADMIN_PASSWORD"]}))')
  AUTH_TOKEN=$(curl -s -m 15 -X POST "$API_URL/api/auth/login" -H "Content-Type: application/json" --data-binary @- <<<"$login_body" \
    | python3 -c 'import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
print(d.get("token") or d.get("access_token") or "")' 2>/dev/null)
  unset login_body
  if [[ -z "$AUTH_TOKEN" ]]; then
    echo "ERROR: admin login failed at $API_URL/api/auth/login" >&2
    exit 2
  fi
fi

# curl with the admin Bearer token (read from a process-substitution config, so it
# does not appear in the process list).
acurl() {
  curl -K <(printf 'header = "Authorization: Bearer %s"\n' "$AUTH_TOKEN") "$@"
}
run() {
  local name="$1"
  local cmd="$2"
  log "=== $name ==="
  if eval "$cmd" 2>&1 | tee -a "$OUT"; then
    log "OK: $name"
    return 0
  else
    log "FAIL: $name"
    return 1
  fi
}

log "Market Bot Probe — API: $API_URL"
log ""

# 1. Probe GET endpoints
log "=== 1. PROBE GET ENDPOINTS ==="
for path in /api/health /api/bot/status /api/stats /api/trades /api/messages /api/settings \
  /api/logs /api/reports/decisions /api/pending-trades /api/system /api/system/health; do
  code=$(acurl -s -o /dev/null -w "%{http_code}" "$API_URL$path" 2>/dev/null)
  log "GET $path -> $code"
  if [ "$code" != "200" ]; then
    acurl -s "$API_URL$path" 2>/dev/null | head -3 >> "$OUT"
  fi
done

# 2. Bot mode cycle: stop -> yfinance -> sandbox -> dryrun-live (stop between)
log ""
log "=== 2. BOT MODE CYCLE ==="

stop_bot() {
  acurl -s -X POST "$API_URL/api/bot/stop" -H "Content-Type: application/json"
  sleep 3
}

start_mode() {
  local mode="$1"
  log "Starting mode: $mode"
  out=$(acurl -s -X POST "$API_URL/api/bot/start" -H "Content-Type: application/json" -d "{\"mode\": \"$mode\"}")
  echo "$out" >> "$OUT"
  echo "$out"
}

# Stop first
stop_bot

# yfinance
start_mode "yfinance"
sleep 5
status=$(acurl -s "$API_URL/api/bot/status")
log "Status after yfinance start: $status"
stop_bot

# sandbox (Schwab off = may fallback to yfinance behavior)
start_mode "sandbox"
sleep 5
status=$(acurl -s "$API_URL/api/bot/status")
log "Status after sandbox start: $status"
stop_bot

# dryrun-live (Schwab required, may error)
start_mode "dryrun-live"
sleep 5
status=$(acurl -s "$API_URL/api/bot/status")
log "Status after dryrun-live start: $status"

# Restore yfinance for continued operation
stop_bot
start_mode "yfinance"
log "Restored yfinance mode"

# 3. POST endpoints (non-destructive)
log ""
log "=== 3. POST ENDPOINTS (read-only/safe) ==="
# Mode change (no restart)
acurl -s -X POST "$API_URL/api/bot/mode" -H "Content-Type: application/json" -d '{"mode":"yfinance"}' >> "$OUT"
log "POST /api/bot/mode -> done"

# System run-tests (requires bot stopped; uses API_URL from env)
log "Skipping POST /api/system/run-tests (run manually with bot stopped, API_URL=$API_URL)"

log ""
log "Probe complete. Full log: $OUT"
