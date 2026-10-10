#!/bin/bash
# Market Pie5 Bot Dashboard Setup - Nginx-Only Architecture
# Run this on the server to display deployment information.

set -e

echo "=========================================="
echo "  Market Pie5 Bot Dashboard"
echo "=========================================="
echo ""
echo "Architecture: Nginx-only reverse proxy"
echo ""
echo "Deployment Instructions:"
echo "1. Build and start (host UID for API bind mounts — see scripts/export_compose_uid_gid.sh):"
echo "   . scripts/export_compose_uid_gid.sh && write_compose_host_user_env \"\$(pwd)\""
echo "   docker compose --env-file .env.compose-host-user --env-file .env up -d --build"
echo "2. API is exposed on port 8004 (mapped to internal port 8000)"
echo "3. Access dashboard at: http://your-domain:8004"
echo ""
echo "Container Network: market-bot-network (custom bridge)"
echo "API Container: market-pie5-bot-api"
echo "Health Check: http://localhost:8004/api/health"
echo ""
echo "For production subdomain setup:"
echo "Configure your reverse proxy (e.g., Nginx on host) to proxy"
echo "market-bot.example.com -> http://localhost:8004"
echo ""
