# ML & AI Architecture — market-pie5-bot

**Canonical reference** for how machine learning and the ALFa AI brain fit together after the 2026 integration rollout. Read this before changing `main.py`, `ml_param_optimizer.py`, or any LiteLLM client.

**Related:** [ALFA_AI_HOW_TO_USE.md](ALFA_AI_HOW_TO_USE.md) · [ENV_VARS.md](ENV_VARS.md) · [ML_GUIDE.md](../ML_GUIDE.md) · [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md) · [ROADMAP.md](ROADMAP.md) (current step + deferred issues)

---

## Implementation status (Jul 2026)

**Objective:** ALFa AI brain is the **only** AI provider in this repo.

**Status:** ✅ **Complete** (runtime + docs + tests). Next repo priority is
**P1 production hardening** — see [ROADMAP.md](ROADMAP.md) *Current step*.

### Delivered

| Phase | What | Key files |
|-------|------|-----------|
| P0 — survey & docs | Architecture doc, env vars, `.env.example` | `docs/ML_AND_AI_ARCHITECTURE.md`, `docs/ENV_VARS.md` |
| P0 — remove Ollama | Deleted direct Ollama client; `LLMResponse` type | `api/services/llm_types.py`, removed `ollama_client.py` |
| P0 — purge HuggingFace | Removed HF env/docs; deleted stale summaries | `.env.example`, removed `HUGGINGFACE_*` from runtime |
| P1 — local ML context | Read-only decision factors in narratives | `main.py`, `api/services/trading_insights_llm.py` |
| P2 — sentiment → brain | Batched LiteLLM sentiment per symbol; VADER fallback | `sentiment_analyzer.py` (`SENTIMENT_USE_BRAIN`) |
| Tests | HF purge; encryption tests use `NEWS_API_KEY` | `test_env_decryption.py`, `test_encrypted_api_key_integration.py`, +13 files |

**Git commits (main):** `09bd4b4`, `2c54666`, `9bb0ae3` (Jul 2026).

### Not in scope (by design)

- **Local ML stays in-process** where numerically superior (signal filter, adaptive learning, portfolio opt). See *Design principle: three layers* below.
- **LLM does not tune trading parameters** — heuristics only; brain explains.
- **Legacy table name** `ollama_activity_log` kept for schema continuity; logs generic brain activity.

### Open issues for later work

Tracked as **K1–K7** in [ROADMAP.md](ROADMAP.md) *Known issues / deferred work*. Highlights:

- **K1:** Alpha Vantage placeholder validation test vs soft-warning behavior.
- **K2:** VADER + Python 3.14 + strict pytest deprecation filter.
- **K5:** Deploy host doc drift (`` vs ``).
- **K7:** LiteLLM client parity vs rankings-bot reference.

---

## Single AI provider: the ALFa AI brain

**The ALFa AI brain (LiteLLM on `:8413` + orchestrator on `:8420`) is the
only AI provider in this repo.** There is no HuggingFace path and no direct
Ollama client. Any local model must be exposed as a LiteLLM alias on the brain,
not wired as a second client here. All LLM/embedding calls go through
`api/services/litellm_client.py`.

## Design principle: three layers

| Layer | What decides trades | Technology | Provider |
|-------|---------------------|------------|----------|
| **1. Strategies** | BUY/SELL/HOLD signals | Deterministic rules + indicators (`main.py`, `pandas-ta`) | In-process (no AI) |
| **2. Local ML** | Filter signals, strategy weights | scikit-learn, Q-learning/bandit (`ml_signal_filter.py`, `adaptive_learning.py`) — numerically superior to an LLM at tabular prediction/RL | In-process (no AI) |
| **3. ALFa AI (brain)** | Sentiment, explain, monitor, narrate, RAG — **never executes trades** | LiteLLM on ``, orchestrator `:8420` | ALFa AI only |

**Division of labor (why each layer exists):**
- Keep layer 2 local **only where it beats an LLM**: tabular signal-filter
  probability (scikit-learn) and reinforcement-learning weights (Q-learning). The
  brain does not replace these; official sklearn guidance is that LLMs are not
  validated for tabular prediction or RL parameter tuning.
