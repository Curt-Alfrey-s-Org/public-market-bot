# ALFa AI — how to use (market-pie5-bot)

Operator and product guide for ALFa AI integration on **market-pie5-bot** (``, `/home/operator/market-pie5-bot`). Follow staged rollout in `.cursor/plans/ALFA_AI_INTEGRATION_PLAN.md`.

**Architecture (what changed & why):** [ML_AND_AI_ARCHITECTURE.md](ML_AND_AI_ARCHITECTURE.md)

**Related:** `docs/ALFA_AI_TRUST_ZONES_AND_ROLLOUT.md` · `docs/ENV_VARS.md` · `/home/operator/.cursor/plans/ALFA_AI_INTEGRATION_PLAN_HOST_105.md` (host service contract) · `alfa-ai/docs/DEPLOYMENT_BASELINE.md` · `rankings-bot/docs/ALFA_AI_MULTI_JOB_ROLLOUT.md` (cluster preflight jobs)

---

## Where the brain lives

market-pie5-bot runs on **``**. The ALFa AI brain (LiteLLM, orchestrator API, operator console) runs on **``**. All LiteLLM and orchestrator calls go over the LAN to `192.0.2.30`. The Docker DNS name `alfa-ai-litellm:4000` is **not** resolvable from `` — do not use it here.

> **HuggingFace is fully removed.** There is no `HUGGINGFACE_API_KEY` and no
> `router.huggingface.co` path. LiteLLM on the brain is the only runtime LLM
> path. Local ML (scikit-learn signal filter, VADER/TextBlob sentiment,
> Q-learning) is unchanged and uses no external LLM API. Automatic error
> monitoring captures unhandled errors to `error_events` and triages them in the
> background via the `code` model (admin AI Monitor surfaces the results).

---

## What you can run

| Capability | Who | Where | Inference |
|------------|-----|-------|-----------|
| **Ask AI dock** | Signed-in users | Decision Report, Dashboard, Trades, Pending Trades, Settings → `POST /api/ai/ask` | `app-chat` via LiteLLM when enabled (RAG-grounded) |
| **Legacy AI page** | Signed-in users | `/ai` → `POST /api/ai/request` (performance narrative only) | `app-chat` — factual summary, no auto-settings |
| **Trade journal** | Signed-in users | `POST /api/ai/journal` | `app-chat` — recent fills in plain English |
| **Param suggestions** | Signed-in users | `GET /api/ai/optimization-suggestions` | **Backtest heuristics** (not LLM); optional `?explain=true` for LLM explanation |
| **Auto-tune (batch)** | System | `main.py` when `BOT_ENABLE_AI_AUTO_TWEAK=true` | **Backtest heuristics only** — never LLM JSON settings |
| **Admin AI Monitor** | Admin only | `/admin/ai-monitor` → `GET /api/admin/ai-monitor/*` | Reads `ollama_activity_log` + `error_events` (auto-triage via `code`) |
| **Agentic jobs** | Admin / automation | `POST /api/admin/ai-jobs/{end-of-day-summary,anomaly-digest,sector-rotation}` → ALFa `POST /api/runs` on **`:8420`** | `agent` inside orchestrator (factual only) |
| **Dev codegen / CI** | Developers | `scripts/codegen/ai_codegen.py`, `.github/workflows/ai-pr-triage.yml` | `code` via LiteLLM |

market-pie5-bot does **not** expose a public unauthenticated demo endpoint (no USPBF-style `demo-ask`). All runtime AI is **`app_authenticated`** or **`internal`**.

**Trading disclaimer:** Ask AI on Trades, Pending Trades, Decision Report, and Dashboard pages includes a **NOT FINANCIAL ADVICE** footer on every response. Ask AI does not place orders — use the bot controls and Pending Trades approval flow for execution.

---

## Prerequisites on the ALFa cluster

