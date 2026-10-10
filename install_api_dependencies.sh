#!/bin/bash
# Install FastAPI dependencies
# This script tries multiple methods to install dependencies

set -e

echo "Installing FastAPI dependencies..."
echo ""

# Method 1: Try pip3 directly
if command -v pip3 &> /dev/null; then
    echo "Method 1: Using pip3..."
    pip3 install --user fastapi uvicorn[standard] python-multipart pydantic websockets psutil
    echo "✅ Dependencies installed via pip3"
    exit 0
fi

# Method 2: Try python3 -m pip
if python3 -m pip --version &> /dev/null; then
    echo "Method 2: Using python3 -m pip..."
    python3 -m pip install --user fastapi uvicorn[standard] python-multipart pydantic websockets psutil
    echo "✅ Dependencies installed via python3 -m pip"
    exit 0
fi

# Method 3: Try apt (if available, though not recommended for Python packages)
if command -v apt &> /dev/null; then
    echo "Method 3: Attempting apt install (may not have all packages)..."
    echo "Note: FastAPI is typically not available via apt, pip is preferred"
    # apt install python3-fastapi python3-uvicorn 2>&1 || echo "apt method not available for these packages"
fi

# Method 4: Manual installation instructions
echo ""
echo "⚠️  Could not automatically install dependencies"
echo ""
echo "Please install manually using one of these methods:"
echo ""
echo "Option 1: Install pip3 first, then install packages:"
echo "  apt install python3-pip"
echo "  pip3 install --user -r requirements-api.txt"
echo ""
echo "Option 2: Use a virtual environment (recommended):"
echo "  python3 -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements-api.txt"
echo ""
echo "Option 3: Install system-wide (requires admin):"
echo "  sudo apt install python3-pip"
echo "  sudo pip3 install -r requirements-api.txt"
echo ""
exit 1
