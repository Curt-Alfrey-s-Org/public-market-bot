#!/usr/bin/env bash
# Run 4: Verify Live capital from Schwab API implementation. Outputs → debug_logs/run_4_*.
# Run from project root:  bash scripts/run_linux_commands_4.sh
# Do NOT use sudo — script uses git and venv.
set -e
cd "$(dirname "$0")/.."

git pull origin main
source venv/bin/activate

mkdir -p debug_logs
echo "=== $(date '+%Y-%m-%dT%H:%M:%S') ===" > debug_logs/run_4_env_info.txt
python3 --version >> debug_logs/run_4_env_info.txt
python3 -c "import sys; print('Prefix:', sys.prefix)" >> debug_logs/run_4_env_info.txt

{
  echo "=== Live capital from Schwab API - Verification ==="
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
  echo ""
  echo "1. Checking for _update_capital_from_schwab_api method:"
  grep -n "_update_capital_from_schwab_api" main.py | head -3 || echo "  ✗ Method not found"
  echo ""
  echo "2. Checking for USE_SCHWAB_CAPITAL_IN_LIVE in .env.example:"
  grep "USE_SCHWAB_CAPITAL_IN_LIVE" .env.example && echo "  ✓ Found" || echo "  ✗ Not found"
  echo ""
  echo "3. Checking for helper methods (_extract_capital_from_account):"
  grep -n "_extract_capital_from_account" main.py | head -2 || echo "  ✗ Methods not found"
  echo ""
  echo "4. Checking for refresh_capital_from_schwab_api method:"
  grep -n "refresh_capital_from_schwab_api" main.py | head -2 || echo "  ✗ Method not found"
  echo ""
  echo "5. Checking that method is called in __init__ (after _initialize_schwab_authenticator):"
  grep -A 5 "_initialize_schwab_authenticator()" main.py | grep -A 5 "_update_capital_from_schwab_api" | head -3 || echo "  ✗ Call not found"
  echo ""
  echo "6. Python syntax check (import test):"
  python3 -c "import main; print('  ✓ main.py imports successfully')" 2>&1 || echo "  ✗ Import failed"
  echo ""
  echo "7. Checking for USE_SCHWAB_CAPITAL_IN_LIVE env var definition:"
  grep -n "USE_SCHWAB_CAPITAL_IN_LIVE" main.py | head -2 || echo "  ✗ Env var not found"
  echo ""
  echo "=== Verification complete ==="
} | tee debug_logs/run_4_results.txt

git add debug_logs/
git status
git commit -m "chore(debug): run 4 Live capital from Schwab API verification for Cursor" || true
git push origin main

echo ""
echo "=== Done. Check debug_logs/run_4_results.txt (or run_4_env_info.txt). ==="
