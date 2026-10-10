# Agent Instructions — market-pie5-bot

market-pie5-bot is a FastAPI backend (`api/main.py`, host `127.0.0.1:8004` →
container `8000`), a monolithic `TradingBot` (`main.py`), a React/Vite frontend
(`frontend/`), and an Expo mobile app (`mobile/`). It runs on ``.

## ALFa AI integration (ML + monitoring)

All LLM inference goes through the **ALFa AI brain (LiteLLM)** on ``. The
legacy HuggingFace cloud path has been **removed**.

- LiteLLM proxy: `http://192.0.2.30` (OpenAI-compatible
  `/v1/chat/completions`, `/v1/embeddings`).
- Orchestrator (agentic jobs): `http://192.0.2.30` (`POST /api/runs`).
- Client: `api/services/litellm_client.py` (async `LiteLLMClient` for routes;
  `litellm_chat_completion_sync` / `litellm_embeddings_sync` for the sync
  `TradingBot`). Telemetry → `ollama_activity_log`.
- Model aliases (owned by `alfa-ai/deploy/litellm_config.yaml`): `app-chat`
  (signed-in features), `code` (internal/dev/triage), `embed` (RAG),
  `agent` (orchestrator jobs).
- Env: see `docs/ENV_VARS.md`. Master switch `LITELLM_ENABLED`.

### Hard rules

1. **Graceful degrade (AI narratives):** If the brain is unreachable, LLM narratives fail with an error object; local ML and strategies continue. **Exception:** when `BOT_REQUIRE_BRAIN=true` (default), the **trading loop** refuses to start / halts — see `BOT_REQUIRE_BRAIN` in `docs/ENV_VARS.md`.
2. **No financial advice**: user-facing AI (Ask AI, jobs) is factual narration
   only and must carry the `NOT FINANCIAL ADVICE` disclaimer (enforced in
   `api/routes/ai_narrative.py` and `ai_jobs.py`).
3. **Trust boundary**: never send Schwab tokens, balances, account numbers, or
   API keys to the brain. Context is sanitized in
   `api/services/market_ask_ai_context.py`; error captures are redacted in
   `api/services/error_monitor.py`. Add new sensitive patterns there.
4. **Local ML stays local**: scikit-learn signal filter
   (`ml_signal_filter.py`), VADER/TextBlob sentiment (`sentiment_analyzer.py`),
   and Q-learning use no external LLM — do not route them through LiteLLM.
5. **LLM does not tune parameters**: `ml_param_optimizer.py` uses backtest
   heuristics only. Use `api/services/trading_insights_llm.py` for narratives
   (performance summary, trade journal, optional explanation of heuristic
   changes). Never parse LLM JSON for auto-applied settings.

### What the LLM is for

| Use | Module / route |
|-----|----------------|
| Ask AI dock | `api/routes/ai_narrative.py` |
| Performance narrative | `trading_insights_llm`, `POST /api/ai/request` |
| Trade journal | `POST /api/ai/journal` |
| Error triage | `error_monitor` + `code` model |
| Agentic reports | `api/routes/ai_jobs.py` |
| RAG / embeddings | `market_rag`, `embed` |
| Dev / CI | `scripts/codegen`, `ai-pr-triage.yml` |

### What is NOT the LLM

| Use | Method |
|-----|--------|
| Parameter suggestions | `ml_param_optimizer` backtest heuristics |
| Trade signals | Strategies + local ML |

## Error monitoring

Unhandled errors are captured by `api/middleware/error_handler.py` →
`error_monitor.record_error`, deduplicated into `error_events`, and triaged in
the background via LiteLLM `code`. Admin view: `/admin/ai-monitor`
(`frontend/src/pages/SettingsInternalAIMonitor.tsx`). API:
`/api/admin/ai-monitor/*` (admin-only).

## Infra constants (do NOT change)

- Port mapping `127.0.0.1:8004:8000`, network `tunnel_network`, container DNS
  names (workspace `.cursorrules`). Container binds `0.0.0.0`; host binds
  loopback for APIs.
- Production runs under one process owner (systemd) — see
  `.cursor/rules/deployment-process-ownership.mdc`.

## Workflow

- Author edits on ``; commit/push from ``; other hosts `git pull`.
- Run startup self-tests after changes (`.cursor/rules/run-selftest-after-changes.mdc`).
- Apply env changes by recreating the container (compose `restart` does not
  reload `.env`).
