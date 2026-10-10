#!/bin/bash
# Convenience script to collect error logs
# Usage: ./collect_logs.sh [output_filename]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

OUTPUT_FILE="${1:-errorlogs.txt}"

echo "Collecting error logs to: $OUTPUT_FILE"
python3 collect_errorlogs.py "$OUTPUT_FILE"

echo ""
echo "Log collection complete!"
echo ""
echo "To commit and push to remote:"
echo "  git add $OUTPUT_FILE"
echo "  git commit -m 'Update error logs for Copilot analysis'"
echo "  git push"
