#!/usr/bin/env bash
# Build + start Market Pie5 Bot with hub-synced wheels.
# Mirrors the documented build (setup_dashboard.sh): host UID/GID export +
# `docker compose --env-file .env.compose-host-user --env-file .env up -d --build`,
# plus the hub hub wheel preflight (non-fatal) used across the bot repos.
#
# Usage (from anywhere):
#   ./scripts/build.sh            # build + start
#   ./scripts/build.sh --no-cache # extra args pass through to compose
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$APP_ROOT"

# hub hub: pull bot wheels into build-contexts before build (non-fatal).
ALFA_AI_ROOT="${ALFA_AI_ROOT:-$APP_ROOT/../alfa-ai}"
[ -f "$ALFA_AI_ROOT/scripts/sync-bot-wheels-preflight.sh" ] && \
  bash "$ALFA_AI_ROOT/scripts/sync-bot-wheels-preflight.sh" || true

# Host UID/GID for compose `user:` bind mounts (writes .env.compose-host-user).
# shellcheck disable=SC1091
. "$SCRIPT_DIR/export_compose_uid_gid.sh"
write_compose_host_user_env "$APP_ROOT"

DOCKER="docker"
docker info &>/dev/null 2>&1 || DOCKER="sudo docker"

ENV_ARGS=(--env-file "$APP_ROOT/.env.compose-host-user")
[ -f "$APP_ROOT/.env" ] && ENV_ARGS+=(--env-file "$APP_ROOT/.env")

exec $DOCKER compose "${ENV_ARGS[@]}" up -d --build "$@"