1. **LiteLLM** healthy on brain host: `curl -fsS http://192.0.2.30/health/liveliness`.
2. **Model aliases** exist in `alfa-ai/deploy/litellm_config.yaml` — at minimum: `app-chat`, `code`, `embed`.
3. **ALFa API** healthy: `curl -fsS http://192.0.2.30/health` when using orchestrator jobs.
4. **UFW on ``** allows `192.0.2.21/24 → 8413, 8420` (recipe in `alfa-ai/docs/PORT_ASSIGNMENTS.md`).
5. **Ollama** reachable from LiteLLM on `` for CPU MoE tier (`qwen3-coder:30b-a3b-q4_K_M` fleet).
6. Cluster preflight (run on brain):

```bash
ssh operator@192.0.2.30 'bash /home/operator/alfa-ai/scripts/alfa_ai_rollout_preflight.sh /home/operator/alfa-ai/deploy/.env'
```

---

## Enable LiteLLM in market-pie5-bot

Docker Compose loads `.env` from the repo root. Add to **`.env`** (see **`.env.example`**):

```env
LITELLM_ENABLED=true
LITELLM_BASE_URL=http://192.0.2.30
LITELLM_API_KEY=change-me
```

Use the **same bearer value** for **`LITELLM_API_KEY`** as **`LITELLM_MASTER_KEY`** in `alfa-ai/deploy/.env` on `` (change both to a strong secret in production, or issue a virtual key via the LiteLLM admin).

Recommended aliases (must exist in **`alfa-ai/deploy/litellm_config.yaml`**):

```env
LITELLM_MODEL_PAGE_QUESTION=app-chat
LITELLM_MODEL_CHAT=app-chat
LITELLM_TIMEOUT=600
```

Optional orchestrator (Stage 6+):

```env
ALFA_AI_API_URL=http://192.0.2.30
ALFA_AI_API_TOKEN=<long-random-secret>
```

Optional direct Ollama fallback when LiteLLM disabled (emergency only — not the cluster contract):

```env
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://192.0.2.30
OLLAMA_MODEL_CHAT=qwen3-coder:30b-a3b-q4_K_M
```

Legacy HuggingFace (superseded — disable in production once LiteLLM verified):

```env
# HUGGINGFACE_API_KEY=...  # remove or leave empty in production
```

### Apply env changes (recreate container)

**Important:** `docker compose restart market-bot-api` does **not** reload `.env`. Recreate:

```bash
cd /home/operator/market-pie5-bot
docker compose --env-file .env up -d --no-deps --force-recreate market-bot-api
```

For production with UID/GID overlay (if used):

```bash
docker compose --env-file .env --env-file .env.compose-host-user up -d --no-deps --force-recreate market-bot-api
```

---

## Verify market-pie5-bot → LiteLLM

From a shell on `` that can reach ``:

```bash
curl -fsS http://192.0.2.30/health/liveliness
curl -fsS http://192.0.2.30/v1/chat/completions \
  -H "Authorization: Bearer change-me" \
  -H "Content-Type: application/json" \
  -d '{"model":"app-chat","messages":[{"role":"user","content":"Say OK in one word."}]}'
```

After API integration (Stage 2+), with a valid JWT and API key:

```bash
TOKEN="change-me"
curl -fsS http://127.0.0.1:8004/api/ai-narrative/ask \
  -H "X-API-Key: ${BOT_API_KEY:?set BOT_API_KEY}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"page":"decision_report","player_name":"","question":"What does the Decision Report show for the top candidate symbol?","context":{}}'
```

In the app: sign in → open **Decision Report** → click **ALFa AI** dock (bottom-right) → ask about a symbol's signal or filter reason.

---

## AI Monitor

**Admin** users: **Settings → AI Monitor** (internal traffic and all LLM calls).

Calls routed through the narrative stack show **`trust_zone: app_authenticated`** in `ollama_activity_log.metadata`. Admin explain/triage features use **`internal`**.

---

## Domain-specific tips

