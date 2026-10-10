#!/usr/bin/env bash
# Run 3: Screener test. Outputs → debug_logs/run_3_*.
# Run from project root:  bash scripts/run_linux_commands_3.sh
# Do NOT use sudo — script uses git and venv.
set -e
cd "$(dirname "$0")/.."

git pull origin main
source venv/bin/activate

mkdir -p debug_logs
echo "=== $(date '+%Y-%m-%dT%H:%M:%S') ===" > debug_logs/run_3_env_info.txt
python3 --version >> debug_logs/run_3_env_info.txt
python3 -c "import sys; print('Prefix:', sys.prefix)" >> debug_logs/run_3_env_info.txt
env | grep -E '^(MAX_STOCKS|SCREENER|ENABLE_SCREENER|TOP_STOCKS|MIN_STOCK|VENV|PATH)=' 2>/dev/null | sort >> debug_logs/run_3_env_info.txt || true

{
  echo "=== Screener test (batch, small run) ==="
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
  MAX_STOCKS_TO_SCAN=80 SCREENER_BATCH_SIZE=80 SCREENER_TEST_MAX_STOCKS=5 python3 run_screener_test.py 2>&1 || true
} | tee debug_logs/run_3_results.txt

git add debug_logs/
git status
git commit -m "chore(debug): run 3 screener results for Cursor" || true
git push origin main

echo ""
echo "=== Done. Check debug_logs/run_3_results.txt (or run_3_env_info.txt). ==="
