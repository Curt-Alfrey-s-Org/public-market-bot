# Documentation Index

Quick reference for market-pie5-bot docs. Use this to find topics without scanning all files.

## Mission & Roadmap

| Topic | Doc |
|-------|-----|
| Mission (Phase 1 stocks, Phase 2 options) | [MISSION.md](../MISSION.md) |
| Roadmap (current priority, phases, backlog) | [ROADMAP.md](ROADMAP.md) |
| Production readiness & React Native | [PRODUCTION_READINESS_AND_REACT_NATIVE.md](PRODUCTION_READINESS_AND_REACT_NATIVE.md) |

## Trading & Operations

| Topic | Doc |
|-------|-----|
| yfinance mode operations | [YFINANCE_OPERATIONS.md](YFINANCE_OPERATIONS.md) |
| yfinance test plan | [YFINANCE_TEST_PLAN.md](YFINANCE_TEST_PLAN.md) |
| Integration analysis | [INTEGRATION_ANALYSIS.md](INTEGRATION_ANALYSIS.md) |
| Live trading checklist | [LIVE_TRADING_CHECKLIST.md](LIVE_TRADING_CHECKLIST.md) |

## Development & Testing

| Topic | Doc / Command |
|-------|---------------|
| **ML & AI architecture (2026)** | [ML_AND_AI_ARCHITECTURE.md](ML_AND_AI_ARCHITECTURE.md) — layers, changes, why |
| **ALFa AI operator guide** | [ALFA_AI_HOW_TO_USE.md](ALFA_AI_HOW_TO_USE.md) |
| **ALFa env vars** | [ENV_VARS.md](ENV_VARS.md) |
| Dependencies | [DEPENDENCIES.md](DEPENDENCIES.md) — Python + frontend |
| Test runner | `python3 tests/runner.py` |
| Self-test + analyze | `./run_selftest_and_analyze.sh` |
| Testing guide | [TESTING_GUIDE.md](../TESTING_GUIDE.md) |
| Contributing | [CONTRIBUTING.md](../CONTRIBUTING.md) |

## Operations

| Topic | Doc / Command |
|-------|---------------|
| **Start / stop / restart** | [START_STOP_RESTART.md](START_STOP_RESTART.md) — `./scripts/start.sh`, `./scripts/stop.sh` |
| **What controls the app** | [WHAT_CONTROLS_THE_APP.md](WHAT_CONTROLS_THE_APP.md) — Request flow, key files |
| **Disk / Docker cleanup** | [DOCKER_DISK_CLEANUP.md](DOCKER_DISK_CLEANUP.md) — host build-cache vs `scripts/docker_cleanup.sh` (project containers) |

## Troubleshooting (symptom → doc)

| Symptom / topic | Doc | One-line |
|-----------------|-----|----------|
| API not responding, connection refused | [START_STOP_RESTART.md](START_STOP_RESTART.md) | Run `./scripts/start.sh` or `./start_api.sh`; check port 8002 |
| Test failures | [TESTING_GUIDE.md](../TESTING_GUIDE.md) | Testing docs, troubleshooting |
| OAuth / token errors | [TOKEN_ENCRYPTION_GUIDE.md](../TOKEN_ENCRYPTION_GUIDE.md) | Token setup, encryption |
| Env var conflicts | [ENV_CONFLICT_CHECKER_GUIDE.md](../ENV_CONFLICT_CHECKER_GUIDE.md) | Check conflicting settings |
| Live mode issues | [LIVE_MODE_GUIDE.md](../LIVE_MODE_GUIDE.md) | Live trading setup, safety |
| Known bugs | [KNOWN_ISSUES.md](../KNOWN_ISSUES.md) | Current limitations, workarounds |
| Collect logs for analysis | `./collect_logs.sh` | Bundles logs into errorlogs.txt |

## Cross-Repo & Setup Improvements

| Topic | Doc |
|-------|-----|
| **Rankings-bot → market-bot improvements** | [RANKINGS_BOT_IMPROVEMENT_ANALYSIS.md](RANKINGS_BOT_IMPROVEMENT_ANALYSIS.md) — Non-mission code from rankings-bot to apply here |

## Skip When Scanning

- `archive/` — Archived completion reports
- Root-level `*_SUMMARY.md`, `*_COMPLETE.md` — Session summaries

## Archive

- [docs/archive/](archive/) — Completion reports and implementation summaries (historical reference)
