# Dependencies — Market-Pie5-Bot

All Python and frontend dependencies. Use this as the single reference for what the project needs.

---

## Python (Backend)

**File:** `requirements.txt`

### Core
- `requests`, `aiohttp`, `httpx` — HTTP clients
- `python-dotenv`, `pydantic-settings` — Config
- `cryptography`, `PyJWT`, `pwdlib[argon2,bcrypt]` — Auth, tokens (argon2 hashing; bcrypt extra verifies legacy hashes)
- `fastapi`, `uvicorn`, `pydantic`, `slowapi` — API framework

### Data & Trading
- `pandas`, `numpy`, `yfinance`, `yahooquery` — Market data
- `schwab-py`, `alpha-vantage` — Broker APIs
- `backtrader` — Backtesting

### ML & Analysis (local — no LLM)
- `scikit-learn`, `joblib` — Signal filter (`ml_signal_filter.py`: RandomForest / GradientBoosting). See [ML_GUIDE.md](../ML_GUIDE.md). Official upgrades: `CalibratedClassifierCV`, `HistGradientBoostingClassifier` ([sklearn docs](https://scikit-learn.org/stable/modules/calibration.html)).
- `vaderSentiment`, `textblob` — Sentiment (`sentiment_analyzer.py`). Planned: migrate VADER to [NLTK](https://www.nltk.org/howto/sentiment.html) (PyPI `vaderSentiment` frozen since 2020).
- `scipy` — Portfolio optimization (`scipy.optimize.minimize`)

### ALFa AI (brain on `` — LLM narratives & monitoring only)
- `httpx` — LiteLLM client (`api/services/litellm_client.py`)
- Env: `LITELLM_*`, `BOT_REQUIRE_BRAIN`, `BOT_LLM_INSIGHTS_ENABLED` — see [ENV_VARS.md](ENV_VARS.md)
- Architecture: [ML_AND_AI_ARCHITECTURE.md](ML_AND_AI_ARCHITECTURE.md)

**Removed:** HuggingFace cloud LLM (`HUGGINGFACE_API_KEY`). Parameter tuning is backtest heuristics, not LLM.

### Database
- `sqlalchemy`, `alembic`, `psycopg2-binary` — ORM, migrations

### Testing
- `pytest`, `pytest-cov` — Tests

---

## Frontend (React + Vite)

**File:** `frontend/package.json`

### Dependencies
- `react`, `react-dom` — UI
- `@tanstack/react-query` — Data fetching
- `axios` — HTTP
- `zustand` — State
- `react-router-dom` — Routing

### DevDependencies
- `vite`, `@vitejs/plugin-react` — Build
- `typescript`, `@types/*` — Types
- `tailwindcss`, `postcss`, `autoprefixer` — Styling
- `eslint`, `@typescript-eslint/*` — Lint

---

## Install

```bash
# Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

---

## See Also

- [ML_AND_AI_ARCHITECTURE.md](ML_AND_AI_ARCHITECTURE.md) — ML vs ALFa AI layers
- [START_STOP_RESTART.md](START_STOP_RESTART.md) — Run the app
- [.github/PORT_ASSIGNMENTS.md](../.github/PORT_ASSIGNMENTS.md) — Ports
