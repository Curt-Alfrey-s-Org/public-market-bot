#!/usr/bin/env bash
# Legacy single script (overwrites debug_logs files). Prefer numbered scripts:
#   bash scripts/run_linux_commands_2.sh  (short-validation → run_2_*)
#   bash scripts/run_linux_commands_3.sh  (screener → run_3_*)
# Run from project root, as your user (venv OK):  bash scripts/run_linux_commands.sh
# If executable:  chmod +x scripts/run_linux_commands.sh  then  ./scripts/run_linux_commands.sh
# Do NOT use sudo — script uses git and venv; sudo can cause "command not found" and path issues.
set -e
cd "$(dirname "$0")/.."

git pull origin main
source venv/bin/activate

mkdir -p debug_logs
echo "=== $(date '+%Y-%m-%dT%H:%M:%S') ===" > debug_logs/env_info.txt
python3 --version >> debug_logs/env_info.txt
python3 -c "import sys; print('Prefix:', sys.prefix)" >> debug_logs/env_info.txt

echo "=== Short-selling validation (paper/sandbox buy + short) ==="
python3 -m unittest test_order_type_configuration test_strategy_signals test_short_selling test_order_payload_builder -v 2>&1 | tee debug_logs/short_validation.txt || true

git add debug_logs/
git status
git commit -m "chore(debug): short-selling validation results for Cursor" || true
git push origin main

echo ""
echo "=== Done. Check debug_logs/short_validation.txt (or env_info.txt). ==="
