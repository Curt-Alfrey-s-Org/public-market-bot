# market-pie5-bot Roadmap

**Last updated:** Jul 2026 (AI consolidation complete; production-readiness next)

---

## Next step: post-merge host steps from the 2026-09-26 review (PR #386 fixes, PR #387 deps)

> Open for review 2026-09-26: [#386](https://github.com/Curt-Alfrey-s-Org/market-pie5-bot/pull/386) (user delete 500, rate limit on the legacy `/api/auth/login` + `/api/auth/register`, env-file newline injection, sandbox-mode display default, no auto-retry of POST/PUT/DELETE after a 5xx) and
> [#387](https://github.com/Curt-Alfrey-s-Org/market-pie5-bot/pull/387) (vulnerable Python floors raised, frontend `npm audit` fixes).
> Independent PRs; merge in either order and do one rebuild after both. This section lives on the #386 branch but covers both PRs. No trading code in `main.py` is touched. No new env vars, no secrets to rotate.
> Host: **** (`/home/operator/market-pie5-bot`). The  VM is currently powered off, so power it on first. `/home/operator/market-pie5-bot` on  is a backup copy only.

**Before pulling**

- [ ] **Power on VM  first** (it is currently powered off).
- [ ] Nothing to back up (no tracked files removed, no `.env` changes).

**After merging PR #386 (fixes)**

- [ ] **:** `cd /home/operator/market-pie5-bot && git pull`, then `docker compose --env-file .env up -d --build` (rebuilds API and frontend).
- [ ] **Behaviour change:** `/api/auth/login` and `/api/auth/register` now allow 10 requests/minute. Behind the frontend nginx every user shares one bucket (the limiter keys on the peer IP), so after 10 attempts in a minute everyone gets 429 for the rest of that minute.
- [ ] **Verify:** admin login works; deleting a test user in the GUI now succeeds (was 500 on Postgres); `GET /api/settings` shows `SCHWAB_SANDBOX_MODE=false` when unset (matches what the bot uses).

**After merging PR #387 (deps)**

- [ ] **:** `git pull`, then `docker compose --env-file .env up -d --build` (the build reinstalls Python deps; one rebuild covers both PRs if merged together).
- [ ] Before that build, check `build-contexts/wheels-bots/` doesn't hold only older wheels below the new floors (for example aiohttp < 3.14.3, cryptography < 50, lxml < 6.1) when the build runs without internet; refresh the wheel cache if it does.
- [ ] **Non-Docker frontend:** `cd frontend && npm ci` (lockfile regenerated; npm `overrides` pins minimatch 9.0.9).
- [ ] **Verify:** API and frontend containers healthy, GUI loads, `pytest tests/backend` locally (GitHub Actions isn't running).

**Decisions for you**

- [ ] **Failed order stays re-approvable:** `main.py` `approve_pending_trade` (~lines 2725-2742) sets `approved` before `execute_trade`; if execution raises, the trade stays in `pending_trades` and a second approve runs it again. The fix belongs in trading code (`main.py`), which the review didn't touch. (#386)
- [ ] **Missing `-centralized` endpoints:** the frontend calls `/api/auth/register-centralized`, `/verify-email-centralized`, `/refresh-centralized`, which don't exist, so UI registration always fails. Switch to `/api/auth/register` (no verification email yet) or build them. (#386)
- [ ] **`/ws` WebSocket has no auth** (leaks running/mode only); needs the frontend to send a token. (#386)
- [ ] **Rate limit behind nginx:** to key per user IP, run uvicorn with `--proxy-headers --forwarded-allow-ips=<nginx container IP>` (deploy decision). (#386)
- [ ] **CORS:** `allow_origin_regex` matches any hostname with `allow_credentials=True` (`api/main.py:616`); not exploitable today (Bearer auth, no cookies), tighten when convenient. (#386)
- [ ] **ESLint config missing:** `cd frontend && npm run lint` fails (no config file). Also: sync bot calls inside async routes block the API while an order is placed (needs a `TradingBot` thread-safety review); `api/middleware/rate_limiter.py` is dead code. (#386)
- [ ] **Remaining advisories:** nltk 3.10.3 PYSEC-2026-3740 (via textblob, no fix published); vite 5 → 8 (dev server only) and react-router-dom 6 → 7 are majors, do separately. `mobile/` has no lockfile and wasn't audited. `.github/workflows/*` action versions weren't reviewed (no `workflow` scope). (#387)

## Next step: post-merge host steps from the 2026-09-25 security review

Merged 2026-09-25: [#382](https://github.com/Curt-Alfrey-s-Org/market-pie5-bot/pull/382) (admin JWT on control endpoints, frontend API key removed, `JWT_SECRET` required, LiteLLM wired), [#383](https://github.com/Curt-Alfrey-s-Org/market-pie5-bot/pull/383) (settings key masking, runtime env, Alembic, CI, docs), [#384](https://github.com/Curt-Alfrey-s-Org/market-pie5-bot/pull/384) (admin-only asset upload, authenticated probe scripts, stale `api/static` dropped). Do these before the Jul 2026 "Current step" work below. Placeholders only; real values go in `.env` (reference: [ENV_VARS.md](ENV_VARS.md), `env.required.example`).

- [ ] **Rotate `BOT_API_KEY`** (was in the public frontend bundle, `scripts/run_selftest_subdomain_trail.sh` and `docs/SECRETS_MANAGEMENT.md`; still in git history). (#382)
- [ ] **Change the password of the admin/director account** that was hardcoded in `scripts/run_selftest_subdomain_trail.sh` / the `scripts/verify_ports_and_health.sh` fallback. (#382)
- [ ] **Update `.env`** (copy the new entries from `env.required.example`):
  - [ ] `JWT_SECRET` (`openssl rand -hex 32`); the API won't start in production without it and existing sessions are invalidated. If `JWT_SECRET_KEY` is also set, make it agree (a mismatch logs a warning). (#382, #383)
  - [ ] `ADMIN_USERNAME` / `ADMIN_PASSWORD`, or make sure DB users exist (built-in defaults are gone). (#382)
  - [ ] `LITELLM_API_KEY` for the brain (`http://192.0.2.30`) with `LITELLM_ENABLED=true`; otherwise the bot refuses to start while `BOT_REQUIRE_BRAIN=true`. (#382)
  - [ ] Remove `VITE_API_KEY`. Keep third-party API keys in `.env` only (now masked in `/api/settings`). (#382, #383)
  - [ ] Optional: `BOT_RUNTIME_ENV_FILE=/app/data/runtime.env` so GUI mode/settings survive restarts. (#383)
- [ ] **⚠ Decide before rebuilding:** the rebuild copies `web_scrapers/` into the API image, so the **earnings, macro, sentiment, options-flow and news filters become active in the live bot** (they silently fell back to "no filter" until now). (#383)
- [ ] **Rebuild + recreate:** `docker compose --env-file .env up -d --build` (frontend without the API key; API image without the stale `api/static` UI). (#382, #383, #384)
- [ ] **Database:** `alembic upgrade head` (safe), or `alembic stamp head` if the schema already exists. (#383)
- [ ] **Operator scripts** (`run_selftest_subdomain_trail.sh`, `probe_all_modes.sh`, `monitor_bot.py`, `yfinance_long_run.py`, `yfinance_mode_optimizer.py`, `latency_probe.py`, `load_test_probe.py`): set `MARKET_BOT_ADMIN_TOKEN`, or `MARKET_BOT_ADMIN_USERNAME` / `MARKET_BOT_ADMIN_PASSWORD`. (#382, #383, #384)
- [ ] **GUI:** asset uploads and firewall toggles now need an admin login. `api/static/` is untracked; only if you relied on the API port serving the UI outside Docker: `cd frontend && npm run build`, copy `dist/` to `api/static/`. (#383, #384)
- [ ] **Smoke + tests:** startup self-test, admin login, bot starts with the brain reachable. GitHub Actions hasn't run since 2026-09-06: run `pytest tests/backend` locally; 2 pre-existing trading failures are expected (`test_exit_prices`, `test_short_cover_exit_prices`). (#383, #384)

Open / deferred:

- [ ] The 2 failing trading tests above (trading logic intentionally untouched). (#383)
- [ ] Security Scan workflow was already failing before these PRs. (#383)
- [ ] Importing `api.main` runs `internet_access_control` (`sudo iptables`), pre-existing. (#382)

---

## Current step (Jul 2026)

**Where we are:** The **ALFa AI brain as the only AI provider** objective is
**complete** (runtime, docs, and test suite). The repo is back on the main
product track: **Phase 1 stocks → live production** via the validation/sandbox/live
gate in [../PRODUCTION_READINESS_CHECKLIST.md](../PRODUCTION_READINESS_CHECKLIST.md).

**Next work (in order):**

1. **P1 production hardening** — structlog rollout, dependency pinning, backup
   restore drill, retry/resilience audit (see **Production Readiness Plan** below).
2. **P0 real-money gate** — finish 30-day paper validation, Schwab sandbox E2E,
   gradual live rollout (operator-driven; not blocked on code).
3. **P2 toolchain EOL** — Vite 5→7/8, ESLint 8→9 (after server is stable).

**AI consolidation detail:** [ML_AND_AI_ARCHITECTURE.md](ML_AND_AI_ARCHITECTURE.md)
§ *Implementation status (Jul 2026)* and **Known issues / deferred work** below.

---

## Known issues / deferred work (Jul 2026)

Issues found during the Jul 2026 AI consolidation and test purge. None block
deploy; fix when touching the related area.

| ID | Area | Issue | Suggested fix | Priority |
|----|------|-------|---------------|----------|
| **K1** | Tests / validation | `test_env_validation_enhancements.py::test_placeholder_detection_alpha_vantage` **fails**. Test expects a placeholder `ALPHA_VANTAGE_API_KEY` to make `validate_configuration()` return invalid; runtime treats it as a **non-fatal warning** ("fundamental data features limited"). Pre-existing; unrelated to AI migration. | Either relax the test to assert warning-only behavior, or make placeholder Alpha Vantage keys a hard validation failure again in `main.py`. | P3 |
| **K2** | Tests / sentiment | `test_sentiment_analyzer.py` fails on **Python 3.14** when VADER is initialized: `DeprecationWarning` from `vaderSentiment` (`codecs.open`) is promoted to error by `pytest.ini` `filterwarnings = error::DeprecationWarning`. Failure reproduces **without** brain-sentiment changes (stash test). | Pin CI/dev to Python 3.12 (matches Dockerfile), or narrow `filterwarnings`, or mock VADER in unit tests. Brain path reduces reliance on VADER over time. | P3 |
| **K3** | Tests / pytest | Default `pytest.ini` `addopts` includes `--cov`; local venv may lack `pytest-cov` → `pytest` exits with "unrecognized arguments". Workaround: `pytest -o addopts="" …`. | Add `pytest-cov` to dev requirements or make coverage opt-in in `pytest.ini`. | P3 |
| **K4** | Tests / integration | `test_encrypted_api_key_integration.py::test_encrypted_api_key_flow` returns `bool` instead of using `assert` → `PytestReturnNotNoneWarning`. | Refactor to pure assert-based test or mark as script-only. | P3 |
| **K5** | Docs / host drift | [REPO_HOST_MAPPING.md](REPO_HOST_MAPPING.md) lists market-pie5-bot on **``**; several docs still say deploy from **``** ([ML_AND_AI_ARCHITECTURE.md](ML_AND_AI_ARCHITECTURE.md), [ENV_VARS.md](ENV_VARS.md), [ALFA_AI_HOW_TO_USE.md](ALFA_AI_HOW_TO_USE.md)). | Reconcile deploy runbooks to `` (or document dual-host transition). | P3 |
| **K6** | Repo hygiene | Untracked on disk (not in git): `SCHWAB_API_SETUP_GUIDE.md`, `validate_schwab_api.py`. | Review, move to `docs/` / `scripts/`, commit or gitignore. | P3 |
| **K7** | AI / parity | P3 item **LiteLLM client parity check** vs `rankings-bot` still open. | Diff `api/services/litellm_client.py` against workspace reference; align async httpx + degrade behavior. | P3 |

**Intentionally kept (not bugs):**

- `test_comprehensive_rate_limiting.py::test_ml_optimizer_no_huggingface_rate_limiter` — regression guard that `MLParameterOptimizer` has no `hf_api_limiter` after migration.
- `api/services/error_monitor.py` — `HUGGINGFACE_*` log-redaction pattern (legacy env values in old logs).

---

## Backlog — AI inline doc references (apply later)

Mirror **rankings-bot**: hub docs + `Doc refs (AI / maintainers)` on auth, trading pipeline, deploy. **Reference:** `../rankings-bot/docs/AI_INLINE_DOC_REF_PROCESS.md`.

---

## Current Priority

- [x] **ALFa AI as the only AI provider** — Ollama removed, HuggingFace removed,
  sentiment via brain (VADER fallback), local ML factors in narratives (read-only).
  Commits: `09bd4b4`, `2c54666`, `9bb0ae3` (Jul 2026). See
  [ML_AND_AI_ARCHITECTURE.md](ML_AND_AI_ARCHITECTURE.md).
- [ ] **Drive Phase 1 (stocks) to live production** — complete the validation→sandbox→live gate
  in [../PRODUCTION_READINESS_CHECKLIST.md](../PRODUCTION_READINESS_CHECKLIST.md) and close the
  P0/P1 items in the **Production Readiness Plan** below. React Native (Expo) work resumes after
  the server is production-grade — see
  [PRODUCTION_READINESS_AND_REACT_NATIVE.md](PRODUCTION_READINESS_AND_REACT_NATIVE.md) §3,
  noting much of its §1 server checklist is now **done** (see drift note below).

---

## Production Readiness Plan — June 2026 audit refresh

**State as of 2026-06-09:** stack healthy (postgres / api / frontend containers up 27h, all
`healthy`; `/api/health` reports `startup_status.initialized: true`). FastAPI lifespan pattern in
`api/main.py`, SQLAlchemy 2 + Alembic (6 migrations), pydantic-settings, slowapi rate limiting,
`/api/v1/` versioned routes **implemented** (`api/routes/v1/`), token refresh endpoint
**implemented** (`api/routes/auth.py`), Postgres backup/restore scripts **implemented**
(`scripts/backup_postgres.sh`, `scripts/restore_postgres.sh`), `stop_grace_period: 30s` set.
25 backend test files + self-test framework (`tests/runner.py`).

**Doc/code drift to resolve:** [PRODUCTION_READINESS_AND_REACT_NATIVE.md](PRODUCTION_READINESS_AND_REACT_NATIVE.md)
(Feb 2026) still lists Gaps 1, 6, 7, A and C as open although they are implemented — mark them
done in that doc so this roadmap stays the single source of truth.

**Immutable networking constants** (workspace `.cursorrules`): network `tunnel_network`, API
publish `127.0.0.1:8004:8000`, nginx `proxy_pass http://market-pie5-bot-api:8000/...`, frontend
`5176`. Nothing in this plan may change them.

### P0 — Production blockers (real-money gate)

- [ ] **Finish Phase A 30-day paper validation** and record the metrics defined in
  `../PRODUCTION_READINESS_CHECKLIST.md` (uptime, earnings-filter hits, stale-position alerts,
  P&L). No live capital until A and B sign-off.
- [ ] **Phase B: Schwab sandbox end-to-end** — real Schwab API with `SCHWAB_SANDBOX_MODE=true`:
  OAuth token lifecycle (refresh, expiry, re-auth), order placement/cancel, error taxonomy
  (transient vs permanent). schwab-py docs: https://schwab-py.readthedocs.io/
- [ ] **Phase C: gradual live rollout** — flip `PAPER_TRADING_MODE=false` only behind the
  documented go-live checklist; smallest position sizes first; daily reconciliation of bot state
  vs Schwab account.
- [x] **Upgrade off `python:3.10-slim`.** *(Done 2026-06-09: Dockerfile now `python:3.12-slim`;
  image builds clean (pydantic 2.13 / SQLAlchemy 2.0.50 / pandas 3.0 all install on 3.12); all
  `datetime.utcnow()` deprecations fixed via `api/utils/timeutils.py`; full backend suite green
  on Python 3.12. Live container intentionally NOT redeployed — operator deploys on next window.)*
- [x] **Fix the passlib/bcrypt incompatibility (auth root cause).** *(Done 2026-06-09: migrated to
  `pwdlib[argon2,bcrypt]` per the FastAPI security tutorial; Argon2 primary hasher, bcrypt legacy
  verify with `verify_and_update()` transparent re-hash on login (`verify_and_update_password` /
  `verify_db_user_password` in `api/auth.py`); passlib + bcrypt pin removed from requirements;
  tests cover new-hash, legacy-verify and re-hash paths in `tests/backend/test_password_hashing.py`.)*

### P1 — Hardening & ops

- [ ] **Backup restore drill + offsite copy.** Scripts exist; restore has no documented test.
  Quarterly restore-into-scratch-container drill; verify cron is actually installed on ``;
  consider retention policy in [POSTGRES_BACKUPS.md](POSTGRES_BACKUPS.md).
- [ ] **Finish structured logging rollout.** `structlog` is a dependency but only
  `api/routes/logs.py` uses it; the rest of the API logs unstructured. Standardize on structlog
  JSON renderer app-wide so the central monitoring stack (Loki/Alloy) can parse fields.
  structlog docs: https://www.structlog.org/
- [ ] **Retry/resilience audit (Gap 2 remainder).** Verify every yfinance/Schwab call path goes
  through the retry helper with transient/permanent distinction; add failure-injection tests
  (kill network mid-cycle) to `tests/`.
- [ ] **Pin production dependency versions.** Open-ended `>=` ranges in `requirements.txt` mean
  rebuilds silently change versions. Generate a constraints/lock file consumed by the Dockerfile
  (https://pip.pypa.io/ trim unused heavyweight deps
  (dash, matplotlib, backtrader if not exercised by the API image).
- [ ] **psycopg2-binary → psycopg 3** (or source-built psycopg2) for production, per psycopg
  install docs (https://www.psycopg.org/ SQLAlchemy 2
  supports the `postgresql+psycopg` dialect natively.
- [ ] **Data archival (Gap 3) decision.** Either implement the `data_archives` snapshot table from
  the production-readiness doc or explicitly descope it — don't leave it half-specified.

### P2 — Supported-version upgrades (frontend toolchain is EOL)

- [ ] **Vite 5.0.8 → 7/8.** Per https://vite.dev/releases (June 2026) only `vite@8.0`, `7.3` and
  `6.4` receive any patches — Vite 5 is unsupported. Migrate via the official guides
  (https://vite.dev/guide/migration); Vite 7+ requires Node 20.19+/22.12+.
- [ ] **ESLint 8.55 → 9 (flat config).** ESLint v8 reached EOL 2024-10-05
  (https://eslint.org/version-support/); typescript-eslint v6 is similarly out of support —
  move to typescript-eslint v8 like rankings-bot already did (cross-repo parity).
- [x] **Remove obsolete `version: '3.8'` from `docker-compose.yml`.** *(Done 2026-06-09: key
  removed; ports/networks untouched — byte-for-byte identical otherwise.)*
- [ ] **React Router v6 / TanStack Query major review** during the Vite bump (React Router 7 is
  the supported line: https://reactrouter.com/upgrading/v6).

### P3 — Repo hygiene & doc drift

- [ ] **Clean the repo root.** ~8,400 entries at repo root: hundreds of one-off session/analysis
  MD files, ad-hoc `check_*.py` / `debug_*.py` / `deploy_*.py` scripts, logs, backtest JSON, and
  state files. Move historical docs to `docs/archive/`, scripts to `scripts/` or delete, gitignore
  generated artifacts (`bot_state.json` runtime copy, logs, coverage.xml). This is the single
  biggest maintainability risk in the repo.
- [x] **Mark closed gaps in PRODUCTION_READINESS_AND_REACT_NATIVE.md** (Gaps 1, 6, 7, A, C) and
  date the doc — drift control per workspace `engineering-standards-and-drift-control.mdc` §5.
  *(Done 2026-06-09: each gap verified in code first — v1 routes, refresh endpoint, backup/restore
  scripts, `stop_grace_period: 30s` — then marked done with implementation pointers; cron install
  and restore drill remain open as P1 above.)*
- [ ] **LiteLLM client parity check.** `api/services/litellm_client.py` must keep the same shape
  as the workspace reference `rankings-bot/api/services/litellm_client.py` (async httpx, graceful
  degrade — primary trading path must never block on AI, telemetry logging). Brain stays at
  `http://192.0.2.30` via aliases; no direct cloud-LLM calls.

---

### Phase 5: ALFa AI consolidation (alfa-ai only) ✅

**Completed Jul 2026** on branch `main` (authoring host: `` clone;
deploy consumer: `` per [REPO_HOST_MAPPING.md](REPO_HOST_MAPPING.md)).

| Milestone | Commit | Summary |
|-----------|--------|---------|
| Remove Ollama/HF; brain-only LLM path | `09bd4b4` | Deleted `ollama_client.py`; shared `LLMResponse` in `llm_types.py`; docs/env updated |
| Local ML → brain context | `2c54666` | `get_decision_factors_summary()` + narrative/journal enrichment |
| Test suite HF purge | `9bb0ae3` | Repointed encryption tests to `NEWS_API_KEY`; removed dead `web_gui` refs |

Deferred issues: see **Known issues / deferred work** at top of this doc (K1–K7).

---

## Completed Phases

### Phase 1: Foundation ✅

- BUY/SELL (long), SHORT/COVER; unified position model with `side`
- Strategies: SMA, Bollinger, RSI, MACD, Momentum; signal→action mapping
- Risk: PDT, T+1, margin/short-availability, capital floor, trailing stops

### Phase 2: yfinance Mode ✅

- yfinance mode for training/validation; sandbox fallback when Schwab fails
- Logs & dashboard, Decision Report, OHLCV cache, throttler, self-test

### Phase 3: Integration ✅

- ML Signal Filter + Portfolio Optimizer integrated
- Adaptive Learning (Q-Learning, Multi-Armed Bandit)
- Comprehensive self-test framework (`tests/runner.py`)

### Phase 4: Web GUI & Production ✅

- React + FastAPI dashboard; login, Settings, System, Logs
- Docker Compose, Nginx; paper/sandbox/live modes

---

## Planned / Future

### High Priority

| Item | Status | Notes |
|------|--------|-------|
| Server production gaps | In progress | Startup recovery, retry, persistence, resilience, secrets, backups |
| Mobile API readiness | Planned | Versioning, error responses, token refresh |
| React Native app | Planned | Expo, iOS/Android; Phase A–E |

### Medium Priority

| Item | Status | Notes |
|------|--------|-------|
| Options trading (Phase 2) | Planned | After Phase 1 stocks production-ready |
| Extended paper/sandbox runs | Planned | 30+ days with buy+short |
| Runbooks | Planned | Deployment, config, common failures |

### Features & Improvements (backlog)

| Area | Item |
|------|------|
| Trading | Confirm Schwab short-selling support; buy-in risk handling |
| Ops | Basic failure testing (API outages, network blips) |
| Docs | Mission/phases linked; short-selling design documented |
| Mobile | PWA-first option before native |

### Tech Debt

- Consolidate duplicate PROJECT_ROOT definitions across routes
- Standardize error handling (timeouts, retries) per project rules
- Audit GitHub Copilot edits (README, demo_*.py, docstrings)
- Remove/fix `tool_cat.py` if present in wrong location

---

## References

- [MISSION.md](../MISSION.md) — Phase 1 (stocks) vs Phase 2 (options)
- [PRODUCTION_READINESS_AND_REACT_NATIVE.md](PRODUCTION_READINESS_AND_REACT_NATIVE.md) — Server, mobile API, React Native
- [YFINANCE_OPERATIONS.md](YFINANCE_OPERATIONS.md) — yfinance mode operations
- [INTEGRATION_ANALYSIS.md](INTEGRATION_ANALYSIS.md) — Integration status
- [CONTRIBUTING.md](../CONTRIBUTING.md) — Dev setup and PR guidelines
