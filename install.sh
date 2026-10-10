#!/bin/bash
set -e

echo "=== Market Pie5 Bot Installation Script ==="
echo "Compatible with Raspberry Pi 5, Linux Mint, Ubuntu, Debian, and other Debian-based distributions"
echo ""

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "Detected: $NAME $VERSION_ID"
    if [ -f /etc/linuxmint/info ]; then
        MINT_VERSION=$(grep RELEASE /etc/linuxmint/info | cut -d= -f2 2>/dev/null || echo "Unknown")
        echo "Linux Mint Version: $MINT_VERSION"
    fi
    echo ""
fi

# Update system packages
echo "Updating system packages..."
sudo apt update -y
sudo apt upgrade -y

# Install required packages
echo "Installing required packages..."
sudo apt install python3 python3-pip python3-venv git -y

# Optionally install python3-tk for desktop GUI
echo ""
echo "Installing optional GUI dependencies..."
sudo apt install python3-tk -y || echo "Warning: python3-tk not installed - desktop GUI may not work"

# Clone repository
echo ""
echo "Cloning repository..."
echo "Note: If this is a private repository, you'll need to authenticate with:"
echo "  Username: Your GitHub username"
echo "  Password: Your GitHub Personal Access Token (NOT your GitHub password)"
echo "  (Public repositories do not require authentication)"
echo ""

if [ -d "market-pie5-bot" ]; then
    echo "Directory 'market-pie5-bot' already exists. Skipping clone."
    cd market-pie5-bot
    git pull origin main || echo "Warning: Could not pull latest changes. Continuing with existing code."
else
    git clone https://github.com/operator/market-pie5-bot.git || {
        echo ""
        echo "=========================================="
        echo "ERROR: Failed to clone repository!"
        echo "=========================================="
        echo ""
        echo "If this is a PRIVATE repository, you need to authenticate:"
        echo ""
        echo "1. A GitHub Personal Access Token (PAT)"
        echo "   - Create one at: https://github.com/settings/tokens"
        echo "   - Required permission: 'repo' (Full control of private repositories)"
        echo ""
        echo "2. When prompted for credentials:"
        echo "   - Username: Your GitHub username"
        echo "   - Password: Use your PAT (NOT your GitHub password)"
        echo ""
        echo "Alternatively, clone with token in URL:"
        echo "   git clone https://operator@example.com/operator/market-pie5-bot.git"
        echo ""
        echo "If this is a PUBLIC repository and the clone failed, check:"
        echo "   - Your internet connection"
        echo "   - The repository URL"
        echo "   - Git is properly installed"
        echo ""
        exit 1
    }
    cd market-pie5-bot
fi

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
python3 -m venv venv || {
    echo ""
    echo "=========================================="
    echo "ERROR: Failed to create virtual environment!"
    echo "=========================================="
    echo ""
    echo "Please ensure python3-venv is installed:"
    echo "  sudo apt install python3-venv"
    echo ""
    exit 1
}

# Install Python dependencies in virtual environment
echo "Installing Python dependencies..."
./venv/bin/pip install -r requirements.txt || {
    echo ""
    echo "=========================================="
    echo "ERROR: Failed to install Python dependencies!"
    echo "=========================================="
    echo ""
    exit 1
}

# Install desktop icons
echo ""
echo "=========================================="
echo "Desktop Icons Installation"
echo "=========================================="
echo ""
echo "Would you like to install desktop application icons?"
echo "This will add Market Pie5 Bot to your application menu."
echo ""
read -p "Install desktop icons? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Installing desktop icons..."
    
    # Get script directory (repository root)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    INSTALL_PATH="$SCRIPT_DIR"
    
    # Create applications directory if it doesn't exist
    APPS_DIR="$HOME/.local/share/applications"
    mkdir -p "$APPS_DIR"
    
    # Install Web GUI desktop file
    if [ -f "market-pie5-web-gui.desktop" ]; then
        sed "s|/home/pi/market-pie5-bot|$INSTALL_PATH|g" market-pie5-web-gui.desktop > "$APPS_DIR/market-pie5-web-gui.desktop"
        chmod +x "$APPS_DIR/market-pie5-web-gui.desktop"
        echo "✓ Web GUI desktop icon installed"
    else
        echo "⚠ Warning: market-pie5-web-gui.desktop not found, skipping Web GUI icon"
    fi
    
    # Install Desktop GUI desktop file
    if [ -f "market-pie5-bot.desktop" ]; then
        sed "s|/home/pi/market-pie5-bot|$INSTALL_PATH|g" market-pie5-bot.desktop > "$APPS_DIR/market-pie5-bot.desktop"
        chmod +x "$APPS_DIR/market-pie5-bot.desktop"
        echo "✓ Desktop GUI icon installed"
    else
        echo "⚠ Warning: market-pie5-bot.desktop not found, skipping Desktop GUI icon"
    fi
    
    # Update desktop database
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$APPS_DIR" 2>/dev/null || true
        echo "✓ Desktop database updated"
    fi
    
    echo ""
    echo "Desktop icons installed successfully!"
    echo "Look for 'Market Pie5' in your application menu under Finance or Office."
