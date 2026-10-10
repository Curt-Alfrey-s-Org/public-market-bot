#!/usr/bin/env bash
# Market Bot Docker cleanup: remove unused images/containers/volumes for this project.
# Run: ./scripts/docker_cleanup.sh   (uses sudo for docker if needed)
# Build cache / disk headroom: ./scripts/cleanup_docker_disk.sh (df + docker builder prune; shared across bots).

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

DOCKER="${DOCKER:-docker}"
if ! $DOCKER info &>/dev/null; then
  DOCKER="sudo docker"
fi

echo "=== Market Bot Docker cleanup ==="

for name in market-pie5-bot-api ansible_market-bot-api_1; do
  if $DOCKER ps -a -q -f "name=^${name}$" 2>/dev/null | grep -q .; then
    echo "Stopping/removing: $name"
    $DOCKER stop "$name" 2>/dev/null || true
    $DOCKER rm "$name" 2>/dev/null || true
  fi
done

echo "Removing dangling images..."
$DOCKER image prune -f 2>/dev/null || true
echo "Removing unused volumes..."
$DOCKER volume prune -f 2>/dev/null || true

echo "[OK] Docker cleanup done."
