# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed / Security (2026-09-26 round 2 review)
- **Admins can delete users on Postgres again.** `DELETE /api/users/{username}` returned 500
  (FK violation) for any user with verification tokens or audit rows; those rows are now removed or
  detached first (audit history is kept).
- **`POST /api/auth/login` and `/api/auth/register` are rate limited** (10/minute, same as
  `/api/v1/auth/login`). The web GUI login had no brute-force limit.
- **Settings values with line breaks are not written to the runtime env file** (they could add
  arbitrary `KEY=VALUE` lines).
- `GET /api/settings` reports `SCHWAB_SANDBOX_MODE` as `false` when unset, matching what the bot uses.
- Frontend API client no longer auto-retries POST/PUT/DELETE after a 5xx (could repeat bot control or
  trade approval actions); GET retries are unchanged.
- `test_mode_override.py::test_mode_defaults` expected the old sandbox default; aligned with the code.
- Tests: `tests/backend/test_review_2026_09_26.py`.

### Security / Fixed (2026-09-25 final round — leftovers from PR #383)
- **`POST /api/assets/upload` is admin-only.** Any logged-in user could write files (up to 100 MB
  each) into the served assets folder; it now needs an admin JWT. `GET /api/assets` (list) still works
  for any logged-in user.
- **Removed the stale committed frontend build `api/static/`** (23 files). It was an old Vite build that
  still trusted a client-side role, and it was only reachable directly on the API port: production serves
  the UI from the `market-bot-frontend` container, whose nginx proxies only `/api/` and `/ws` to the API.
  Without `api/static/` the API serves no UI: `/` returns a small JSON banner (`200`) and other non-API
  paths return `404` (previously `503`). `api/static/` is now in `.gitignore`. To serve a UI from the API
  outside Docker, build it yourself (`cd frontend && npm run build`, then copy `dist/` to `api/static/`).
- **`scripts/latency_probe.py` and `scripts/load_test_probe.py` authenticate** via
  `scripts/market_bot_auth.py` (`MARKET_BOT_ADMIN_TOKEN`, or `MARKET_BOT_ADMIN_USERNAME` /
  `MARKET_BOT_ADMIN_PASSWORD`); they exit with code 2 and a clear message when no token is available,
  instead of measuring 401 responses.
- Tests: `tests/backend/test_assets_upload_auth.py`, `tests/backend/test_api_static_fallback.py`.

### Security / Fixed (2026-09-25 follow-up — remaining medium/low findings and leftovers from PR #382)
- **`GET /api/settings` no longer returns third-party API keys.** Schwab, Hugging Face, Alpha Vantage,
  News API and Finnhub keys come back as `********` when set and `""` when not, for every role. A
  mask sent back by the GUI is never stored, and the `PUT` response masks them too.
- **Firewall toggles are admin-only.** `GET /api/network/access/forbid` and `/allow` changed the
  outbound firewall for any logged-in user; they now need an admin JWT, like `POST /api/network/access`.
- **Frontend shows the real role.** `AuthContext` used to show any non-admin/director account as
  `admin`. It now keeps `admin`/`director`/`user` as issued by the server and refuses unknown roles.
  (The server already enforced roles, so this was a display bug.)
- **Operator scripts authenticate.** `scripts/probe_all_modes.sh`, `scripts/monitor_bot.py`,
  `scripts/yfinance_long_run.py` and `scripts/yfinance_mode_optimizer.py` use an admin token from
  `MARKET_BOT_ADMIN_TOKEN`, or log in with `MARKET_BOT_ADMIN_USERNAME`/`MARKET_BOT_ADMIN_PASSWORD`.
  Shared helper: `scripts/market_bot_auth.py`.
- **Runtime mode/settings persistence (low).** New `api/runtime_env.py`. In a container, mode and
  settings changes are written only to `BOT_RUNTIME_ENV_FILE` (for example
  `/app/data/runtime.env` on the mounted data volume). Without it nothing is written, and
  `PUT /api/settings` answers `persisted: false`. Host installs keep using the project `.env`.
  Trading defaults are unchanged.
- **Docker image includes `web_scrapers/` (medium).** Earnings/macro calendars, retail sentiment,
  options flow and the news monitor were silently disabled in the container because the package was
  not copied.
- **Alembic works (low).** `001_create_tables.py` now declares `revision = "001"` and runs on
  Alembic's connection. `alembic.ini` had options outside any section and would not parse. The chain
  `001 → 005` resolves (`alembic heads` → `005`).
- **`JWT_SECRET` / `JWT_SECRET_KEY` (low):** one read path. If both are set to different values,
  `JWT_SECRET` wins and a warning names the ignored variable.
- **`pytz` declared (low)** in `requirements.txt`. `main.py` imports it and pandas 3 no longer installs it.
- **Removed the unused `/home/operator/auth-service` client** (the import in `api/routes/auth.py` and
  `api/middleware/auth_middleware.py`, which was never imported and could not load).