else
    echo "Skipping desktop icons installation."
    echo "You can install them later by running: ./install_desktop_icons.sh"
fi

# Install ClamAV for security scanning
echo ""
echo "=========================================="
echo "ClamAV Security Scanning"
echo "=========================================="
echo ""
echo "Would you like to install ClamAV antivirus with automatic updates?"
echo "ClamAV provides virus scanning and malware detection for your system."
echo "Unattended updates will keep virus definitions current automatically."
echo ""
read -p "Install ClamAV with automatic updates? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Installing ClamAV and configuring automatic updates..."
    
    # Install ClamAV and related packages
    if sudo apt install clamav clamav-daemon clamav-freshclam -y; then
        if command -v freshclam &> /dev/null; then
            # Stop freshclam service if running
            sudo systemctl stop clamav-freshclam 2>/dev/null || true
            
            # Update virus definitions
            echo "Updating virus definitions (this may take a few minutes)..."
            sudo freshclam || echo "Warning: Initial virus definition update failed. The system will automatically retry every hour via the freshclam service."
            
            # Enable and start freshclam service for automatic updates
            if command -v systemctl &> /dev/null; then
                if ! sudo systemctl enable clamav-freshclam 2>/dev/null; then
                    echo "Warning: Failed to enable freshclam service. Automatic updates may not run at boot."
                fi

                if ! sudo systemctl start clamav-freshclam 2>/dev/null; then
                    echo "Warning: Failed to start freshclam service. Automatic updates may not be running yet."
                fi
                
                # Check service status
                if sudo systemctl is-active --quiet clamav-freshclam; then
                    echo "✓ ClamAV installed successfully"
                    echo "✓ Automatic virus definition updates enabled"
                    echo "✓ freshclam service is running"
                    echo ""
                    echo "ClamAV will automatically update virus definitions every hour."
                    echo "To scan a directory: clamscan -r /path/to/directory"
                    echo "To check update status: sudo systemctl status clamav-freshclam"
                else
                    echo "Warning: ClamAV installed but freshclam service is not running."
                    echo "You can start it manually: sudo systemctl start clamav-freshclam"
                fi
            else
                echo "Warning: systemd/systemctl not available. Skipping freshclam service enable/start."
                echo "You may need to configure ClamAV virus definition updates manually for your environment."
            fi
        else
            echo "Warning: ClamAV packages were installed but 'freshclam' was not found in PATH."
            echo "You may need to check your installation or PATH configuration."
        fi
    else
        echo "Warning: Failed to install ClamAV. Continuing without virus scanning."
        echo "Check your internet connection and package repository configuration."
        echo "You can install ClamAV manually later with:"
        echo "  sudo apt install clamav clamav-daemon clamav-freshclam -y"
        echo "Skipping ClamAV configuration because installation did not complete successfully."
    fi
else
    echo "Skipping ClamAV installation."
    echo "You can install it later with: sudo apt install clamav clamav-daemon clamav-freshclam"
fi

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Platform: $NAME ${VERSION_ID:-Unknown}"
echo ""
echo "Next steps:"
echo "1. Copy the environment template: cp .env.example .env"
echo "2. Edit .env with your API keys and credentials"
echo "3. Run the bot:"
echo "   - Web GUI (recommended): ./start_web_gui.sh"
echo "   - Desktop GUI: ./start_bot.sh"
echo "   - CLI mode: ./venv/bin/python3 main.py"
echo ""
echo "For Linux Mint users:"
echo "  See LINUX_MINT_GUIDE.md for desktop integration and optimization tips"
echo ""
echo "Note: The bot runs in a Python virtual environment (venv)."
echo "To activate it manually: source venv/bin/activate"
echo ""
