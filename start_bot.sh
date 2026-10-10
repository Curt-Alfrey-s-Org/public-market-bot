#!/bin/bash
# Market Pie5 Bot Launcher Script
# This script makes it easy to launch the trading bot GUI on Raspberry Pi 5

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to handle errors and keep terminal open
show_error() {
    local error_msg="$1"
    echo ""
    echo "========================================"
    echo "ERROR: $error_msg"
    echo "========================================"
    echo ""
    if [ $# -gt 1 ]; then
        shift
        for msg in "$@"; do
            echo "$msg"
        done
        echo ""
    fi
    echo "Press Enter to close this window..."
    read
    exit 1
}

echo "========================================"
echo "Market Pie5 Trading Bot Launcher"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv || show_error "Failed to create virtual environment" "Please ensure python3-venv is installed"
    echo "Installing dependencies..."
    ./venv/bin/pip install -r requirements.txt || show_error "Failed to install dependencies"
fi

# Enable strict error handling after venv check
set -e

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "NOTE: Using paper trading mode. Edit .env file to add your API keys."
    echo ""
fi

# Check if running interactively (from terminal) or non-interactively (from desktop icon)
if [ -t 0 ]; then
    # Interactive mode - show menu
    echo "Select launch mode:"
    echo "1) GUI Mode (Recommended)"
    echo "2) Command-line Mode"
    echo "3) Exit"
    echo ""
    read -p "Enter choice [1-3]: " choice
    
    case $choice in
        1)
            echo ""
            echo "Starting GUI mode..."
            echo "Close the GUI window to exit."
            echo ""
            ./venv/bin/python3 gui.py
            ;;
        2)
            echo ""
            echo "Starting command-line mode..."
            echo "Press Ctrl+C to exit."
            echo ""
            ./venv/bin/python3 main.py
            ;;
        3)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid choice. Exiting..."
            exit 1
            ;;
    esac
else
    # Non-interactive mode (desktop icon) - launch GUI directly
    echo "Starting Desktop GUI mode..."
    echo "Close the GUI window to exit."
    echo ""
    
    # Launch GUI and keep terminal open on error
    ./venv/bin/python3 gui.py || show_error "GUI failed to start" \
        "Please check:" \
        "1. Python dependencies are installed" \
        "2. Display is available (DISPLAY variable set)" \
        "3. Tkinter is installed (python3-tk package)"
fi

echo ""
echo "========================================"
echo "Bot stopped."
echo "========================================"
