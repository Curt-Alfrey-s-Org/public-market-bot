#!/bin/bash
# Setup virtual environment for FastAPI
# This is the recommended approach

set -e

echo "Setting up virtual environment for FastAPI..."
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip in venv
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing FastAPI dependencies..."
pip install -r requirements-api.txt

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "To use the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "To start the API server:"
echo "  source venv/bin/activate"
echo "  ./start_api.sh"
echo ""
