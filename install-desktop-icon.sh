#!/bin/bash
# Install Market Pie5 Web Dashboard desktop icon for all users
# This script installs the desktop file system-wide and optionally sets up autostart

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Market Pie5 Bot - Desktop Icon Installer                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root for system-wide installation
if [ "$EUID" -eq 0 ]; then
    INSTALL_MODE="system"
else
    INSTALL_MODE="user"
    echo -e "${YELLOW}Note: Running as regular user. Will install for current user only.${NC}"
    echo -e "${YELLOW}      For system-wide installation, run with sudo.${NC}"
    echo ""
fi

# Check if desktop file exists
if [ ! -f "market-pie5-web-gui.desktop" ]; then
    echo -e "${RED}Error: market-pie5-web-gui.desktop not found in current directory${NC}"
    exit 1
fi

# Check if icon exists
if [ ! -f "market-pie5-icon.svg" ]; then
    echo -e "${YELLOW}Warning: market-pie5-icon.svg not found${NC}"
    ICON_AVAILABLE=false
else
    ICON_AVAILABLE=true
fi

# Install launcher script (system-wide only)
if [ "$INSTALL_MODE" = "system" ]; then
    echo -e "${BLUE}Installing launcher script...${NC}"
    
    # Copy launcher script to /usr/local/bin
    if [ -f "launch-web-gui.sh" ]; then
        cp "launch-web-gui.sh" "/usr/local/bin/market-pie5-launch-web-gui"
        chmod 755 "/usr/local/bin/market-pie5-launch-web-gui"
        echo -e "${GREEN}✓ Launcher script installed to /usr/local/bin${NC}"
    else
        echo -e "${YELLOW}Warning: launch-web-gui.sh not found${NC}"
        echo -e "${YELLOW}Creating launcher script...${NC}"
        
        # Create launcher script that finds installation directory
        cat > /usr/local/bin/market-pie5-launch-web-gui << 'LAUNCHER_EOF'
#!/bin/bash
# Universal launcher for Market Pie5 Web Dashboard
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POSSIBLE_DIRS=(
    "$HOME/market-pie5-bot"
    "$HOME/market-bot/market-pie5-bot"
    "/opt/market-pie5-bot"
    "/usr/local/market-pie5-bot"
    "/home/operator/market-pie5-bot"
    "/home/pi/market-pie5-bot"
)
INSTALL_DIR=""
for dir in "${POSSIBLE_DIRS[@]}"; do
    if [ -f "$dir/start_web_gui.sh" ]; then
        INSTALL_DIR="$dir"
        break
    fi
done
if [ -z "$INSTALL_DIR" ]; then
    echo "Error: Could not find Market Pie5 Bot installation"
    exit 1
fi
cd "$INSTALL_DIR" && exec ./start_web_gui.sh
LAUNCHER_EOF
        chmod 755 "/usr/local/bin/market-pie5-launch-web-gui"
        echo -e "${GREEN}✓ Launcher script created${NC}"
    fi
fi

# Install desktop file
echo -e "${BLUE}Installing desktop file...${NC}"

if [ "$INSTALL_MODE" = "system" ]; then
    # System-wide installation
    DESKTOP_DIR="/usr/share/applications"
    ICON_DIR="/usr/share/pixmaps"
    
    # Copy desktop file
    cp "market-pie5-web-gui.desktop" "$DESKTOP_DIR/"
    chmod 644 "$DESKTOP_DIR/market-pie5-web-gui.desktop"
    echo -e "${GREEN}✓ Desktop file installed to $DESKTOP_DIR${NC}"
    
    # Copy icon
    if [ "$ICON_AVAILABLE" = true ]; then
        cp "market-pie5-icon.svg" "$ICON_DIR/market-pie5-icon.svg"
        chmod 644 "$ICON_DIR/market-pie5-icon.svg"
        echo -e "${GREEN}✓ Icon installed to $ICON_DIR${NC}"
    fi
    
    # Update desktop database
    update-desktop-database "$DESKTOP_DIR"
    echo -e "${GREEN}✓ Desktop database updated${NC}"
    