- **Removed stray root files:** accidental shell output (`h origin main`,
  `k, docs, capital sizing, email demo -y`, `ersoperatorDesktopreposmarket-bot`) and generated
  logs/reports (`test_results.txt`, `test_failures.txt`, `stored_messages.json`,
  `runner_api_report.json`, `test_report_phase8.json`, `screener_results.txt`, `bot_log_operator.txt`).
  These are now in `.gitignore`.
- **CI runs `tests/backend`:** a new `backend-api` job in `.github/workflows/tests.yml` uses throwaway
  per-run credentials, and `iptables` is stubbed.
- Docs: `LOGIN_REFACTOR_SUMMARY.md`, `docs/PHASE_2BCE_COMPLETION.md` and
  `PRODUCTION_QUICK_REFERENCE.md` no longer show `admin123`/`user123`.
- Tests: `tests/backend/test_settings_secrets.py`, `tests/backend/test_runtime_env.py`,
  `tests/backend/test_network_toggle_auth.py`, `tests/test_alembic_chain.py`, plus JWT-name
  cases in `tests/test_security_config.py`.

### Security (2026-09-25 — org code review findings 8, 9, 10)
- **Control endpoints require an admin session (8).** Bot start/stop/shutdown/shutdown-server,
  `/api/bot/mode`, pending-trade approve/reject, settings writes, trade reset, network access and
  run-tests now depend on `require_admin` (admin JWT). v1 bot start/stop and v1 settings writes
  require a DB user with role `admin`. The `BOT_API_KEY` alone can no longer drive them.
- **API auth gate (8).** `RequireApiKeyMiddleware` + `BlockGuestMiddleware` replaced by
  `RequireAuthMiddleware`: `/api/*` needs a valid session JWT or (for scripts) `X-API-Key`.
  The client-sent `X-User-Role` header is ignored; `guest`/unknown-role tokens are rejected.
- **No backend secret in the frontend (8).** `VITE_API_KEY` removed from `frontend/Dockerfile`,
  `docker-compose.yml`, `api/config.py` (now optional/ignored) and the frontend code; the browser
  sends the logged-in user's Bearer token. Frontend login now maps the API's `token` field and
  rejects `success=false`, so the app never runs without a real session.
- **JWT secret required in production (10).** New `api/security_config.py`; `JWT_SECRET`
  (alias `JWT_SECRET_KEY`) signs both web and mobile tokens. No public default: missing or
  placeholder values stop the API at startup in production (`ENVIRONMENT` defaults to production).
- **No default login accounts (10).** Removed the built-in `admin/admin123` and `user/user123`
  from `api/routes/auth.py` and `api/routes/v1/auth.py`; env passwords compared in constant time.
- **Scripts:** removed a hardcoded API key and login from `scripts/run_selftest_subdomain_trail.sh`
  and fallback passwords from `scripts/verify_ports_and_health.sh`; redacted a literal key from
  `docs/SECRETS_MANAGEMENT.md`.

### Fixed (2026-09-25 — finding 9)
- **Bot could not start in its container:** `docker-compose.yml` now wires `BOT_REQUIRE_BRAIN`,
  `LITELLM_ENABLED` (default `true`), `LITELLM_BASE_URL` (default `http://192.0.2.30`),
  `LITELLM_API_KEY` (env only) and related settings. Startup and `/api/bot/start` report which
  variable is missing (`LITELLM_ENABLED` / `LITELLM_API_KEY`) instead of a generic "brain unreachable".
- `api/dependencies/auth.py` `get_admin_user` checked a non-existent `is_superuser` column; it now
  checks `role == "admin"`.

### Added (2026-09-25)
- `env.required.example` (placeholders for new/changed variables), tests
  `tests/backend/test_control_endpoint_auth.py`, `tests/backend/test_no_default_credentials.py`,
  `tests/test_security_config.py`.

### Security (2026-06-07)
- **axios** updated to ^1.17.0 (fixes CVE-2026-44490, CVE-2026-44494, CVE-2026-42033, CVE-2026-42035).
- **Python deps:** Pillow >=12.2.0, cryptography >=46.0.6, requests >=2.33.0.
- **CodeQL** GitHub Action updated v3 → v4.

### Changed (2026-06-07 — hub wheel unbloat)
- `build-contexts/` no longer carries local wheels (~302 MB removed from repo).
- `.gitignore` standardized: `build-contexts/wheels-bots/*` with `!.gitkeep`.
- Build scripts now auto-sync wheels from hub hub via `sync-bot-wheels-preflight.sh` (non-fatal — falls back to PyPI).

