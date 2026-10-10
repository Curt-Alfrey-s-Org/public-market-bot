#!/bin/bash
# Install Desktop Icons for Market Pie5 Bot
# This script installs desktop entry files for both Web GUI and Desktop GUI

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Market Pie5 Bot - Desktop Icons Installer               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get script directory (repository root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Detect installation path
INSTALL_PATH="$SCRIPT_DIR"
echo -e "${BLUE}Installation path detected: ${GREEN}$INSTALL_PATH${NC}"

# Create applications directory if it doesn't exist
APPS_DIR="$HOME/.local/share/applications"
if [ ! -d "$APPS_DIR" ]; then
    echo -e "${YELLOW}Creating applications directory...${NC}"
    mkdir -p "$APPS_DIR"
fi

# Function to update desktop file with correct path
update_desktop_file() {
    local desktop_file="$1"
    local temp_file="${desktop_file}.tmp"
    
    # Replace the default path with actual installation path
    sed "s|/home/pi/market-pie5-bot|$INSTALL_PATH|g" "$desktop_file" > "$temp_file"
    mv "$temp_file" "$desktop_file"
}

# Install Web GUI desktop file
echo ""
echo -e "${BLUE}Installing Web GUI desktop icon...${NC}"
if [ -f "market-pie5-web-gui.desktop" ]; then
    # Update path in desktop file
    cp market-pie5-web-gui.desktop /tmp/market-pie5-web-gui.desktop.tmp
    sed "s|/home/pi/market-pie5-bot|$INSTALL_PATH|g" /tmp/market-pie5-web-gui.desktop.tmp > "$APPS_DIR/market-pie5-web-gui.desktop"
    chmod +x "$APPS_DIR/market-pie5-web-gui.desktop"
    echo -e "${GREEN}✓ Web GUI desktop icon installed${NC}"
    echo -e "  Name: ${YELLOW}Market Pie5 Web Dashboard${NC}"
else
    echo -e "${RED}✗ market-pie5-web-gui.desktop not found${NC}"
fi

# Install Desktop GUI desktop file
echo ""
echo -e "${BLUE}Installing Desktop GUI icon...${NC}"
if [ -f "market-pie5-bot.desktop" ]; then
    # Update path in desktop file
    cp market-pie5-bot.desktop /tmp/market-pie5-bot.desktop.tmp
    sed "s|/home/pi/market-pie5-bot|$INSTALL_PATH|g" /tmp/market-pie5-bot.desktop.tmp > "$APPS_DIR/market-pie5-bot.desktop"
    chmod +x "$APPS_DIR/market-pie5-bot.desktop"
    echo -e "${GREEN}✓ Desktop GUI icon installed${NC}"
    echo -e "  Name: ${YELLOW}Market Pie5 Bot (Desktop GUI)${NC}"
else
    echo -e "${RED}✗ market-pie5-bot.desktop not found${NC}"
fi

# Update desktop database
echo ""
echo -e "${BLUE}Updating desktop database...${NC}"
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
    echo -e "${GREEN}✓ Desktop database updated${NC}"
else
    echo -e "${YELLOW}⚠ update-desktop-database not found, icons may not appear immediately${NC}"
fi

# Clean up temp files
rm -f /tmp/market-pie5-*.desktop.tmp

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Installation Complete!                                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Desktop icons have been installed to:${NC}"
echo -e "  ${GREEN}$APPS_DIR${NC}"
echo ""
echo -e "${BLUE}You should now see two icons in your application menu:${NC}"
echo -e "  1. ${YELLOW}Market Pie5 Web Dashboard${NC} - Browser-based interface (Recommended)"
echo -e "  2. ${YELLOW}Market Pie5 Bot (Desktop GUI)${NC} - Desktop Tkinter interface"
echo ""
echo -e "${BLUE}Look for them under:${NC}"
echo -e "  - Finance category"
echo -e "  - Office category"
echo -e "  - Or search for 'Market Pie5' or 'trading' in your application launcher"
echo ""
echo -e "${YELLOW}Note: If icons don't appear immediately, try logging out and back in,${NC}"
echo -e "${YELLOW}or restart your desktop environment.${NC}"
echo ""
