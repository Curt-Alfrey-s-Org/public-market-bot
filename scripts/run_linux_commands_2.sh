#!/usr/bin/env bash
# Run 2: Short-selling validation (paper/sandbox buy + short). Outputs → debug_logs/run_2_*.
# Run from project root:  bash scripts/run_linux_commands_2.sh
# Do NOT use sudo — script uses git and venv.
set -e
cd "$(dirname "$0")/.."

git pull origin main
source venv/bin/activate

mkdir -p debug_logs
echo "=== $(date '+%Y-%m-%dT%H:%M:%S') ===" > debug_logs/run_2_env_info.txt
python3 --version >> debug_logs/run_2_env_info.txt
python3 -c "import sys; print('Prefix:', sys.prefix)" >> debug_logs/run_2_env_info.txt

{
  echo "=== Short-selling validation (paper/sandbox buy + short) ==="
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
  python3 -m unittest test_order_type_configuration test_strategy_signals test_short_selling test_order_payload_builder -v 2>&1 || true
} | tee debug_logs/run_2_results.txt

git add debug_logs/
git status
git commit -m "chore(debug): run 2 short-selling validation results for Cursor" || true
git push origin main

echo ""
echo "=== Done. Check debug_logs/run_2_results.txt (or run_2_env_info.txt). ==="
