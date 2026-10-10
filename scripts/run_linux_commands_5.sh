#!/usr/bin/env bash
# Run 5: Cleanup .env2 file and verify. Outputs → debug_logs/run_5_*.
# Run from project root:  bash scripts/run_linux_commands_5.sh
# Do NOT use sudo — script uses git and venv.
set -e
cd "$(dirname "$0")/.."

git pull origin main
source venv/bin/activate

mkdir -p debug_logs
echo "=== $(date '+%Y-%m-%dT%H:%M:%S') ===" > debug_logs/run_5_env_info.txt
python3 --version >> debug_logs/run_5_env_info.txt
python3 -c "import sys; print('Prefix:', sys.prefix)" >> debug_logs/run_5_env_info.txt

{
  echo "=== Cleanup .env2 file ==="
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
  echo ""
  if [ -f .env2 ]; then
    echo "Found .env2 file, deleting..."
    rm -f .env2
    echo "  ✓ Deleted .env2"
  else
    echo ".env2 not found (already deleted or never existed)"
  fi
  echo ""
  echo "Verifying .env2 is in .gitignore:"
  if grep -q "\.env2" .gitignore; then
    echo "  ✓ .env2 is in .gitignore"
  else
    echo "  ✗ .env2 not found in .gitignore"
  fi
  echo ""
  echo "Checking for other .env* files:"
  ls -la .env* 2>/dev/null | grep -v ".env.key" | grep -v ".env.example" || echo "  (no other .env files found)"
  echo ""
  echo "=== Cleanup complete ==="
} | tee debug_logs/run_5_results.txt

git add debug_logs/ .gitignore
git status
git commit -m "chore: cleanup .env2, add to .gitignore" || true
git push origin main

echo ""
echo "=== Done. Check debug_logs/run_5_results.txt (or run_5_env_info.txt). ==="