- Everything the brain does **better** — sentiment, reasoning, narration,
  monitoring, retrieval — belongs to layer 3.
- **Local ML feeds the brain:** sentiment is produced by the brain directly
  (see below). Signal-filter status, adaptive-learning strategy weights, and the
  sentiment source are passed into the brain's narrative context via
  `TradingBot.get_decision_factors_summary()` (read-only) →
  `generate_performance_narrative(track_record, decision_factors=...)`. The trade
  journal also surfaces per-trade `strategy` / `ml_confidence` /
  `sentiment_signal` when present. This lets the brain describe *how* the bot
  decided; it never feeds back into execution.

Trade execution is **always** layer 1 + 2. The brain does not pick symbols, sizes, or parameters to auto-apply unless you explicitly enable heuristic auto-tune (see below).

---

## What changed (2026) and why

### 1. HuggingFace removed → ALFa AI brain (LiteLLM)

**Before:** `main.py` and `ml_param_optimizer.py` called `https://router.huggingface.co` with `meta-llama/Meta-Llama-3-8B-Instruct`.

**After:** All LLM calls go to the ALFa AI brain at `http://192.0.2.30` (OpenAI-compatible). Client: `api/services/litellm_client.py`.

**Why:** Cluster brain is LAN-local, auditable, and shares model aliases with other bots. HuggingFace cloud keys and rate limits are gone.

**Removed env vars:** `HUGGINGFACE_API_KEY`, `HUGGINGFACE_MAX_CALLS_PER_MINUTE`, etc.

---

### 2. LLM no longer tunes trading parameters

**Before:** The LLM was prompted as a “trading expert” and asked for JSON settings (`AI_SYSTEM_PROMPT`, `_call_llm_api`). No proven out-of-sample edge for LLM parameter advice.

**After:**
- **`ml_param_optimizer.py`** — **backtest heuristics** only (rule-based nudges from win rate, drawdown, Sharpe within `param_ranges`). Method: `backtest_heuristic`.
- **`api/services/trading_insights_llm.py`** — LLM for **narratives only** (performance summary, trade journal, optional *explanation* of heuristic changes). Never parses LLM JSON for settings.
- **`apply_ai_suggestions()`** — only applies heuristic optimizer output when `BOT_ENABLE_AI_AUTO_TWEAK=true`; does not parse LLM responses for settings.

**Why:** Research (sklearn FAQ, FinBen, Bailey/López de Prado) shows LLMs are not validated for production parameter tuning. Heuristics + walk-forward backtests are the honest path; LLM explains results to humans.

**API surface:**

| Endpoint | Purpose |
|----------|---------|
| `POST /api/ai/request` | Performance narrative (LLM) |
| `POST /api/ai/journal` | Recent trades summary (LLM) |
| `GET /api/ai/optimization-suggestions` | Heuristic params; `?explain=true` for LLM explanation |

---

### 3. Automatic error monitoring + admin AI Monitor

**Added:** `error_events` table, `api/services/error_monitor.py`, background triage via LiteLLM `code`, admin UI `/admin/ai-monitor`.

**Why:** Ops visibility without manual log triage. Errors are redacted before persistence or LLM calls.

---

### 4. Ask AI dock, RAG, agentic jobs, dev tooling

| Feature | Module / route |
|---------|----------------|
| Ask AI (per-page Q&A) | `api/routes/ai_narrative.py`, `AskAIDock.tsx` |
| RAG over domain docs | `market_rag.py`, `scripts/rag/index_market_corpus.py` |
| End-of-day / anomaly / sector jobs | `api/routes/ai_jobs.py` → orchestrator `POST /api/runs` |
| PR triage / codegen | `.github/workflows/ai-pr-triage.yml`, `scripts/codegen/` |
| Opt-in fine-tune capture | `finetune_capture.py`, `FINETUNE_CAPTURE_ENABLED` |

