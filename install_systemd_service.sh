#!/bin/bash

##############################################################################
# Systemd Service Installation Script for market-pie5-bot
# 
# This script installs the trading bot as a systemd service that will:
# - Auto-start on system boot
# - Auto-restart if it crashes
# - Log output to journalctl
# - Enable monitoring via 'systemctl status market-pie5-bot'
#
# Usage: sudo bash install_systemd_service.sh
#
##############################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BOT_USER="${BOT_USER:-operator}"
BOT_GROUP="${BOT_GROUP:-operator}"
BOT_HOME="/home/${BOT_USER}/market-bot/market-pie5-bot"
SERVICE_FILE="${BOT_HOME}/market-pie5-bot.service"
SYSTEMD_DEST="/etc/systemd/system/market-pie5-bot.service"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Market-Pie5-Bot Systemd Installation${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}ERROR: This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Verify bot installation
if [ ! -f "${BOT_HOME}/main.py" ]; then
    echo -e "${RED}ERROR: Bot not found at ${BOT_HOME}${NC}"
    exit 1
fi

if [ ! -f "${SERVICE_FILE}" ]; then
    echo -e "${RED}ERROR: Service file not found at ${SERVICE_FILE}${NC}"
    exit 1
fi

echo -e "${YELLOW}Configuration:${NC}"
echo "  Bot user: ${BOT_USER}"
echo "  Bot home: ${BOT_HOME}"
echo "  Service file: ${SERVICE_FILE}"
echo "  Systemd destination: ${SYSTEMD_DEST}"
echo ""

# Verify user exists
if ! id "${BOT_USER}" &>/dev/null; then
    echo -e "${RED}ERROR: User ${BOT_USER} not found${NC}"
    echo "Create the user first with: sudo useradd -m -s /bin/bash ${BOT_USER}"
    exit 1
fi

# Copy service file
echo -e "${YELLOW}Installing systemd service file...${NC}"
cp "${SERVICE_FILE}" "${SYSTEMD_DEST}"
chmod 644 "${SYSTEMD_DEST}"
echo -e "${GREEN}✓ Service file installed${NC}"

# Verify .env file exists
if [ ! -f "${BOT_HOME}/.env" ]; then
    echo -e "${YELLOW}WARNING: .env file not found at ${BOT_HOME}/.env${NC}"
    echo "The bot will use default environment variables from .env.example"
    echo "Please configure your .env file before starting the service"
fi

# Check if virtual environment exists
if [ ! -d "${BOT_HOME}/venv" ]; then
    echo -e "${YELLOW}WARNING: Virtual environment not found at ${BOT_HOME}/venv${NC}"
    echo "Please create it with: cd ${BOT_HOME} && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    echo ""
fi

# Reload systemd daemon
echo -e "${YELLOW}Reloading systemd daemon...${NC}"
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd daemon reloaded${NC}"

# Display next steps
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Installation Complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${YELLOW}Next Steps:${NC}\n"

echo "1. Enable auto-start on boot:"
echo -e "   ${BLUE}sudo systemctl enable market-pie5-bot${NC}\n"

echo "2. Start the service manually:"
echo -e "   ${BLUE}sudo systemctl start market-pie5-bot${NC}\n"

echo "3. Check service status:"
echo -e "   ${BLUE}systemctl status market-pie5-bot${NC}\n"

echo "4. View logs in real-time:"
echo -e "   ${BLUE}journalctl -u market-pie5-bot -f${NC}\n"

echo "5. View last 50 log lines:"
echo -e "   ${BLUE}journalctl -u market-pie5-bot -n 50${NC}\n"

echo -e "${YELLOW}Service Management Commands:${NC}\n"

echo -e "  Start service:"
echo -e "    ${BLUE}sudo systemctl start market-pie5-bot${NC}"

echo -e "  Stop service:"
echo -e "    ${BLUE}sudo systemctl stop market-pie5-bot${NC}"

echo -e "  Restart service:"
echo -e "    ${BLUE}sudo systemctl restart market-pie5-bot${NC}"

echo -e "  Enable auto-start on boot:"
echo -e "    ${BLUE}sudo systemctl enable market-pie5-bot${NC}"

echo -e "  Disable auto-start on boot:"
echo -e "    ${BLUE}sudo systemctl disable market-pie5-bot${NC}"

echo -e "  Check status:"
echo -e "    ${BLUE}systemctl status market-pie5-bot${NC}"

echo ""
echo -e "${YELLOW}Logging:${NC}\n"

echo -e "  Follow logs live:"
echo -e "    ${BLUE}journalctl -u market-pie5-bot -f${NC}"

echo -e "  View last N lines:"
echo -e "    ${BLUE}journalctl -u market-pie5-bot -n 100${NC}"

echo -e "  View logs since last boot:"
echo -e "    ${BLUE}journalctl -u market-pie5-bot -b${NC}"

echo -e "  View logs for specific time range:"
echo -e "    ${BLUE}journalctl -u market-pie5-bot --since '2 hours ago'${NC}"

echo ""
echo -e "${GREEN}Installation successful!${NC}"
echo ""

# Optional: offer to enable and start the service
read -p "Would you like to enable and start the service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Enabling service...${NC}"
    systemctl enable market-pie5-bot
    echo -e "${GREEN}✓ Service enabled${NC}"
    
    echo -e "${YELLOW}Starting service...${NC}"
    systemctl start market-pie5-bot
    echo -e "${GREEN}✓ Service started${NC}"
    
    echo ""
    echo -e "${YELLOW}Service status:${NC}"
    systemctl status market-pie5-bot
fi
