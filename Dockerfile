# syntax=docker/dockerfile:1
# Python 3.12: 3.10 reaches EOL Oct 2026 (https://devguide.python.org/versions/);
# matches rankings-bot base image (cross-repo parity).
FROM python:3.12-slim

WORKDIR /app

# Shared apt cache across bot repos (BuildKit ids bots-apt / bots-apt-lists).
# See /srv/dep-cache/README.md.
RUN --mount=type=cache,id=bots-apt,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=bots-apt-lists,target=/var/lib/apt/lists,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl

COPY requirements.txt .

# Shared pip cache across bot repos (BuildKit id=bots-pip).
COPY build-contexts/wheels-bots/ /tmp/wheels/
RUN --mount=type=cache,id=bots-pip,target=/root/.cache/pip,sharing=locked \
    pip install --find-links /tmp/wheels -r requirements.txt

# Copy application
COPY api/ /app/api/
COPY log_manager.py /app/
COPY *.py /app/
# Optional bot data sources imported by main.py (earnings/macro calendars, retail
# sentiment, options flow, news monitor). Without this they were silently
# disabled in the container (security/correctness review 2026-09-25).
COPY web_scrapers/ /app/web_scrapers/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the API
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
