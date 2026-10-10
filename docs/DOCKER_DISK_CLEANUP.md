# Docker and disk cleanup

This repository includes **`scripts/cleanup_docker_disk.sh`** to reclaim space when the root filesystem fills up. A full disk commonly causes **`docker compose build`** failures, database errors, and shell messages like **“No space left on device”**.

## What the script does

1. Prints **`df -h /`** so you can see usage at a glance.
2. Emits a **WARNING** when **`/`** is **≥90%** used **or** **≤2 GiB** free.
3. If the Docker CLI is available **and** the daemon is reachable (uses **`sudo docker`** only if needed), it prunes **BuildKit build cache**:
   - **Default:** `docker builder prune -f`
   - **Aggressive:** `docker builder prune -af`
4. Optionally prunes **dangling images** or, with explicit safeguards, **all unused images**.

If Docker is missing or the daemon is not running, the script **skips** prune steps and **exits 0**.

## Usage

From the repository root:

```bash
./scripts/cleanup_docker_disk.sh
./scripts/cleanup_docker_disk.sh --help
```

### Flags

| Flag | Effect |
|------|--------|
| *(none)* | `docker builder prune -f` |
| `--aggressive` | `docker builder prune -af` |
| `--images` | Also `docker image prune -f` (dangling only) |
| `--all-images` | `docker image prune -a -f` — **dangerous**; requires confirmation |

### Environment variables

| Variable | Effect |
|----------|--------|
| `CLEANUP_DOCKER_AGGRESSIVE=1` | Same as `--aggressive` |
| `CLEANUP_DOCKER_IMAGES=1` | Same as `--images` |
| `CLEANUP_DOCKER_CONFIRM_ALL_IMAGES=1` | Required for non-interactive `--all-images` |

## Relationship to `scripts/docker_cleanup.sh`

- **`cleanup_docker_disk.sh`** — Host-wide **build cache** (and optional image prune). Use when **`/`** is full or before heavy builds.
- **`docker_cleanup.sh`** — Project-focused **stop/remove containers** and related image cleanup for this app. Use when you want to reset local containers/images **for this repo’s stack**.

Use both when appropriate: e.g. run **`cleanup_docker_disk.sh`** to free tens of gigabytes of BuildKit cache, then **`docker_cleanup.sh`** if you still need to tear down project containers.

## Market-pie5-bot: where this is referenced

There is **no** `full_deploy` hook in this repo. Run cleanup **manually** when disk is tight. **`scripts/start.sh`** and **`docs/START_STOP_RESTART.md`** point to this script.

## After cleanup

Run **`./scripts/start.sh`** (or your usual compose workflow). See **[START_STOP_RESTART.md](START_STOP_RESTART.md)** for process control.

## See also

- [docs/INDEX.md](INDEX.md) — documentation index  
- [START_STOP_RESTART.md](START_STOP_RESTART.md) — start / stop / restart  
