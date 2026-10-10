# Coding Standards — Market-Pie5-Bot

**Principle:** All code must be standards-driven, following official manuals, documentation, and industry best practices.

---

## Core Principles

### 1. Follow Official Documentation First

When implementing features or fixing issues:
- **Consult official documentation** for the framework/library being used
- **Reference language specifications** for Python, TypeScript, JavaScript
- **Follow API documentation** exactly (FastAPI, React, Vite, Schwab API)
- **Use proven patterns** from official examples and guides

**Never guess or assume** — look it up in the official docs.

---

## Language-Specific Standards

### Python (FastAPI Backend)

#### Style & Formatting
- **PEP 8** — Python style guide (line length, naming, imports)
- **PEP 257** — Docstring conventions
- **Type hints** — Use Python 3.10+ type annotations for all function signatures
- **Import order**: stdlib → third-party → local (alphabetized within each group)

#### FastAPI Best Practices
- **Pydantic models** for all request/response validation
- **Dependency injection** for database sessions, auth
- **HTTP status codes** — Use correct semantic codes (200, 201, 400, 401, 404, 500)
- **Error handling** — Always raise `HTTPException` with proper status and detail
- **Async where appropriate** — Use `async def` for I/O-bound operations

### TypeScript/JavaScript (React Frontend)

#### Style & Formatting
- **ESLint** — Follow configured linting rules
- **TypeScript strict mode** — Enable strict type checking
- **Naming** — PascalCase for components, camelCase for functions/variables

#### React Best Practices (React 18+)
- **Functional components** — Always use function components with hooks
- **TypeScript interfaces** — Define types for all props, state, API responses
- **Hooks** — Use built-in hooks properly (useState, useEffect, useContext, useMemo)
- **Error boundaries** — Implement error boundaries for resilient UIs

---

## Docker & Deployment Standards

### Dockerfile Best Practices
- **Multi-stage builds** — Separate build and runtime stages
- **Minimal base images** — Use alpine or slim variants
- **Layer caching** — Order commands for optimal caching
- **Health checks** — Always include HEALTHCHECK instruction

### Docker Compose Standards
- **Networks** — Use shared networks for service communication
- **Environment** — Use `.env` files, never hardcode secrets
- **Restart policy** — Set `restart: unless-stopped` for production services

---

## Security Standards

### Secrets Management
- **Environment variables** — Store secrets in `.env` files (never commit)
- **Token encryption** — Use Fernet for `token.json` when `SCHWAB_TOKEN_ENCRYPTION_KEY` is set
- **Log masking** — Never log API keys, tokens, or account IDs

### Subprocess / Running External Commands
- **Prefer list form** — Use `subprocess.Popen([executable, arg1, ...])`; avoid `shell=True`
- **Absolute path for executable** — Use `/bin/bash` so commands work when PATH is empty
- **No user input in command** — Never pass unsanitized user input as executable or arguments

---

## Testing Standards

### Unit Tests
- **Naming** — Test function names should describe what's being tested
- **Arrange-Act-Assert** — Follow AAA pattern
- **Mocking** — Mock external dependencies (Schwab API, yfinance)
- **Isolation** — Each test should be independent

### Integration Tests
- **Test real workflows** — Test complete trading flows
- **API endpoints** — Test all HTTP methods and status codes
- **Error scenarios** — Test error handling and edge cases

---

## Git & Version Control Standards

### Commit Messages (Conventional Commits)
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `refactor:` — Code refactoring
- `test:` — Test additions/changes
- `chore:` — Maintenance tasks

### Branch Strategy
- **main** — Production-ready code
- **develop** — Integration branch
- **feature/** — New features
- **fix/** — Bug fixes
- **hotfix/** — Urgent production fixes

---

## Configuration Standards

### Critical Settings — Fail Fast
- **Required env vars** — `PAPER_TRADING_MODE`, `SCHWAB_API_KEY` (for live): fail with clear error if missing or invalid
- **Do not** silently fall back to dangerous defaults (e.g., live trading when credentials missing)
- **API:** Return 503 with clear message when required config is missing

---

## Market Bot Specific Standards

### Trading Safety
- **Mode gates** — Never execute live trades when `PAPER_TRADING_MODE=true`
- **Confirmation** — Require explicit user confirmation before trading starts
- **PDT compliance** — Enforce PDT rules in live mode; document behavior

### Schwab API Integration
- **Rate limiting** — Respect Schwab API rate limits; use built-in retry/backoff
- **Error handling** — Handle auth failures, timeouts, 429; never silently continue with bad data
- **Sandbox vs production** — Use correct endpoints; sandbox fails hard (no fallback to fake data)

### Token Storage
- **Encryption** — Support Fernet encryption for `token.json`
- **HMAC integrity** — Detect tampering; log verification failures

---

## References

- **Python:** [PEP 8](https://peps.python.org/pep-0008/), [PEP 257](https://peps.python.org/pep-0257/)
- **FastAPI:** [Official Documentation](https://fastapi.tiangolo.com/)
- **React:** [Official Documentation](https://react.dev/)
- **Docker:** [Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

## Enforcement

Code reviews should verify:
- ✅ Follows official documentation and best practices
- ✅ Includes proper error handling and validation
- ✅ Has appropriate tests and documentation
- ✅ Meets security and trading safety standards

**When in doubt, consult the official documentation first.**