- **Best questions on Decision Report:** "Why did the screener reject TSLA this cycle?", "Explain the difference between signal HOLD and action — for symbol X", "Summarize how many candidates passed volume filters today."
- **Best questions on Dashboard:** "Summarize today's win rate and P&L trend", "What mode is the bot running in and what does that mean?"
- **Best questions on Trades / Pending Trades:** "What exit reasons appear most often this week?", "Explain the reasoning block on pending trade ID …" — responses include the non-advice disclaimer; never treat as trade recommendations.
- **Best questions on Settings:** "What do MAX_STOCK_VOLATILITY and MIN_DAILY_VOLUME control?", "Explain paper vs sandbox vs live mode."
- **Screener data** comes from yfinance/Wikipedia universe in `stock_screener.py`; without network, Ask AI uses cached JSON under `data/` only.
- **Live trading** requires explicit operator confirmation (`api/routes/bot.py` start flow); Ask AI cannot start the bot or approve pending trades.

### Non-advice disclaimer (operator guidance)

When reviewing Ask AI outputs for product quality, confirm every response on trade-related pages ends with:

> NOT FINANCIAL ADVICE: This response is for educational and informational purposes only…

If a response omits the disclaimer or uses imperative buy/sell language, file a bug against `api/services/ai_narrative_llm.py` post-processing.

---

## When ALFa AI is down

market-pie5-bot must keep serving its primary functions:

- **Bot loop, screener, paper/sandbox trading** keep working without AI.
- **Ask AI dock** shows a friendly degraded message; no exceptions thrown.
- **`/api/health/detailed`** reports `litellm.status: unreachable` so monitoring catches it.
- **Legacy HuggingFace path** must remain disabled in production `.env`; do not fall back to cloud keys silently.

Brain-down checklist (from ``):

```bash
curl -fsS --max-time 3 http://192.0.2.30/health/liveliness || echo "LiteLLM down on "
curl -fsS --max-time 3 http://192.0.2.30/health || echo "ALFa API down on "
```

Fix on `` per [DOCKGE_111_OPERATOR.md](/home/operator/alfa-ai/docs/DOCKGE_111_OPERATOR.md). market-pie5-bot needs no action on `` — it self-recovers when the brain returns.

---

## Production hardening

Before exposing beyond trusted LAN:

1. Set strong **`LITELLM_MASTER_KEY`** and **`ALFA_AI_API_TOKEN`** in alfa-ai `deploy/.env` on ``.
2. Set **`ALFA_AI_REQUIRE_API_AUTH=true`** on orchestrator.
3. UFW-scope ports **8413** and **8420** on `` per `alfa-ai/docs/PORT_ASSIGNMENTS.md` LAN exception recipe (no ``-side firewall needed for these ports — they are not bound on ``).
4. Run `./scripts/alfa_ai_rollout_preflight.sh deploy/.env --strict` on brain host.
5. Remove legacy cloud keys (`HUGGINGFACE_API_KEY`, etc.) from production `.env` once LiteLLM path is verified.
6. Confirm **`PAPER_TRADING_MODE=true`** for non-production environments; live mode requires operator acknowledgment per `README.md` disclaimer.

---

## Related docs

- `.cursor/plans/ALFA_AI_INTEGRATION_PLAN.md` — staged rollout
- `docs/ENV_VARS.md` — all LiteLLM and ALFa variables
- `README.md` § DISCLAIMER — legal notice for automated trading
- `MISSION.md` — Phase 1 stocks scope
- `/home/operator/.cursor/plans/ALFA_AI_INTEGRATION_PLAN_HOST_105.md` — host-level service contract this guide inherits
- `/home/operator/docs/ALFA_AI_HOST_105_USAGE.md` — operator guide for `` host scripts
- `alfa-ai/docs/DISTRIBUTED_AI.md` — cluster topology and tier matrix
- `rankings-bot/docs/ALFA_AI_TRUST_ZONES_AND_ROLLOUT.md` — trust zone reference pattern
