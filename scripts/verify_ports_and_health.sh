#!/usr/bin/env bash
set -euo pipefail

BOT_NAME="Market Pie5 Bot"
# Use LAN host (or API_HOST) for checks when API is bound on 0.0.0.0; reserve 127.x for sensitive-only (e.g. OAuth).
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8002}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
DOCKER_FILTER="market-pie5-bot|market-bot"
FRONTEND_SRC="${FRONTEND_SRC:-$(pwd)/frontend/src}"

# Credentials come from the environment only (no built-in fallback passwords).
ADMIN_USER="${ADMIN_USERNAME:-}"
ADMIN_PASS="${ADMIN_PASSWORD:-}"
DIRECTOR_USER="${DIRECTOR_USERNAME:-}"
DIRECTOR_PASS="${DIRECTOR_PASSWORD:-}"

LOG_DIR="${LOG_DIR:-$(pwd)/logs}"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/selftest-ports-$(date +%Y%m%d_%H%M%S).log"

log() {
  echo "$@" | tee -a "$LOG_FILE"
}

check_http() {
  local label="$1"
  local url="$2"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)
  if [[ "$code" == "200" ]]; then
    log "[PASS] $label -> $url ($code)"
    return 0
  fi
  log "[FAIL] $label -> $url ($code)"
  return 1
}

login_check() {
  local label="$1"
  local user="$2"
  local pass="$3"
  if [[ -z "$user" || -z "$pass" ]]; then
    log "[SKIP] $label login -> set ${label^^}_USERNAME/${label^^}_PASSWORD in the environment to check"
    return 0
  fi
  local payload
  payload=$(printf '{"username":"%s","password":"%s"}' "$user" "$pass")
  local resp
  resp=$(curl -s -w "HTTP_STATUS:%{http_code}" -H "Content-Type: application/json" -d "$payload" "http://$API_HOST:$API_PORT/api/auth/login" || true)
  local status
  status=$(echo "$resp" | sed -n 's/.*HTTP_STATUS:\([0-9]*\)$/\1/p')
  if [[ "$status" != "200" ]]; then
    log "[FAIL] $label login -> status $status"
    return 1
  fi
  local token
  token=$(echo "$resp" | sed -n 's/.*"access_token": "change-me"]*\)".*/\1/p')
  if [[ -z "$token" ]]; then
    log "[FAIL] $label login -> token missing"
    return 1
  fi
  local me_status
  me_status=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $token" "http://$API_HOST:$API_PORT/api/auth/me" || true)
  if [[ "$me_status" == "200" ]]; then
    log "[PASS] $label login -> /api/auth/me ($me_status)"
    return 0
  fi
  log "[FAIL] $label login -> /api/auth/me ($me_status)"
  return 1
}

check_frontend_api_paths() {
  if [[ ! -d "$FRONTEND_SRC" ]]; then
    log "[SKIP] Frontend source not found at $FRONTEND_SRC"
    return 0
  fi
  local client_file="$FRONTEND_SRC/api/client.ts"
  if [[ ! -f "$client_file" ]]; then
    log "[WARN] client.ts not found at $client_file"
    return 0
  fi
  local base_has_api=0
  if grep -q "API_BASE_URL" "$client_file" && grep -q "/api" "$client_file"; then
    base_has_api=1
  fi
  local call_lines
  call_lines=$(grep -R -n -E "apiClient\.(get|post|put|delete|patch)\('\/" "$FRONTEND_SRC" || true)
  if [[ -z "$call_lines" ]]; then
    log "[WARN] No apiClient calls found"
    return 0
  fi
  if [[ "$base_has_api" == "1" ]]; then
    local bad
    bad=$(echo "$call_lines" | grep "/api/" || true)
    if [[ -n "$bad" ]]; then
      log "[FAIL] Frontend API paths include '/api/' but base already includes /api"
      log "$bad"
      return 1
    fi
    log "[PASS] Frontend API paths match base /api"
  else
    local bad
    bad=$(echo "$call_lines" | grep -v "/api/" || true)
    if [[ -n "$bad" ]]; then
      log "[FAIL] Frontend API paths missing '/api/' prefix"
      log "$bad"
      return 1
    fi
    log "[PASS] Frontend API paths include /api prefix"
  fi
}

log "=== $BOT_NAME Selftest ==="
log "API: http://$API_HOST:$API_PORT"
if [[ -n "$FRONTEND_PORT" ]]; then
  log "Frontend: http://$FRONTEND_HOST:$FRONTEND_PORT"
fi

log "--- Host ports in use ---"
ss -tulpn | grep -E "(:$API_PORT\b|:$FRONTEND_PORT\b)" | tee -a "$LOG_FILE" || true

log "--- Docker ports ---"
if command -v docker >/dev/null 2>&1; then
  docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "$DOCKER_FILTER" | tee -a "$LOG_FILE" || true
else
  log "[WARN] docker not available"
fi

log "--- HTTP checks ---"
check_http "API health" "http://$API_HOST:$API_PORT/api/health"
if [[ -n "$FRONTEND_PORT" ]]; then
  check_http "Frontend" "http://$FRONTEND_HOST:$FRONTEND_PORT/"
else
  log "[SKIP] Frontend check not configured"
fi

log "--- Auth checks ---"
login_check "Admin" "$ADMIN_USER" "$ADMIN_PASS"
login_check "Director" "$DIRECTOR_USER" "$DIRECTOR_PASS"

log "--- Frontend API path check ---"
check_frontend_api_paths

log "=== Selftest complete ==="
log "Log saved to $LOG_FILE"
