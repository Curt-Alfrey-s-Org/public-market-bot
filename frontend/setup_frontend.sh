#!/bin/bash
# Setup React frontend
# Run this script to set up the frontend

set -e

echo "Setting up React frontend..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    echo "Please install Node.js 18+ first:"
    echo "  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -"
    echo "  sudo apt-get install -y nodejs"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"
echo ""

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    echo "✅ Dependencies installed"
else
    echo "Dependencies already installed"
fi

# Initialize Tailwind CSS if not already done
if [ ! -f "tailwind.config.js" ]; then
    echo "Initializing Tailwind CSS..."
    npx tailwindcss init -p
    echo "✅ Tailwind CSS initialized"
fi

echo ""
echo "✅ Frontend setup complete!"
echo ""
echo "To start the development server:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "The frontend will be available at: http://localhost:5173"
echo ""