### Added (2026 — ALFa AI integration & ML/AI refit)
- **ALFa AI brain (LiteLLM)** on `` replaces HuggingFace for all LLM inference (`api/services/litellm_client.py`).
- **Error monitoring:** automatic capture → `error_events`, background triage (`code`), admin **AI Monitor** (`/admin/ai-monitor`).
- **Ask AI dock** with RAG, trust boundaries, NOT FINANCIAL ADVICE disclaimer.
- **Agentic jobs** (end-of-day summary, anomaly digest, sector rotation) via orchestrator `:8420`.
- **Dev tooling:** `AGENTS.md`, `scripts/codegen/ai_codegen.py`, `.github/workflows/ai-pr-triage.yml`.
- **Opt-in fine-tune capture** (`finetune_samples`, `FINETUNE_CAPTURE_ENABLED`).
- **`api/services/trading_insights_llm.py`** — LLM for performance narrative, trade journal, optimization *explanation* only.
- **`GET /api/ai/optimization-suggestions`**, `POST /api/ai/journal`.
- **`docs/ML_AND_AI_ARCHITECTURE.md`** — canonical ML vs AI layers, changes, and rationale.
- **`docs/ENV_VARS.md`** — ALFa AI / brain-gate environment reference.
- **Trading gate:** `BOT_REQUIRE_BRAIN=true` (default) — bot won't start/halt if brain down.

### Fixed (2026-06-07)
- **LiteLLM telemetry duration:** the error-path return in `api/services/litellm_client.py`
  now sets `total_duration_ns` from the measured request elapsed, so
  `ollama_activity_log.duration_seconds` records real latency for failed/non-200 LiteLLM
  calls instead of `0`. (The success path already set it.) Fix mirrors the reference
  implementation in `rankings-bot`, which carried the same bug at source.

### Changed (2026)
- **`ml_param_optimizer.py`:** backtest **heuristics** replace LLM JSON parameter suggestions (no proven OOS edge for LLM tuning).
- **`main.py` `analyze_strategy()`:** narrative-only LLM; no auto-applied settings from LLM responses.
- **`apply_ai_suggestions()`:** heuristic optimizer only when `BOT_ENABLE_AI_AUTO_TWEAK=true`.
- **Frontend AI page:** copy updated (narrative vs HuggingFace).
- **Docs:** README, ML_GUIDE, AI_IMPROVEMENTS_GUIDE, INDEX, DEPENDENCIES, INTEGRATION_* reconciled for HF removal and new architecture.

### Removed (2026)
- HuggingFace cloud LLM path (`HUGGINGFACE_*`, `test_hf_api*.py`).
- LLM-as-“trading expert” parameter JSON contract (`AI_SYSTEM_PROMPT` settings block).

### Added
- **Rankings-bot improvements (non-mission setup):**
  - `.github/CODING_STANDARDS.md` — Python, FastAPI, React, Docker, security, trading safety
  - `scripts/start.sh`, `scripts/stop.sh` — Unified start/stop (--dev, --api-only)
  - `docs/START_STOP_RESTART.md` — Quick reference for start/stop commands
  - `docs/WHAT_CONTROLS_THE_APP.md` — Request flow (Vite → API)
  - `docs/PRODUCTION_API_OWNERSHIP.md` — Process ownership, Twelve-Factor
  - `.github/PORT_ASSIGNMENTS.md` — Canonical ports (8002, 5173)
  - `docs/DEPENDENCIES.md` — Python + frontend dependency reference
  - Expanded `docs/INDEX.md` — Operations section, troubleshooting table
- **Dry-run (Live) Mode Tests:**
  - Comprehensive test coverage for dry-run mode configuration in `test_mode_override.py`
  - Validates `DRY_RUN_MODE` environment variable behavior
  - Tests dry-run mode with live-like settings (paper=false, sandbox=false, api=on)
  - Verifies DRY_RUN_MODE defaults to false when not set
  - Tests multiple value formats (true/false, on/off, yes/no, 1/0)
- **Copilot PR Label Gate:**
  - New workflows to enforce and automate Copilot PR completion signals:
    - `.github/workflows/copilot-label-gate.yml` requires the `copilot-completed` label on Copilot PRs
    - `.github/workflows/copilot-auto-label.yml` auto-adds `copilot-completed` when all checks pass
  - Documentation updates in README, CONTRIBUTING, COPILOT_TASK, and COPILOT_SENTINEL_VISUAL_GUIDE
- **Component Enhancements:**
  - Portfolio optimization caching with 5-minute TTL for improved performance
  - Component coordination state tracking for better integration between ML components
  - Enhanced ML parameter application with improved feedback loops
  - Cache invalidation on parameter changes
  - Better coordination between ML filter, portfolio optimizer, and adaptive learning
- **Testing Infrastructure:**
  - Comprehensive test suite for component enhancements (`test_component_enhancements.py`)
  - Cursor rule for testing requirements (`.cursor/rules/TEST_AND_VERIFY.mdc`)
- **Documentation:**
  - Component enhancement plan (`docs/COMPONENT_ENHANCEMENT_PLAN.md`)
  - Testing and monitoring guide (`docs/TESTING_MONITORING.md`)
  - Error fix documentation (Plotly, yfinance, feed refresh)

### Fixed
- **Plotly Chart Errors:**
  - Fixed "nonexistent object" errors in chart creation
  - Improved subplot handling using `make_subplots()`
  - Better empty data handling during bot boot
  - Enhanced error handling for chart creation
- **yfinance Error Suppression:**
  - Suppressed delisted stock error messages
  - Added stderr capture for yfinance errors
  - Reduced log noise from non-critical errors
- **Feed Refresh Issues:**
  - Added throttling to prevent excessive refresh attempts
  - Fixed thread exhaustion errors
  - Improved error handling with cached data fallback
