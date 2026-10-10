# Public snapshot

This tree is a **scrubbed snapshot** of the private `market-pie5-bot` repository. It is not
a continuation of private git history. The source commit SHA is recorded only on the operator
build host under `public-exports/_tools/market-source-sha.txt`.

## Configure before you run

1. Copy `config/hosts.example.env` to `config/hosts.env` and set your hostnames or IPs (do not commit `hosts.env`).
2. Copy `.env.example` to `.env` and set database, brokerage, and auth placeholders to real secrets (never commit `.env`).
3. Copy `env.required.example` lines you need into `.env` if you use the 2026 security-review variables.
4. Point AI at your own LiteLLM or compatible gateway, for example `LITELLM_BASE_URL=http://192.0.2.30:8000` (documentation address [RFC 5737](https://www.rfc-editor.org/rfc/rfc5737)).

Live trading and automated order schedulers stay **disabled** in the shipped examples (`PAPER_TRADING_MODE=true`, no live feature flags enabled). Enable them only deliberately on your own deployment.

## Example addresses (RFC 5737)

| Role | Example variable | Address |
|------|------------------|---------|
| Market app host | `MARKET_HOST` | `192.0.2.21` |
| LLM / LiteLLM gateway | `LITELLM_BASE_URL` | `http://192.0.2.30:8000` |
| Loopback | API bind | `127.0.0.1` |

Public URL example: `https://market.example.com` ([RFC 2606](https://www.rfc-editor.org/rfc/rfc2606)).

## Dropped or rewritten

- `docs/REPO_HOST_MAPPING.md` (cluster inventory)
- `.cursor/` operator rules tied to this deployment
- Non-example env files (`.env`, `.env.local`, etc.)
- `MYSQL_CREDENTIAL_CHANGE.md` replaced with a generic rotation note (no live hosts or passwords)
