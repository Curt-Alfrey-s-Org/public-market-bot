# Secrets Management - Market Bot

**CRITICAL:** Never commit `.env.production` or any files containing real secrets to version control.

## Overview

This document describes how secrets are managed in the Market Bot application to ensure:
- No hardcoded API keys in docker-compose.yml
- No sensitive values in logs
- Secure secret validation at startup
- Proper secret rotation procedures

## Files

### `.env.example` (Safe - Committed)
Template file with placeholder values. Used by developers to understand required variables.

```bash
BOT_API_KEY=your_bot_api_key_here
SCHWAB_CLIENT_SECRET=your_schwab_client_secret_here
POSTGRES_PASSWORD=your_postgres_password_here
```

### `.env.production` (Secret - NOT Committed) ⚠️
Contains real production secrets. **MUST be in .gitignore and NEVER committed.**

```bash
BOT_API_KEY=<real key: generate with openssl rand -base64 48>
JWT_SECRET=<real secret: python -c "import secrets; print(secrets.token_urlsafe(48))">
SCHWAB_CLIENT_SECRET=abc123xyz789...
POSTGRES_PASSWORD=super_secret_password_123
```

### `.env` (Development - Ignored)
Local development environment file. Ignored by git.

## Setup Instructions

### Local Development

1. **Copy template to production file:**
   ```bash
   cp .env.example .env.production
   ```

2. **Fill in real values:**
   ```bash
   # Edit .env.production with a secure editor
   nano .env.production
   ```

3. **Verify no secrets are logged:**
   ```bash
   # Check that docker-compose.yml references ${BOT_API_KEY} not literal values
   grep -i "ijBIr2v5WP" docker-compose.yml || echo "✓ No hardcoded keys found"
   ```

### Docker Deployment

1. **Load environment from file:**
   ```bash
   docker compose --env-file .env.production up -d
   ```

2. **Verify secrets loaded correctly:**
   ```bash
   # Check logs for redaction markers
   docker logs market-pie5-bot-api | grep -i "redacted" | head -5
   ```

3. **Never use default values in docker-compose.yml:**
   ```yaml
   # ✓ Good: Uses environment variable
   - BOT_API_KEY=${BOT_API_KEY}
   
   # ✗ Bad: Hardcoded secret (NEVER use)
   - BOT_API_KEY=<real-key-committed-here>
   ```

## Environment Variables

> **2026-09-25:** `VITE_API_KEY` was removed. Anything in a `VITE_*` variable is
> compiled into the public JavaScript bundle, so the backend key must never be
> passed to the frontend build. See `env.required.example` and `docs/LOGIN_AUTH.md`.

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | PostgreSQL connection string | `postgresql://user@localhost:5432/marketbot` |
| `BOT_API_KEY` | Yes | Server-to-server API key (`X-API-Key`) for scripts/monitoring. Never built into the frontend; admin control endpoints ignore it. | `<generate: openssl rand -base64 48>` |
| `JWT_SECRET` | Yes (production) | JWT signing secret for login sessions. API refuses to start in production without it. | `<generate: python -c "import secrets; print(secrets.token_urlsafe(48))">` |
| `LITELLM_API_KEY` | Yes if `BOT_REQUIRE_BRAIN=true` | This bot's key for the ALFa AI LiteLLM proxy | `<your LiteLLM virtual key>` |
| `SCHWAB_CLIENT_ID` | No | Schwab OAuth client ID (if using Schwab integration) | `client_id_here` |
| `SCHWAB_CLIENT_SECRET` | No | Schwab OAuth client secret | `client_secret_here` |
| `POSTGRES_PASSWORD` | Yes | PostgreSQL user password | `secure_password_123` |
| `ADMIN_PASSWORD` | Yes | Admin user password | `admin_secure_pass` |
| `DIRECTOR_PASSWORD` | Yes | Director user password | `director_secure_pass` |
| `USER_PASSWORD` | Yes | Standard user password | `user_secure_pass` |

## Validation at Startup

The application validates all required environment variables at startup using `api/config.py`:

```python
# Fails immediately if required variables are missing
try:
    settings = Settings()
except Exception as e:
    print(f"❌ CONFIGURATION ERROR: {e}")
    # Lists which required variables are missing
    sys.exit(1)
```