All user-facing LLM output includes **NOT FINANCIAL ADVICE** and sanitized context (`market_ask_ai_context.py`).

---

### 5. Trading gate: `BOT_REQUIRE_BRAIN=true` (default)

**Before:** AI features degraded gracefully; the trading loop kept running if the brain was down.

**After (default):** The trader **refuses to start** and **halts mid-run** if LiteLLM `/health/liveliness` fails when `BOT_REQUIRE_BRAIN=true`.

**Why:** Operator policy — do not run the bot when the advisory/monitoring stack is unavailable.

**Important:** Trade *decisions* still do not use the brain. The gate is policy, not alpha. Set `BOT_REQUIRE_BRAIN=false` to restore old behavior.

---

## Local ML stack (kept only where superior to the brain)

These run **in-process** with no external LLM and feed their output into the
brain's context:

| Component | Module | Why local | Planned upgrades |
|-----------|--------|-----------|------------------|
| Signal filter | `ml_signal_filter.py` — RF / `GradientBoostingClassifier` | Tabular win-probability; an LLM is not superior here ([scikit-learn](https://scikit-learn.org/stable/) 1.8+) | `CalibratedClassifierCV`, `class_weight='balanced'`, optional `HistGradientBoostingClassifier` |
| Adaptive learning | `adaptive_learning.py` — Q-learning + Thompson bandit | Reinforcement learning; sklearn [FAQ: RL out of scope](https://scikit-learn.org/stable/faq.html), LLMs unvalidated | Keep; validate with walk-forward |
| Portfolio opt | `scipy.optimize.minimize` | Constrained numeric optimization ([SciPy 1.17+](https://docs.scipy.org/doc/scipy/)) | Bump minimum pin |

**Not recommended by official sklearn/scipy docs:** FinBERT, BloombergGPT, or transformers as drop-in replacements for the tabular signal filter.

### Sentiment → moved to the brain

Sentiment analysis is a language task the brain does better than the frozen-2020
VADER lexicon, so it is handled by the ALFa AI brain (`sentiment_analyzer.py`
`_brain_sentiment()` — one batched LiteLLM call per symbol over its headlines). A
deterministic VADER/TextBlob fallback remains only for offline/degraded mode
(brain unreachable or `SENTIMENT_USE_BRAIN=false`), consistent with the
graceful-degrade contract of every other AI feature.

---

## Environment variables (summary)

See [ENV_VARS.md](ENV_VARS.md) for the full list.

| Variable | Default | Role |
|----------|---------|------|
| `LITELLM_ENABLED` | `false` | Master switch for brain LLM features |
| `SENTIMENT_USE_BRAIN` | `true` | Use the brain for sentiment; falls back to VADER when off/unreachable |
| `BOT_REQUIRE_BRAIN` | `true` | Hard gate: no trading if brain down |
| `BOT_LLM_INSIGHTS_ENABLED` | `true` | Narratives (journal, performance summary) |
| `BOT_ENABLE_AI_AUTO_TWEAK` | `false` | Auto-apply **heuristic** params only |
| `ERROR_MONITOR_ENABLED` | `true` | Capture + triage errors |

---

## Historical docs

HuggingFace-era summaries (`HUGGINGFACE_API_FIX_SUMMARY.md`,
`API_KEY_RELOAD_FIX_SUMMARY.md`) have been **removed** — the ALFa AI brain is the
only AI provider. Canonical integration status is
[INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md).

---

## Apply changes on ``

Per [REPO_HOST_MAPPING.md](REPO_HOST_MAPPING.md), the market-pie5-bot clone
runs on **``** (`/home/operator/market-pie5-bot`). Legacy docs may still
reference ``; treat `` as canonical until those are reconciled (K5).

```bash
cd /home/operator/market-pie5-bot
git pull --ff-only origin main
docker compose --env-file .env up -d --no-deps --force-recreate market-bot-api
curl -fsS http://127.0.0.1:8004/api/health/detailed | jq '{litellm, brain_gate: "BOT_REQUIRE_BRAIN in .env"}'
```
