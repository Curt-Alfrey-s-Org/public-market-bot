#!/usr/bin/env bash
# Run 6: Verify Top Performers Feed refactor. Outputs → debug_logs/run_6_*.
# Run from project root:  bash scripts/run_linux_commands_6.sh
# Do NOT use sudo — script uses git and venv.
set -e
cd "$(dirname "$0")/.."

git pull origin main
source venv/bin/activate

mkdir -p debug_logs
echo "=== $(date '+%Y-%m-%dT%H:%M:%S') ===" > debug_logs/run_6_env_info.txt
python3 --version >> debug_logs/run_6_env_info.txt
python3 -c "import sys; print('Prefix:', sys.prefix)" >> debug_logs/run_6_env_info.txt

{
  echo "=== Top Performers Feed Refactor - Verification ==="
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
  echo ""
  echo "1. Checking for top_performers_feed.py module:"
  if [ -f top_performers_feed.py ]; then
    echo "  ✓ top_performers_feed.py exists"
    echo "  - Checking for TopPerformersFeed class:"
    grep -n "class TopPerformersFeed" top_performers_feed.py && echo "    ✓ Found" || echo "    ✗ Not found"
    echo "  - Checking for get_top_performers_feed function:"
    grep -n "def get_top_performers_feed" top_performers_feed.py && echo "    ✓ Found" || echo "    ✗ Not found"
  else
    echo "  ✗ top_performers_feed.py not found"
  fi
  echo ""
  echo "2. Checking web_gui.py integration:"
  echo "  - Checking for feed import:"
  grep -n "from top_performers_feed import" web_gui.py | head -2 && echo "    ✓ Found" || echo "    ✗ Not found"
  echo "  - Checking for feed-container in UI:"
  grep -n "feed-container" web_gui.py | head -2 && echo "    ✓ Found" || echo "    ✗ Not found"
  echo "  - Checking for feed callbacks:"
  grep -n "def update_feed_display" web_gui.py && echo "    ✓ Found" || echo "    ✗ Not found"
  echo "  - Checking for feed priority in bot loop:"
  grep -n "Top Performers Feed" web_gui.py | head -2 && echo "    ✓ Found" || echo "    ✗ Not found"
  echo ""
  echo "3. Checking bot loop priority order (Feed → Watchlist → Screener):"
  grep -A 10 "Priority order: Feed" web_gui.py | head -5 || echo "  ✗ Priority order not found"
  echo ""
  echo "4. Checking .env.example for feed config:"
  grep "ENABLE_TOP_PERFORMERS_FEED" .env.example && echo "  ✓ Found" || echo "  ✗ Not found"
  echo ""
  echo "5. Python syntax check (import test):"
  python3 -c "
import sys
try:
    from top_performers_feed import get_top_performers_feed, FEED_ENABLED, get_feed_symbols
    print('  ✓ top_performers_feed imports successfully')
    print(f'  - FEED_ENABLED: {FEED_ENABLED}')
except ImportError as e:
    print(f'  ✗ Import failed: {e}')
    sys.exit(1)
except Exception as e:
    print(f'  ✗ Error: {e}')
    sys.exit(1)
" 2>&1 || echo "  ✗ Import failed"
  echo ""
  echo "6. Checking feed module structure:"
  python3 -c "
try:
    from top_performers_feed import TopPerformersFeed
    feed = TopPerformersFeed()
    print('  ✓ TopPerformersFeed can be instantiated')
    print(f'  - get_feed_symbols(): {feed.get_feed_symbols()}')
    print(f'  - get_feed_data(): {len(feed.get_feed_data())} stocks')
    stats = feed.get_stats()
    print(f'  - Stats: {stats}')
except Exception as e:
    print(f'  ✗ Error: {e}')
    import traceback
    traceback.print_exc()
" 2>&1 || echo "  ✗ Feed module test failed"
  echo ""
  echo "7. Checking web_gui.py can import feed:"
  python3 -c "
import sys
sys.path.insert(0, '.')
try:
    # Try to import the feed-related code from web_gui
    import web_gui
    print('  ✓ web_gui.py imports successfully')
    # Check if feed_instance exists
    if hasattr(web_gui, 'feed_instance'):
        print('  ✓ feed_instance exists in web_gui')
    else:
        print('  ⚠ feed_instance not found (may be None if feed disabled)')
except Exception as e:
    print(f'  ✗ Import failed: {e}')
    import traceback
    traceback.print_exc()
" 2>&1 || echo "  ✗ web_gui import test failed"
  echo ""
  echo "=== Verification complete ==="
} | tee debug_logs/run_6_results.txt

git add debug_logs/ top_performers_feed.py
git status
git commit -m "chore(debug): run 6 Top Performers Feed refactor verification for Cursor" || true
git push origin main

echo ""
echo "=== Done. Check debug_logs/run_6_results.txt (or run_6_env_info.txt). ==="