### Example startup error:
```
❌ CONFIGURATION ERROR: Missing required environment variable: POSTGRES_PASSWORD

Please ensure all required environment variables are set in .env file:
  - DATABASE_URL
  - POSTGRES_PASSWORD
  - BOT_API_KEY
  ...
```

## Secret Redaction in Logs

All logs are automatically filtered to redact sensitive values:

```python
# Logging module automatically redacts:
logger.info("Connected to database")
# Output: "Connected to database"  (no credentials shown)

logger.debug(f"Using DATABASE_URL: {database_url}")
# Output: "Using DATABASE_URL: postgresql://***REDACTED***"
```

### Redacted Patterns

The following are automatically redacted from logs:
- `BOT_API_KEY`, `VITE_API_KEY`, `api_key`, `api-key`
- `SCHWAB_CLIENT_SECRET`, `client_secret`, `secret`
- `POSTGRES_PASSWORD`, `password`, `passwd`
- PostgreSQL connection strings (URLs with credentials)
- Bearer tokens and Authorization headers
- Any custom values with "key", "password", "secret", or "token" in the name

## Rotation Procedures

### Rotate API Key

1. **Generate new key:**
   ```bash
   # Generate new random API key (example using OpenSSL)
   openssl rand -base64 48 | tr -d '\n='
   ```

2. **Update .env.production:**
   ```bash
   # Edit to replace old key
   BOT_API_KEY=new_key_here
   # VITE_API_KEY is no longer used: the frontend authenticates with the
   # logged-in user's JWT, so rotating BOT_API_KEY needs no frontend rebuild.
   ```

3. **Deploy with new key:**
   ```bash
   docker compose --env-file .env.production down
   docker compose --env-file .env.production up -d
   ```

4. **Verify:**
   ```bash
   # Check logs for successful startup
   docker logs market-pie5-bot-api | grep "Bot started" | tail -1
   ```

### Rotate Database Password

1. **Generate new password:**
   ```bash
   openssl rand -base64 24 | tr -d '\n='
   ```

2. **Update PostgreSQL:**
   ```bash
   docker exec market-pie5-bot-postgres psql -U postgres -c \
     "ALTER USER marketbot_user WITH PASSWORD 'new_password';"
   ```

3. **Update .env.production:**
   ```bash
   POSTGRES_PASSWORD=new_password
   DATABASE_URL=postgresql://marketbot_user@postgres:5432/marketbot
   ```

4. **Restart application:**
   ```bash
   docker compose --env-file .env.production restart market-pie5-bot-api
   ```

## Security Best Practices

1. **Never commit secrets:**
   - Always use `.env.production` (in .gitignore)
   - Use `.env.example` as template (safe to commit)

2. **Limit secret access:**
   - Only deployment team should have access to .env.production
   - Use secure vault/secrets manager in production (AWS Secrets Manager, HashiCorp Vault, etc.)

3. **Audit logs:**
   - Regularly check logs for any leaks: `docker logs market-pie5-bot-api | grep -v "***REDACTED***"`
   - All logs are automatically redacted; any visible secrets indicate a breach

4. **Rotation schedule:**
   - Rotate API keys quarterly
   - Rotate database passwords quarterly
   - Rotate admin passwords monthly

5. **Environment variable loading:**
   - Load from `.env` or `.env.production` at startup
   - Never pass secrets as command-line arguments (visible in `ps` output)
   - Use `docker secrets` for Docker Swarm deployments

## Troubleshooting

### Application fails to start with "Missing environment variable"

```bash
# Check if .env.production exists
ls -la .env.production

# Check for typos in variable names (case-sensitive)
cat .env.production | head -20

# Verify required variables are present
grep -E "DATABASE_URL|BOT_API_KEY|POSTGRES_PASSWORD" .env.production
```

### Secrets appearing in logs

```bash
# Check if logs show actual values (indicates redaction bypass)
docker logs market-pie5-bot-api | grep -i "ijBIr2v5WP"  # Should return nothing

# If found, restart with fresh environment
docker compose --env-file .env.production restart market-pie5-bot-api
```

### Can't access database after password rotation

```bash
# Verify connection string format
cat .env.production | grep DATABASE_URL

# Test connection manually
docker exec market-pie5-bot-api psql ${DATABASE_URL} -c "SELECT 1"

# Check PostgreSQL logs
docker logs market-pie5-bot-postgres | grep -i "authentication\|error"
```

## References

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/
- [Docker Secrets Best Practices](https://docs.docker.com/engine/swarm/secrets/)
