# market-pie5-bot (public snapshot)

Paper-trading bot with an API, a web UI, and an optional LLM gateway. This tree is a scrubbed snapshot. See `docs/PUBLIC_SNAPSHOT.md`.

License: GNU General Public License version 3. See `LICENSE`.

The shipped example keeps paper trading on (`PAPER_TRADING_MODE=true`). Leave live trading off until you choose to enable it on your own machine.

## Configure before you run

1. Copy `config/hosts.example.env` to `config/hosts.env`. Do not commit `hosts.env`.
2. Copy `.env.example` to `.env` and replace every `change-me` placeholder. Never commit `.env`.
3. Set `LITELLM_BASE_URL` only when you run your own gateway.

## Ports

From `docker-compose.yml` in this repo:

| Service | Published address |
|---------|-------------------|
| postgres | `127.0.0.1:5435` (container `5432`) |
| market-bot-api | `127.0.0.1:8004` (container `8000`) |
| market-bot-frontend | port `5176` (container `80`) |

## Run

```bash
docker compose up -d
```

Open the UI on port 5176. The API and Postgres listen on localhost.

This program is experimental. It is not financial advice. You are responsible for any orders and for your own API credentials.
