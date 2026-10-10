#!/bin/bash
# Test script for default browser auto-launch functionality
# This validates the changes to start_web_gui.sh

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Testing default browser auto-launch functionality...${NC}"
echo ""

# Test 1: Check if xdg-open is available (Linux standard)
echo -e "${BLUE}Test 1: Checking for browser launcher commands...${NC}"
if command -v xdg-open &> /dev/null; then
    echo -e "${GREEN}✓ xdg-open found (Linux standard)${NC}"
elif command -v open &> /dev/null; then
    echo -e "${GREEN}✓ open found (macOS)${NC}"
else
    echo -e "${RED}✗ No browser launcher found (xdg-open or open) - browser will not auto-launch${NC}"
fi
echo ""

# Test 2: Check if curl is available for server check
echo -e "${BLUE}Test 2: Checking for curl (needed for server check)...${NC}"
if command -v curl &> /dev/null; then
    echo -e "${GREEN}✓ curl found${NC}"
else
    echo -e "${RED}✗ curl not found - server readiness check may fail${NC}"
fi
echo ""

# Test 3: Validate script syntax
echo -e "${BLUE}Test 3: Validating start_web_gui.sh syntax...${NC}"
if bash -n start_web_gui.sh; then
    echo -e "${GREEN}✓ Script syntax is valid${NC}"
else
    echo -e "${RED}✗ Script has syntax errors${NC}"
    exit 1
fi
echo ""

# Test 4: Check if script has required functions
echo -e "${BLUE}Test 4: Checking for required functions...${NC}"
if grep -q "wait_for_server()" start_web_gui.sh; then
    echo -e "${GREEN}✓ wait_for_server() function found${NC}"
else
    echo -e "${RED}✗ wait_for_server() function missing${NC}"
    exit 1
fi

if grep -q "cleanup()" start_web_gui.sh; then
    echo -e "${GREEN}✓ cleanup() function found${NC}"
else
    echo -e "${RED}✗ cleanup() function missing${NC}"
    exit 1
fi
echo ""

# Test 5: Check if script launches browser with default launcher
echo -e "${BLUE}Test 5: Checking for browser launch code...${NC}"
if grep -q "xdg-open.*http://localhost:8050" start_web_gui.sh; then
    echo -e "${GREEN}✓ xdg-open browser launch code found${NC}"
elif grep -q "open.*http://localhost:8050" start_web_gui.sh; then
    echo -e "${GREEN}✓ open (macOS) browser launch code found${NC}"
else
    echo -e "${RED}✗ Browser launch code missing${NC}"
    exit 1
fi
echo ""

# Test 6: Check if script has signal handlers
echo -e "${BLUE}Test 6: Checking for signal handlers...${NC}"
if grep -q "trap.*cleanup.*INT" start_web_gui.sh; then
    echo -e "${GREEN}✓ Signal handler for Ctrl+C found${NC}"
else
    echo -e "${RED}✗ Signal handler missing${NC}"
    exit 1
fi
echo ""

# Test 7: Check web_gui.py has splash screen
echo -e "${BLUE}Test 7: Checking for splash screen in web_gui.py...${NC}"
if grep -q "splash-screen" web_gui.py; then
    echo -e "${GREEN}✓ Splash screen found in web_gui.py${NC}"
else
    echo -e "${RED}✗ Splash screen missing in web_gui.py${NC}"
    exit 1
fi

if grep -q "Enter Dashboard" web_gui.py; then
    echo -e "${GREEN}✓ Enter Dashboard button found${NC}"
else
    echo -e "${RED}✗ Enter Dashboard button missing${NC}"
    exit 1
fi
echo ""

# Test 8: Check for webbrowser module import and usage
echo -e "${BLUE}Test 8: Checking for webbrowser module in web_gui.py...${NC}"
if grep -q "import webbrowser" web_gui.py; then
    echo -e "${GREEN}✓ webbrowser module imported${NC}"
else
    echo -e "${RED}✗ webbrowser module import missing${NC}"
    exit 1
fi

if grep -q "webbrowser.open" web_gui.py; then
    echo -e "${GREEN}✓ webbrowser.open() usage found${NC}"
else
    echo -e "${RED}✗ webbrowser.open() usage missing${NC}"
    exit 1
fi
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   All tests passed!                                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}The changes should work as expected:${NC}"
echo -e "  1. Double-click the desktop icon"
echo -e "  2. Server starts and waits for readiness"
echo -e "  3. Default web browser opens automatically"
echo -e "  4. Splash screen is displayed"
echo -e "  5. Click 'Enter Dashboard' button to enter"
echo ""
