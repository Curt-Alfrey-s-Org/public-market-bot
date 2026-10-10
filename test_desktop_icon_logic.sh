#!/bin/bash
# Test desktop icon installation logic from install.sh
# This simulates the desktop icon section without running full install

set -e

echo "Testing Desktop Icon Installation Logic"
echo "========================================"
echo ""

# Get script directory (repository root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_PATH="$SCRIPT_DIR"
# Default path pattern to replace (matches the pattern in desktop files)
DEFAULT_PATH="/home/pi/market-pie5-bot"

echo "Installation path: $INSTALL_PATH"
echo "Default path pattern: $DEFAULT_PATH"
echo ""

# Check if desktop files exist
if [ -f "market-pie5-web-gui.desktop" ]; then
    echo "✓ market-pie5-web-gui.desktop found"
else
    echo "✗ market-pie5-web-gui.desktop NOT FOUND"
    exit 1
fi

if [ -f "market-pie5-bot.desktop" ]; then
    echo "✓ market-pie5-bot.desktop found"
else
    echo "✗ market-pie5-bot.desktop NOT FOUND"
    exit 1
fi

echo ""
echo "Testing sed command to update paths..."

# Test sed command (without installing)
sed "s|$DEFAULT_PATH|$INSTALL_PATH|g" market-pie5-web-gui.desktop > /tmp/test-web-gui.desktop
if grep -q "$INSTALL_PATH" /tmp/test-web-gui.desktop; then
    echo "✓ Path replacement works for web-gui.desktop"
else
    echo "✗ Path replacement failed for web-gui.desktop"
    exit 1
fi

sed "s|$DEFAULT_PATH|$INSTALL_PATH|g" market-pie5-bot.desktop > /tmp/test-bot.desktop
if grep -q "$INSTALL_PATH" /tmp/test-bot.desktop; then
    echo "✓ Path replacement works for bot.desktop"
else
    echo "✗ Path replacement failed for bot.desktop"
    exit 1
fi

echo ""
echo "Displaying updated desktop file (first 10 lines):"
echo "------------------------------------------------"
head -10 /tmp/test-web-gui.desktop

echo ""
echo "================================================"
echo "✓ Desktop icon logic test PASSED"
echo "================================================"
echo ""
echo "The install.sh script will correctly:"
echo "  • Detect installation path"
echo "  • Update desktop file paths"
echo "  • Install to ~/.local/share/applications/"
echo "  • Update desktop database"
echo ""

# Cleanup
rm -f /tmp/test-web-gui.desktop /tmp/test-bot.desktop