else
    # User-specific installation - need to update Exec path
    DESKTOP_DIR="$HOME/.local/share/applications"
    ICON_DIR="$HOME/.local/share/icons"
    
    # Create directories if they don't exist
    mkdir -p "$DESKTOP_DIR"
    mkdir -p "$ICON_DIR"
    
    # Create user-specific desktop file with correct path
    cat > "$DESKTOP_DIR/market-pie5-web-gui.desktop" << DESKTOP_EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Market Pie5 Web Dashboard
Comment=Browser-based trading dashboard - Compatible with Raspberry Pi 5, Linux Mint, Ubuntu, and Debian
Exec=$SCRIPT_DIR/start_web_gui.sh
Icon=$SCRIPT_DIR/market-pie5-icon.svg
Terminal=true
Categories=Finance;Office;Network;
Keywords=trading;stock;bot;finance;web;dashboard;linux;
StartupNotify=true
StartupWMClass=market-pie5-web-gui
Path=$SCRIPT_DIR
X-Desktop-File-Install-Version=0.26
DESKTOP_EOF
    
    chmod 644 "$DESKTOP_DIR/market-pie5-web-gui.desktop"
    echo -e "${GREEN}✓ Desktop file installed to $DESKTOP_DIR${NC}"
    
    # Copy icon
    if [ "$ICON_AVAILABLE" = true ]; then
        cp "market-pie5-icon.svg" "$ICON_DIR/market-pie5-icon.svg"
        chmod 644 "$ICON_DIR/market-pie5-icon.svg"
        echo -e "${GREEN}✓ Icon installed to $ICON_DIR${NC}"
    fi
    
    # Update desktop database
    update-desktop-database "$DESKTOP_DIR"
    echo -e "${GREEN}✓ Desktop database updated${NC}"
fi

echo ""

# Ask about autostart
read -p "Do you want to set up autostart on login? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Setting up autostart...${NC}"
    
    if [ "$INSTALL_MODE" = "system" ]; then
        # System-wide autostart
        AUTOSTART_DIR="/etc/xdg/autostart"
        cp "market-pie5-web-gui.desktop" "$AUTOSTART_DIR/"
        chmod 644 "$AUTOSTART_DIR/market-pie5-web-gui.desktop"
        update-desktop-database "$AUTOSTART_DIR"
        echo -e "${GREEN}✓ Autostart configured for all users (system-wide)${NC}"
        echo -e "${YELLOW}  Note: The application will start automatically for all users on login${NC}"
    else
        # User-specific autostart
        AUTOSTART_DIR="$HOME/.config/autostart"
        mkdir -p "$AUTOSTART_DIR"
        cp "market-pie5-web-gui.desktop" "$AUTOSTART_DIR/"
        chmod 644 "$AUTOSTART_DIR/market-pie5-web-gui.desktop"
        update-desktop-database "$AUTOSTART_DIR"
        echo -e "${GREEN}✓ Autostart configured for current user${NC}"
        echo -e "${YELLOW}  Note: The application will start automatically on login${NC}"
    fi
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Installation Complete!                                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}The Market Pie5 Web Dashboard icon should now appear in your${NC}"
echo -e "${BLUE}application menu under 'Office' or 'Finance' categories.${NC}"
echo ""

if [ "$INSTALL_MODE" = "system" ]; then
    echo -e "${YELLOW}To install for all users on startup:${NC}"
    echo -e "  Run this script with sudo to install system-wide"
    echo -e "  Or copy the desktop file to /etc/xdg/autostart/"
else
    echo -e "${YELLOW}To install for all users:${NC}"
    echo -e "  sudo ./install-desktop-icon.sh"
fi

echo ""
