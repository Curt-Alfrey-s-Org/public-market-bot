#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-market-pie5-bot-api}"
TAIL_LINES="${TAIL_LINES:-200}"

DOCKER_CMD=()
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    DOCKER_CMD=(docker)
  fi
fi
if [[ ${#DOCKER_CMD[@]} -eq 0 ]] && command -v sudo >/dev/null 2>&1; then
  if sudo -n docker info >/dev/null 2>&1; then
    DOCKER_CMD=(sudo docker)
  fi
fi
if [[ ${#DOCKER_CMD[@]} -eq 0 ]]; then
  echo "Docker is not available. Start Docker or configure sudo access." >&2
  exit 2
fi

"${DOCKER_CMD[@]}" logs --timestamps --tail "$TAIL_LINES" -f "$CONTAINER_NAME"
