# Port Configuration Summary (Updated)

This project now follows the canonical port assignments documented in:
- `/home/operator/.github/PORT_ASSIGNMENTS.md`

## Production Ports (Canonical)

- **API Host Binding:** `127.0.0.1:8004` → container `8000`
- **Frontend Host Binding:** `5176:80` (nginx)
- **Postgres Host Binding:** `127.0.0.1:5435` → container `5432`

## Local Development (Optional)

- **Vite dev server:** `5173` (local only, not used in production)
- **API dev server:** `8000` inside container

## Why This Changed

Earlier notes referenced the default Vite port `5173`. Production now uses the nginx container on port `80`, with the host mapping `5176:80` for optional local access. The API is locked to localhost (`127.0.0.1:8004`) and reached by nginx over Docker DNS.

## See Also

- `.github/PORT_ASSIGNMENTS.md` (canonical source)
- `.github/NETWORKING_STANDARDS.md`
