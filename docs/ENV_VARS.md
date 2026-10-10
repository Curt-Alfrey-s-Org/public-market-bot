# Environment Variables — market-pie5-bot ALFa AI integration

Authoritative reference for the ALFa AI / LiteLLM and error-monitoring
environment variables. For the full application `.env`, see `.env.example`.

> **Single source of truth:** the LiteLLM proxy contract (OpenAI-compatible
> `/v1/chat/completions`, `/v1/embeddings`, virtual keys) follows the official
> LiteLLM proxy docs: <https://docs.litellm.ai/docs/proxy/quick_start>. Model
> alias names are owned by `alfa-ai/deploy/litellm_config.yaml` on ``.

## Topology

market-pie5-bot runs on **``**. The ALFa AI brain (LiteLLM proxy +
orchestrator) runs on **``**. All inference goes over the LAN to
`http://192.0.2.30`. The Docker DNS name `alfa-ai-litellm:4000` is **not**
resolvable from `` — do not use it here.

## LLM insights (narrative only — not parameter tuning)

| Variable | Default | Purpose |
|----------|---------|---------|
| `BOT_LLM_INSIGHTS_ENABLED` | `true` | When `true`, enable LLM narratives (performance summary, trade journal, optional optimization *explanation*). Does not affect backtest heuristic optimizer. |

Parameter **values** come from `ml_param_optimizer` (backtest heuristics), not from the LLM.

## LiteLLM (brain connectivity + AI features)

| Variable | Default | Purpose |
|----------|---------|---------|
| `LITELLM_ENABLED` | `false` in code, **`true` in `docker-compose.yml`** | Master switch for brain LLM features (narratives, triage, Ask AI). When `false`, LLM features are unavailable. With default `BOT_REQUIRE_BRAIN=true`, the trader also **will not run** (disabled brain counts as down). |
| `LITELLM_BASE_URL` | `http://192.0.2.30` | LiteLLM proxy URL (LAN to brain). |
| `LITELLM_API_KEY` | (none; env only) | Bearer key. There is no shared default. Set it to this bot's LiteLLM virtual key (or `LITELLM_MASTER_KEY` from `alfa-ai/deploy/.env` on ``). Required to start the bot while `BOT_REQUIRE_BRAIN=true`. |
| `LITELLM_MODEL_CHAT` | `app-chat` | Default chat alias for signed-in AI features. |
| `LITELLM_MODEL_PAGE_QUESTION` | (falls back to `LITELLM_MODEL_CHAT`) | Alias for the per-page Ask AI narrative route. |
| `LITELLM_MODEL_INTERNAL` | `code` | Alias for internal/admin triage (error explain, log triage). |
| `LITELLM_TIMEOUT` | `600` | Request timeout (seconds). The CPU MoE fleet can be slow on cold start. |
| `LITELLM_API_KEY_APP` | (falls back to `LITELLM_API_KEY`) | Optional separate key for the `app_authenticated` trust zone. |
| `LITELLM_API_KEY_INTERNAL` | (falls back to `LITELLM_API_KEY`) | Optional separate key for the `internal` (admin) trust zone. |

Required model aliases on the brain: `app-chat`, `code`, `embed` (and `agent`
for orchestrator jobs). Verify with:

```bash
curl -fsS http://192.0.2.30/v1/models -H "Authorization: Bearer $LITELLM_API_KEY"
```

## Trading gate — require the brain (hard dependency)

By default the trader **will not run unless the ALFa AI brain is reachable**.
The `/start` endpoints return **HTTP 503** when the brain is down, and a running
loop **halts** if the brain becomes unreachable mid-run. A brain that is
disabled (`LITELLM_ENABLED=false`) counts as "down" for this gate.

| Variable | Default | Purpose |
|----------|---------|---------|
| `BOT_REQUIRE_BRAIN` | `true` | When `true`, the trading loop refuses to start and halts mid-run if the brain (LiteLLM `/health/liveliness`) is unreachable. Set `false` to restore graceful-degrade behavior (bot trades without the brain). |
| `BOT_BRAIN_CHECK_INTERVAL_SECONDS` | `60` | How often the running loop re-probes brain health. `0` disables mid-run re-checks (start-time gate still applies). |
| `BOT_BRAIN_CHECK_TIMEOUT_SECONDS` | `10` | Timeout for each liveliness probe. |

### Compose wiring and startup errors (2026-09-25)

`docker-compose.yml` now passes `BOT_REQUIRE_BRAIN`, `LITELLM_ENABLED` (default
`true`), `LITELLM_BASE_URL` (default `http://192.0.2.30`),
`LITELLM_API_KEY` (from the env only, no default), the optional per-zone keys and
the model/timeout settings to the API container. Before this the container had no
LiteLLM settings, so the brain counted as disabled and `BOT_REQUIRE_BRAIN=true`
blocked every start. No override compose file exists in the repo.

If the brain is required but not configured, the API logs at startup (and
`/api/bot/start` returns 503 with) a message naming the variable, e.g.:

```
Bot cannot start: BOT_REQUIRE_BRAIN=true but the ALFa AI brain (LiteLLM at http://192.0.2.30)
is not configured: LITELLM_API_KEY is not set (set it to this bot's LiteLLM key). ...
```

> Note: trade *decisions* are made by deterministic strategies + local ML, not
> the brain. This gate is an operator policy choice to refuse trading when the
> AI brain (advisory/monitoring layer) is unavailable.

