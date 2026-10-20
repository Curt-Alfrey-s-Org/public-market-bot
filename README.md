# public-market-bot

Paper-trading stack: FastAPI backend, React web UI, and PostgreSQL. **Live trading stays off by default** (`PAPER_TRADING_MODE=true`). You supply your own API keys and secrets; nothing in this repo is pre-filled for a specific operator.

**License:** GNU General Public License v3.0 — see [LICENSE](LICENSE).

## Requirements

- [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/) (Compose V2: `docker compose`)
- Schwab developer credentials (optional until you connect a broker; sandbox mode is the default)
- Optional: an OpenAI-compatible LLM gateway (LiteLLM or similar) if you want AI-assisted features

## Quick start

1. **Clone** this repository.

2. **Configure environment**

   ```bash
   cp .env.example .env
   ```

   Copy the required auth lines from [env.required.example](env.required.example) into `.env` (or merge that file). Replace every `change-me` value with your own secrets. Generate a JWT secret, for example:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   Optional host URLs (documentation-only addresses): copy [config/hosts.example.env](config/hosts.example.env) to `config/hosts.env` and adjust if you use a custom LLM base URL.

   **Paper trading:** keep `PAPER_TRADING_MODE=true` and `SCHWAB_SANDBOX_MODE=true` until you deliberately go live.

   **Without an LLM gateway:** set `BOT_REQUIRE_BRAIN=false` and `LITELLM_ENABLED=false` in `.env` so the API starts without LiteLLM.

   Never commit `.env` or `config/hosts.env`.

3. **Create the external Compose network** (required once per Docker host; the frontend service attaches to it):

   ```bash
   docker network create tunnel_network
   ```

4. **Start the stack** ([Compose file reference](https://docs.docker.com/reference/compose-file/)):

   ```bash
   docker compose up -d --build
   ```

5. **Open the UI** at [http://127.0.0.1:5176](http://127.0.0.1:5176). The API listens on `127.0.0.1:8004`; Postgres on `127.0.0.1:5435`.

## Ports (from `docker-compose.yml`)

| Service            | Host address        |
|--------------------|---------------------|
| market-bot-frontend | `5176` → container `80` |
| market-bot-api     | `127.0.0.1:8004` → `8000` |
| postgres           | `127.0.0.1:5435` → `5432` |

## Health checks

```bash
docker compose ps
curl -fsS http://127.0.0.1:8004/api/health
curl -fsS http://127.0.0.1:5176/
```

## Further reading

- [CONTRIBUTING.md](CONTRIBUTING.md) — development notes
- [docs/PUBLIC_SNAPSHOT.md](docs/PUBLIC_SNAPSHOT.md) — what this public tree includes
- [docs/USER_GUIDE.md](docs/USER_GUIDE.md) — using the web GUI

## Disclaimer

Experimental software, not financial advice. You are responsible for orders, compliance, and safeguarding your credentials.