- **Log Noise Reduction:**
  - Reduced excessive "Feed refresh requested" logging
  - Changed configuration warnings to DEBUG level
  - Improved error message clarity

### Changed
- **Workflow: Linux-only via Cursor Remote-SSH (no Windows ↔ Linux push/pull):**
  - **`.cursor/rules/dev-deploy-workflow.mdc`**: Primary setup is SSH into Linux + Cursor Remote-SSH; edit, run, commit, push all on Linux.
  - **`.cursor/rules/linux-commands-script.mdc`**: Added context that user works on Linux via Remote-SSH; `debug_logs/run_N_*` are local — open in Cursor; push for backup/collab only. Commit message no longer "for Cursor."
  - **`.cursor/rules/commands-last.mdc`**: Example context "On Linux Mint" → "On Linux."
  - **`debug_logs/README.md`**: Flow updated: run script on Linux (you're there), open `run_N_*` directly in Cursor; push optional for backup. "Done" message no longer "Pull on Windows."
  - **`DEV_DEPLOY_WORKFLOW.md`**: Reworked for Linux-only workflow: Connect via Remote-SSH, edit/run/commit/push on Linux; debug logs local; one-time setup uses `git clone` + venv; summary updated.
  - **`scripts/run_linux_commands*.sh`** (all): "Done" echo changed from "Pull on Windows and check..." to "Check debug_logs/run_N_*...."

### Added
- **Top Performers Feed refactor (roadmap idea #2):**
  - **`top_performers_feed.py`**: New module implementing live feed of top performing stocks with real-time price updates and auto-replacement. `TopPerformersFeed` class tracks performance history, identifies underperformers (5%+ drop), and automatically replaces them with better candidates. Thread-safe operations with lock-based access. `get_top_performers_feed()`, `get_feed_symbols()`, `get_feed_data()` convenience functions.
  - **`web_gui.py`**: Completely refactored top performers list on homepage. Replaced legacy watchlist UI with new "Top Performers Feed (Live)" widget showing live ticker data (price, change, change % with color coding). New callbacks: `update_feed_display()` (auto-refresh + manual refresh), `feed_refresh_feedback()`. Bot loop priority updated: **Feed → Watchlist → Screener/File** (feed checked FIRST as per roadmap #2). Feed initialization on startup. Legacy watchlist kept for backward compatibility (hidden).
  - **`.env.example`**: Added feed configuration: `ENABLE_TOP_PERFORMERS_FEED` (default: `true`), `TOP_PERFORMERS_FEED_SIZE` (default: 50), `TOP_PERFORMERS_FEED_UPDATE_INTERVAL` (default: 300s), `TOP_PERFORMERS_FEED_PERFORMANCE_WINDOW` (default: 3600s), `TOP_PERFORMERS_FEED_REPLACEMENT_THRESHOLD` (default: 0.05).
  - **`scripts/run_linux_commands_6.sh`**: Verification script for feed refactor (checks module, imports, UI integration, bot loop priority, syntax).
- **Live capital from Schwab API (roadmap idea #1):**
  - **`main.py`**: Added `_update_capital_from_schwab_api()` method that fetches account cash/buying power from Schwab API via `get_account()` / `get_accounts()`. In live production mode (not paper/sandbox), automatically updates `BOT_TOTAL_CAPITAL` with real account funds on bot startup. Added `_extract_capital_from_account_data()` and `_extract_capital_from_accounts_list()` helpers. Added `refresh_capital_from_schwab_api()` for periodic updates.
  - **`USE_SCHWAB_CAPITAL_IN_LIVE`** env var (default: `true`): Controls whether to fetch capital from Schwab API in live mode. When `true`, overrides `BOT_TOTAL_CAPITAL` config with actual account funds.
  - **`.env.example`**: Added `USE_SCHWAB_CAPITAL_IN_LIVE` with comment explaining usage.
  - **`LIVE_MODE_GUIDE.md`**: Updated "Capital & Position Sizing" section to document Schwab API capital fetch. Updated env vars table.
  - **`docs/LIVE_PRODUCTION_FLOW.md`**: Updated "Bot creation" step to mention capital fetch from Schwab API.
- **Roadmap ideas (user – Jan 2026):**
  - **`ROADMAP.md`**: New **Design principles** (mimic TOS, tweak reference code). New **Roadmap Ideas (User – Jan 2026)** section: (1) Live capital from Schwab API (funds available); (2) Top performers / popular symbols feed (TOS-like, checked first); (3) T+1 / no funds → alerts + stored messages + capital schedule; (4) Opens/closes: position priority, profit-based trailing-stop tightening, hold-period data, feedback module, resource efficiency, stored messages vs alerts; (5) Filter/sort on all lists; (6) Trade tab UX (symbol-grouped, no hunting); (7) GUI upgrade (stock-market-bot look, animation, pages/tabs/charts); (8) Capital management for held positions (exit at minimal loss to free capital, user approval); (9) Risk-based capital allocation (low/med/high risk sectors, ML + capital + win rate). Research notes: Schwab trailing stop, hold-period data, trade-tab grouping.
- **Numbered Linux scripts (no overwriting):**
  - **`scripts/run_linux_commands_2.sh`**: Short-selling validation → `debug_logs/run_2_env_info.txt`, `run_2_results.txt`. `git pull`, venv, unittest `test_order_type_configuration` / `test_strategy_signals` / `test_short_selling` / `test_order_payload_builder`, then push.
  - **`scripts/run_linux_commands_3.sh`**: Screener test → `debug_logs/run_3_env_info.txt`, `run_3_results.txt`. Same flow; runs `run_screener_test.py` with small batch.
  - **`debug_logs/README.md`**: Numbered runs table (_2, _3, …), `run_N_*` outputs. **`DEV_DEPLOY_WORKFLOW.md`**, **`docs/SCREENER_TEST_ANALYSIS.md`**: Updated to use `run_3` for screener, `run_2` for short-validation.
  - **`.cursor/rules/linux-commands-script.mdc`**: Create **`run_linux_commands_N.sh`** (next N) instead of overwriting; write to `debug_logs/run_N_*`. **Legacy** `run_linux_commands.sh` kept with deprecation note; prefer _2 / _3.
- **Short-selling validation (Linux script):**
  - **`scripts/run_linux_commands.sh`** (legacy): Short-selling validation; overwrites `debug_logs` files. Prefer **`run_linux_commands_2.sh`**.
  - **`debug_logs/README.md`**: `short_validation` content now under run 2 (`run_2_results.txt`).
- **Capital & position sizing docs:**
  - **`LIVE_MODE_GUIDE.md`**: New § **4. Capital & Position Sizing** — dry-run vs live capital ($10k / $1k), conservative live start preset (`BOT_MIN_ALLOCATION=50`, `BOT_MAX_ALLOCATION=200`, `BOT_POSITION_SIZE=0.01`, etc.), env vars table. TOC updated.
  - **`.env.example`**: Comments for `BOT_TOTAL_CAPITAL` (10000 dry-run, 1000 live) and conservative live start; link to LIVE_MODE_GUIDE.
  - **`ROADMAP.md`**: User Workflow "Capital & sizing" items marked done.
- **Copilot task and workflow:**
  - **`.github/COPILOT_TASK.md`**: Scoped task — **Update DOCUMENTATION_INDEX** (add `EMAIL_ALERTS_GUIDE`, `debug_logs/README`, refresh `DEV_DEPLOY_WORKFLOW` row). Branch: `copilot/update-documentation-index`. Links from copilot-instructions.md.
  - **`.github/copilot-instructions.md`**: "Current task for Copilot" at top; workflow steps, branch naming, `copilot-completed` label.
  - **Dry-run (Live) mode tests**: Tests in `test_mode_override.py` for the fourth web GUI mode; `DRY_RUN_MODE`, four mode configs (Sandbox, Live, Training, Dry-run Live). **`main.py`**: `_get_dry_run_mode()` helper for `DRY_RUN_MODE`.
- **Debug logs for Cursor (Linux → push → analyze)**:
  - **`debug_logs/`**: Logs captured on Linux and pushed so Cursor can analyze after `git pull`. **`debug_logs/README.md`** describes usage.
  - **`debug_logs/env_info.txt`**: Run timestamp, `python3 --version`, venv prefix, relevant env vars (MAX_STOCKS, SCREENER_*, etc.).
  - **`debug_logs/screener_results.txt`**: `run_screener_test.py` stdout+stderr (timing breakdown, pass/fail, symbols).
  - **`scripts/run_linux_commands.sh`**: Captures env_info + screener run → `debug_logs/`, then `git add debug_logs/` + commit + push. Run on Linux; pull on Windows and open `debug_logs/screener_results.txt` (or `env_info.txt`) for Cursor to analyze.
  - **`DEV_DEPLOY_WORKFLOW.md`**: New "Debug logs for Cursor" section. **`docs/SCREENER_TEST_ANALYSIS.md`**: Quick-reference row for "Capture + push (Linux script)".
- **Dry-run (Live) mode button**:
  - **Web GUI:** 4th mode button **Dry-run (Live)** on the homepage. Like Live (real credentials, risk checks) but **no orders placed**; sets `DRY_RUN_MODE=true` for the session when Start is clicked. Use to validate live config before going true Live.
  - **`web_gui.py`:** `mode-dryrun-live-button`; `select_mode` handles it; `control_bot` applies Live-like `PAPER_TRADING_MODE`/`SCHWAB_SANDBOX_MODE`/`SCHWAB_API_ENABLED` plus `DRY_RUN_MODE=true`. Logs "Dry-run: true" when selected.
  - **`docs/ENV_SIMPLIFICATION.md`:** Updated to 4 mode buttons; Dry-run (Live) in table and “Changes applied.” **ROADMAP** Pick up next: Dry-run button marked done.
- **Cursor rule: Linux commands as test script**:
  - **`.cursor/rules/linux-commands-script.mdc`**: When a reply ends with **"Commands to run"** for Linux (git, `python3`, tests, etc.), **create or overwrite** `scripts/run_linux_commands.sh` with those commands. User runs `./scripts/run_linux_commands.sh` on Linux — no copy-paste errors, faster.
  - **`scripts/run_linux_commands.sh`**: Placeholder script (overwritten when Cursor gives commands). Uses `#!/usr/bin/env bash`, `set -e`, `cd` to project root.
  - **`DEV_DEPLOY_WORKFLOW.md`**: Short "Linux commands script" section describing the rule and usage.
- **Screener optimization (batch mode, ~3s goal for ~200 filtered)**:
  - **Phase 1 (fetch+filter):** Batch fetch via `yf.download(symbols, group_by="ticker", threads=True)` in chunks of `SCREENER_BATCH_SIZE` (default 200). Fetch **full** scan pool (`MAX_STOCKS_TO_SCAN`, default 600); **no early cutoff** so we don’t miss good candidates. Filter by price/vol/volatility. Goal ~3s for ~200 filtered (TOS-like).
  - **Phase 2 (sort):** Score remaining stocks (momentum, volume, volatility, liquidity proxy when `marketCap=0`), sort, return top `max_results`.
  - **Config:** `SCREENER_USE_BATCH_FETCH` (default true), `SCREENER_BATCH_SIZE`, `SCREENER_TARGET_FILTERED`, `MAX_STOCKS_TO_SCAN` (default 600). Batch mode skips sentiment/ML; disable batch for full advanced filtering.
  - **`stock_screener.py`:** `_fetch_batch_stock_info`, batch path in `screen_stocks`. **`docs/SCREENER_TEST_ANALYSIS.md`** updated with “Screener optimization (implemented).”
- **ROADMAP – User workflow & constraints; Pick up next (2026-01-24)**:
  - **User Workflow & Constraints:** $10k dry-run / $1k live start; very small $ at first live; 50-stock pool note (enough for best candidates, configurable); 3 day-trades/week for "cash cow" picks, other trades next calendar day (swing); after-hours trading support.
  - **Pick up next:** Dry-run (Live) mode button (screener batch optimization done). Linked from ROADMAP Backlog.
- **Strategy-based trading (Phase 1)**:
  - `get_strategy_signal(symbol)` on TradingBot: fetches OHLCV (DataFetcher or yfinance), runs SMA 20/50 via StrategyManager, returns (BUY|SELL|HOLD, price, volume)
  - CLI (`main`) and GUI (`run_bot`) trading loops use strategy signals instead of hardcoded BUY; HOLD skips, BUY/SELL trigger `execute_trade`
  - `test_strategy_signals.py`: unit tests for `get_strategy_signal`
- **(signal, position) → action mapping (Phase B)**:
  - `_signal_to_action(symbol, signal)`: maps BUY/SELL + position → BUY, SELL, SHORT, COVER, or None (skip). SELL+flat→SHORT, BUY+short→COVER; BUY+long / SELL+short → skip.
  - CLI and GUI loops use mapped action for `execute_trade`; enable shorts from strategy BUY/SELL without strategies emitting SHORT/COVER.
  - `TestSignalToAction` in `test_strategy_signals.py` for all mapping cases.
- **Margin/short-availability and short concentration limits**:
  - Env: `ALLOW_SHORTS_IN_PAPER`, `SCHWAB_SHORT_SELLING_ENABLED`, `MAX_SHORT_POSITIONS`, `MAX_SHORT_EXPOSURE_PCT`
  - `can_open_short(allocation, for_live)`: gates SHORT in paper/live; enforces max short positions and max short exposure % of capital
  - Paper and live `execute_trade` paths call `can_open_short` before opening SHORT; skip with `reason='short_not_allowed'` when blocked
  - `TestCanOpenShort` in `test_short_selling.py`; `.env.example` updated
- **Entry/exit price audit and limit offset**:
  - **docs/ENTRY_EXIT_PRICE_AUDIT.md**: Audit of price source, flow, order-type usage, gaps; reference for roadmap work
  - **LIMIT_ORDER_OFFSET_PCT** (env, default 0): Optional limit-order price offset; opens = price×(1−offset), closes = price×(1+offset); cap 0–5%
  - ROADMAP task **Entry/Exit Price & Order-Type Logic** (wire order_types, price sources, exit logic)
- **Entry/exit price & order-type logic (ROADMAP §4)**:
  - **order_payload_builder.py**: Builds Schwab API payloads for MARKET, LIMIT, STOP, STOP_LIMIT, TRAILING_STOP; wired into `execute_trade_live_mode`. Env: `STOP_OFFSET_PCT`, `STOP_LIMIT_OFFSET_PCT`, `TRAILING_STOP_ORDER_PCT`
  - **PRICE_SOURCE** (env): `realtime` (default) vs `last_close`; `get_strategy_signal` uses last OHLCV close when `last_close`
  - **EXIT_REFRESH_PRICE** (env, default true): Re-fetch price immediately before SELL/COVER in CLI and GUI; use for execution
  - **VALID_ORDER_TYPES** extended to include STOP, STOP_LIMIT, TRAILING_STOP; `.env.example` updated
- **Cursor rules (`.cursor/rules/`)**:
  - **commands-last**: Put suggested terminal commands in a "Commands to run" block at the end of responses
  - **dev-deploy-workflow**: Build on Windows, run on Linux Mint (python3 + venv); reference DEV_DEPLOY_WORKFLOW
  - **mission-phase-scope**: Phase 1 (stocks buy/short) before Phase 2 (options); reference MISSION.md
  - **docs-and-tests**: Update CHANGELOG, DOCUMENTATION_INDEX, add tests when adding features
  - **python-standards**: PEP 8, max line 127, flake8/black/isort (applies when editing `**/*.py`)
- **Dev/deploy workflow (build on Windows, run on Linux Mint)**:
  - **DEV_DEPLOY_WORKFLOW.md**: Edit on Windows → push to GitHub → pull on Linux Mint; run with `python3` in venv; test on server
  - **.gitattributes**: Enforce LF for `*.sh`, `*.py`, etc., so scripts run correctly on Linux when edited on Windows
  - CONTRIBUTING, DOCUMENTATION_INDEX, README: links to workflow and `python3`/venv run instructions
- **Mission & Production Scope (2026-01-24)**:
  - **MISSION.md**: Canonical mission — Phase 1 (stocks buy/short) → Phase 2 (options); production-ready definition, gap analysis, Phase 1 checklist
  - Short selling (Phase 1) added as top priority in ROADMAP and PROJECT_STATUS
  - Mission references in README, PROJECT_STATUS, ROADMAP, DOCUMENTATION_INDEX
- **Linux Mint Compatibility (2026-01-22)**:
  - **LINUX_MINT_GUIDE.md**: Comprehensive 493-line installation and setup guide for Linux Mint users
  - **MARKET_MINT_BOT_GUIDE.md**: 487-line guide for creating a Linux Mint-focused fork
  - **LINUX_MINT_COMPATIBILITY_SUMMARY.md**: Implementation summary and documentation
  - Linux Mint compatibility badge in README.md
  - Platform compatibility section in README.md
  - OS detection in install.sh with Linux Mint-specific messaging
  - Updated desktop files with multi-platform compatibility notes
- GitHub Actions CI/CD pipeline for automated testing
- Security scanning with CodeQL, Safety, and Bandit
- Code quality checks with flake8, pylint, black, and isort
- Automated release workflow with distribution archives
- Feature maturity indicators in ML documentation
- Comprehensive trade data tracking for AI analysis
  - Entry and exit prices for all trades
  - P&L metrics (dollar and percentage)
  - Exit reasons (trailing stop, target reached, etc.)
  - Hold duration for position analysis
  - Volatility and volume data
  - Enhanced trade history display in web GUI

### Changed
- **Stock universe – Russell 1000**: **`stock_screener.py`** uses **Russell 1000** (`Russell 1000 Index` on Wikipedia) for “Russell index” coverage. ~1000 largest US names; skips small-cap “bottom.” Wikipedia has no full Russell 2000 list; Russell 1000 has a full Components table. Universe: S&P 500, NASDAQ-100, Dow, S&P 400, Russell 1000. Fetch logic picks the first Wikipedia table with a Symbol column (Robust to Record/Returns-before-Components layout).
- **.env simplification**: **`docs/ENV_SIMPLIFICATION.md`** – mode buttons (current 3, when to add e.g. Dry-run), **what affects what** map, duplicate removal, deprecated vars. **`.env.example`** consolidated duplicate Stock Discovery blocks, removed **`ENABLE_PDT_RULES`** (deprecated), added **WHAT AFFECTS WHAT** summary and section headers (1. SCHWAB, 2. Trading mode, 3. Stock discovery). **`DOCUMENTATION_INDEX`** links `docs/ENV_SIMPLIFICATION.md`.
- **Screener test runner**: **`run_screener_test.py`** configures logging, suppresses Pandas4Warning (`module="yfinance.*"`), runs `screen_for_trades`, and prints returned symbols. Use `python3 run_screener_test.py 2>&1 | tee screener_results.txt` so Cursor can analyze timing/pass-fail. **`docs/SCREENER_TEST_ANALYSIS.md`** explains capture, re-run, and **example analysis** (2026-01-25): 33 s total, 100% in fetch; 50 fetches @ ~0.66 s avg; recommendations (parallelize fetches, batch yfinance, early exit).
- **Stock screener (universe vs scan pool, .env, timing)**: Logging now states **"Screening up to X stocks from universe of Y (returning up to Z that fit .env: price $A–$B, vol ≥ C)"** so it's clear we don't screen the full universe (e.g. 158) one-by-one; we cap the scan pool. Scan pool is capped at `min(MAX_STOCKS_TO_SCAN, max(max_results*3, 50), universe size)` so we never screen far more than we need (e.g. 50 → 150 max). **Timing instrumentation**: Added detailed timing breakdown (fetch, filter, sentiment, ML, scoring) to identify bottlenecks; controlled by `ENABLE_SCREENER_TIMING` (default true). Shows total time, per-operation time, avg/call, and % of total. **.env.example** clarifies that MAX_STOCKS_TO_SCAN = how many we fetch one-by-one; set closer to TOP_STOCKS_TO_TRADE (e.g. 60) if you only need 50 that fit, to reduce API calls.
- **Pandas/yfinance warnings**: `main.py`, `web_gui.py`, **`data_fetcher.py`**, and **`async_data_fetcher.py`** filter `Timestamp.utcnow` (Pandas4Warning) by message (`r'.*Timestamp\.utcnow.*'`); **pytest.ini** `ignore:.*Timestamp.utcnow.*`. **`run_unittest.py`**: bootstrap runner that sets the filter **before** any imports, then runs `unittest discover`; use for full-suite runs with clean output. **DEV_DEPLOY_WORKFLOW** recommends `python3 run_unittest.py` for the full suite. (Do **not** use `PYTHONWARNINGS=ignore::pandas.errors.Pandas4Warning` — it yields "Invalid -W option: invalid module name".)
- **When to run which tests**: **DEV_DEPLOY_WORKFLOW.md** documents **quick validation** (targeted tests: order-type, strategy signals, short selling, order payload) vs **full suite** (run less often, before PR / after major pulls). Fewer full runs, faster iteration.
- **Strategy-based trading**: ROADMAP Short Selling updated (signal→action mapping done; optional explicit strategy SHORT/COVER); MISSION checklist updated (strategies + mapping complete)
- **Short selling**: ROADMAP/MISSION updated (margin/availability + concentration limits done; buy-in risk deferred)
- **Entry/exit price**: Audit updated; order_payload_builder wired; PRICE_SOURCE, EXIT_REFRESH_PRICE, STOP/STOP_LIMIT/TRAILING_STOP; ROADMAP §4 done
- **Mission & Production Scope (2026-01-24)**:
  - PROJECT_STATUS overview: production-ready for long-only; Phase 1 = buy + short, Phase 2 = options
  - ROADMAP: Mission & Phase 1 scope section; short selling as high-priority task; Q1 goals aligned with Phase 1
  - DOCUMENTATION_INDEX: MISSION in essential docs; "Mission & Production Readiness" and developer paths
- **Linux Mint Compatibility (2026-01-22)**:
  - README.md description now mentions both Raspberry Pi 5 and Linux Mint
  - install.sh enhanced with platform detection and better user guidance
  - Desktop files updated for broader Linux distribution support
  - DOCUMENTATION_INDEX.md includes new Linux Mint guides
- Clarified ML feature status from "experimental" to "production-ready" with clear user requirements
- Updated documentation to reflect actual feature maturity levels
- Enhanced `record_trade` method to accept comprehensive trading metrics
- Improved web GUI trade cards with detailed sell order information

### Fixed
- **Order-type tests `no_auth_client` on Linux:** `DRY_RUN_MODE` was false due to `.env` or import order (`main` imported by another test first). Tests now **patch `main.DRY_RUN_MODE` to `True`** in each `execute_trade_live_mode` test so the dry-run path is always used, and force `os.environ['DRY_RUN_MODE'] = 'true'` before importing `main`.
- **Flaky BUY dry-run / order-type tests**: `execute_trade_live_mode` BUY path uses `generate_random_volume()` and `filter_stock`; when volume < `MIN_DAILY_VOLUME` the trade is `skipped` and tests expecting `dry_run_success` failed intermittently. `test_order_type_configuration` and `test_live_mode_dry_run` now mock `filter_stock` (and, where needed, `LIMIT_ORDER_OFFSET_PCT`) for BUY dry-run assertions so they no longer flake.
- Documentation confusion around ML features requiring user verification
- Missing sell order data in trade history display

## [1.0.0] - 2026-01-18

### Added
- Initial stable release
- Complete trading bot with multiple strategies (SMA, RSI, MACD, Bollinger Bands, Momentum)
- ML-based signal filtering (production-ready)
- Web-based dashboard with real-time charts
- Desktop GUI for Raspberry Pi 5
- Pattern Day Trading (PDT) compliance
- Schwab API integration with OAuth 2.0
- Sandbox mode for realistic testing
- yfinance simulation mode with auto-fallback
- Sentiment analysis integration
- Portfolio optimization (Modern Portfolio Theory)
- Advanced order types (Market, Limit, Stop, Stop-Limit, Trailing Stop, OCO, Bracket)
- Comprehensive risk management
- Backtesting with Backtrader
- Resource monitoring and throttling
- Centralized logging and reporting
- Alert system with email notifications

### Security
- Secure OAuth token storage
- Environment variable configuration for secrets
- Rate limiting and API error handling

## Release Process

To create a new release:

1. Update the version in this CHANGELOG.md
2. Commit the changes: `git commit -am "Prepare release v1.x.x"`
3. Create and push a tag: `git tag -a v1.x.x -m "Release v1.x.x" && git push origin v1.x.x`
4. GitHub Actions will automatically create the release with artifacts

[Unreleased]: https://github.com/operator/market-pie5-bot/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/operator/market-pie5-bot/releases/tag/v1.0.0