## Authentication and secrets (security review 2026-09-25)

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENVIRONMENT` | `production` (compose and code) | `development`/`dev`/`test`/`testing`/`local` relax the `JWT_SECRET` requirement; anything else is production. |
| `JWT_SECRET` | **none: required in production** | Signs web and mobile session tokens (`JWT_SECRET_KEY` accepted as a legacy alias; one secret for both). Missing or old public placeholder value → API exits at startup with `CONFIGURATION ERROR: JWT_SECRET ...`. Generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"`. |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | none | Env admin account; exists only when both are set (no `admin/admin123` fallback). Same for `DIRECTOR_*` and `USER_*`. |
| `BOT_API_KEY` | none (required) | Server-to-server `X-API-Key` for scripts/monitoring (read endpoints). Admin control endpoints ignore it. Never pass it to the frontend. |
| `VITE_API_KEY` | **removed** | No longer read; delete it from `.env`. The browser uses the logged-in user's JWT. |
| `MARKET_BOT_ADMIN_USERNAME` / `MARKET_BOT_ADMIN_PASSWORD` | none | Admin login used by the operator scripts (`scripts/run_selftest_subdomain_trail.sh`, `probe_all_modes.sh`, `monitor_bot.py`, `yfinance_long_run.py`, `yfinance_mode_optimizer.py`). |
| `MARKET_BOT_ADMIN_TOKEN` | none | Admin JWT for the same scripts, used instead of logging in (preferred over username/password when set; not used by `run_selftest_subdomain_trail.sh`). Treat it like a password. |
| `BOT_RUNTIME_ENV_FILE` | unset | Where the API saves runtime mode/settings changes (`POST /api/bot/mode`, `PUT /api/settings`). In Docker set it to a file on a mounted volume, e.g. `/app/data/runtime.env`. The file is created with mode 600 and only holds the keys the API writes. If unset in a container, nothing is written and changes last until the API restarts. On a host install (not in a container) the default is the project `.env`, as before. |
| `RUNNING_IN_CONTAINER` | auto (`/.dockerenv`) | Overrides container detection for the rule above (`true`/`false`). |
| `JWT_SECRET_KEY` | legacy alias | Read only if `JWT_SECRET` is unset. If both are set to different values, `JWT_SECRET` is used and a warning is logged. |

Third-party API keys (`SCHWAB_APP_KEY`, `SCHWAB_SECRET_KEY`, `HUGGING_FACE_API_KEY`,
`ALPHA_VANTAGE_API_KEY`, `NEWS_API_KEY`, `FINNHUB_API_KEY`) are never returned by
`GET /api/settings` (shown as `********` when set) and can't be written through the
Settings API. Set them in `.env`.

See [LOGIN_AUTH.md](LOGIN_AUTH.md) for which endpoints need an admin session.
Placeholders for everything above are in `env.required.example` at the repo root.

## Automatic error monitoring (alfa-ai triage)

| Variable | Default | Purpose |
|----------|---------|---------|
| `ERROR_MONITOR_ENABLED` | `true` | Capture runtime errors, persist to `error_events`, and run background triage. Requires `LITELLM_ENABLED=true` for the triage step (capture still works without it). |
| `ERROR_MONITOR_INTERVAL_SECONDS` | `300` | Seconds between background triage batches. |
| `ERROR_MONITOR_BATCH_SIZE` | `10` | Max `pending` errors triaged per batch. |

## ALFa orchestrator (agentic jobs — Stage 6)

| Variable | Default | Purpose |
|----------|---------|---------|
| `ALFA_AI_API_URL` | `http://192.0.2.30` | ALFa orchestrator API (LAN). |
| `ALFA_AI_API_TOKEN` | (unset) | Bearer token required when `ALFA_AI_REQUIRE_API_AUTH=true` on the brain. |

## Opt-in fine-tune capture (Stage 8)

Disabled by default. When enabled, redacted `(prompt -> completion)` pairs are
stored in `finetune_samples`. Export/purge with
`scripts/finetune/export_finetune.py`.

| Variable | Default | Purpose |
|----------|---------|---------|
| `FINETUNE_CAPTURE_ENABLED` | `false` | Master switch for capture. |
| `FINETUNE_RETENTION_DAYS` | `30` | Days before captured samples are purged. |

## Removed: direct Ollama fallback

The direct-Ollama client (`OLLAMA_ENABLED`, `OLLAMA_BASE_URL`,
`OLLAMA_MODEL_CHAT`, `OLLAMA_TIMEOUT`) has been **removed**. The ALFa AI brain is
the single AI provider; if you need a local model, expose it through the brain's
LiteLLM proxy (a `litellm_config.yaml` alias on ``) rather than a second
direct client in this repo. The LLM telemetry table remains named
`ollama_activity_log` for schema continuity (historical name; it logs every
LiteLLM/brain call).

## Removed: HuggingFace

The HuggingFace cloud LLM path has been **fully removed** (no
`HUGGINGFACE_API_KEY`, `HUGGINGFACE_MAX_CALLS_PER_MINUTE`, or
`HUGGINGFACE_TIME_WINDOW_SECONDS`). LiteLLM on the ALFa AI brain is the only
runtime LLM path. Local ML (scikit-learn signal filter, sentiment analyzer,
Q-learning) is unchanged and uses no external LLM API; its outputs are fed to
the brain as context (see [ML_AND_AI_ARCHITECTURE.md](ML_AND_AI_ARCHITECTURE.md)).

## Apply env changes (recreate container)

`docker compose restart` does **not** reload `.env`. Recreate the API container:

```bash
cd /home/operator/market-pie5-bot
docker compose --env-file .env up -d --no-deps --force-recreate market-bot-api
curl -fsS http://127.0.0.1:8004/api/health/detailed | jq '.litellm'
```
