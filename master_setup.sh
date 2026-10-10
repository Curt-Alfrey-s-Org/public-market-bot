#!/bin/bash
# Master Setup Script for market-pie5-bot Web GUI
# Sets up both API backend and React frontend with proper dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   market-pie5-bot Master Setup                             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo "Please install Python 3: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠ Node.js not found${NC}"
    echo "Node.js is required for the React frontend."
    echo "Install it with: sudo apt install nodejs npm"
    echo ""
    read -p "Continue without Node.js setup? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    SKIP_FRONTEND=true
fi

# Step 1: Create Python virtual environment
echo -e "${BLUE}[1/4] Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Step 2: Install Python dependencies
echo ""
echo -e "${BLUE}[2/4] Installing Python dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
if [ -f "requirements-api.txt" ]; then
    pip install -r requirements-api.txt -q
fi
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Step 3: Setup frontend
if [ "$SKIP_FRONTEND" != "true" ]; then
    echo ""
    echo -e "${BLUE}[3/4] Setting up React frontend...${NC}"
    if [ -d "frontend" ]; then
        cd frontend
        
        # Check if node_modules exists
        if [ ! -d "node_modules" ]; then
            echo "Installing npm packages..."
            npm install
        else
            echo -e "${GREEN}✓ npm packages already installed${NC}"
        fi
        
        cd ..
        echo -e "${GREEN}✓ Frontend setup complete${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend directory not found, skipping${NC}"
    fi
else
    echo ""
    echo -e "${YELLOW}[3/4] Skipping frontend setup (Node.js not available)${NC}"
fi

# Step 4: Create .env if needed
echo ""
echo -e "${BLUE}[4/4] Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${YELLOW}⚠ Please edit .env with your API keys and configuration${NC}"
    else
        echo -e "${YELLOW}⚠ No .env.example found${NC}"
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Done
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✓ Setup complete!                                       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Port Configuration:${NC}"
echo -e "  API Backend:  ${GREEN}http://localhost:8000${NC}"
echo -e "  Frontend:     ${GREEN}http://localhost:5173${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Configure your .env file with API keys"
echo "2. Start the web GUI: ./start_web_gui.sh"
echo "   OR"
echo "   Start API: ./start_api.sh"
echo "   Start frontend: cd frontend && npm run dev"
echo ""