# Market Pie5 Bot - Linux Mint Installation and Setup Guide

**Running Market Pie5 Bot on Linux Mint**

This guide provides complete instructions for installing and running the Market Pie5 Bot trading bot on Linux Mint (versions 20.x, 21.x, and newer). The bot is fully compatible with Linux Mint and all Debian-based distributions.

---

## 🖥️ System Requirements

### Minimum Requirements
- **OS:** Linux Mint 20.x or newer (also compatible with Ubuntu 20.04+, Debian 10+)
- **CPU:** Dual-core processor (Intel/AMD)
- **RAM:** 2 GB minimum, 4 GB recommended
- **Storage:** 500 MB for bot + dependencies
- **Python:** 3.8 or newer (3.10+ recommended)
- **Internet:** Required for market data and API access

### Recommended for Optimal Performance
- **CPU:** Quad-core processor or better
- **RAM:** 8 GB or more
- **Python:** 3.10 or newer
- **SSD:** For faster data access

---

## 📦 Installation

### Step 1: System Preparation

Update your system packages:

```bash
sudo apt update
sudo apt upgrade -y
```

Install required system packages:

```bash
# Essential packages
sudo apt install -y python3 python3-pip python3-venv git

# Optional but recommended for GUI
sudo apt install -y python3-tk

# Optional: For development and testing
sudo apt install -y curl wget build-essential
```

### Step 2: Clone the Repository

```bash
# Clone the repository
cd ~
git clone https://github.com/operator/market-pie5-bot.git
cd market-pie5-bot
```

### Step 3: Set Up Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip (recommended)
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Copy the environment template
cp .env.example .env

# Edit the .env file with your API keys
nano .env  # or use your preferred text editor (gedit, vim, etc.)
```

**Key configuration settings:**
- `SCHWAB_API_KEY` - Your Schwab API key (from developer.schwab.com)
- `SCHWAB_APP_SECRET` - Your Schwab app secret
- `SCHWAB_CALLBACK_URL` - OAuth callback URL (default: https://127.0.0.1:8182)
- `PAPER_TRADING_MODE=true` - Start with paper trading (recommended)
- `BOT_TOTAL_CAPITAL` - Starting capital for paper trading

See `.env.example` for complete configuration options.

---

## 🚀 Running the Bot

### Option 1: Web GUI (Recommended)

The web-based dashboard works on any device with a browser:

```bash
./start_web_gui.sh
```

Then open your browser to: **http://localhost:8050**

**Features:**
- 📊 Real-time charts and statistics
- 📱 Access from any device on your network
- 🎨 Modern, responsive interface
- 📈 Live trade monitoring

### Option 2: Desktop GUI (Tkinter)

Native desktop application using Tkinter:

```bash
./start_bot.sh
```

Select "GUI Mode" when prompted.

**Note:** Requires `python3-tk` package installed (see Step 1).

### Option 3: Command-Line Interface

For headless servers or terminal-only usage:

```bash
./start_bot.sh
```

Select "Command-line Mode" when prompted, or run directly:

```bash
source venv/bin/activate
python3 main.py
```

---

## 🖥️ Desktop Integration (Linux Mint)

### Creating Desktop Shortcuts

#### 1. Update Desktop Files

Edit the desktop files to match your installation path:

**For Desktop GUI:**
```bash
nano market-pie5-bot.desktop
```

Update the `Exec` line:
```
Exec=/home/YOUR_USERNAME/market-pie5-bot/start_bot.sh
```

**For Web GUI:**
```bash
nano market-pie5-web-gui.desktop
```

Update the `Exec` line:
```
Exec=/home/YOUR_USERNAME/market-pie5-bot/start_web_gui.sh
```

#### 2. Install Desktop Files

```bash
# Copy to applications directory
mkdir -p ~/.local/share/applications/
cp market-pie5-bot.desktop ~/.local/share/applications/
cp market-pie5-web-gui.desktop ~/.local/share/applications/

# Update desktop database
update-desktop-database ~/.local/share/applications/
```

#### 3. Add to Favorites (Optional)

After installation, the bot will appear in your application menu under "Office" or "Finance". You can:
- Right-click and add to favorites
- Drag to desktop for quick access
- Pin to panel

---

## 🔧 Linux Mint Specific Configuration

### Cinnamon Desktop Environment

If using Cinnamon (default for Linux Mint):

**1. System Tray Integration:**
```bash
# The web GUI will automatically open in your default browser
# The desktop icon will use the terminal for status updates
```

**2. Autostart (Optional):**
```bash
# Create autostart entry
mkdir -p ~/.config/autostart/
cp market-pie5-web-gui.desktop ~/.config/autostart/
```

### MATE Desktop Environment

If using MATE:

**1. Terminal Settings:**
```bash
# Ensure terminal stays open on error
# Edit start_bot.sh or start_web_gui.sh if needed
```

**2. Panel Integration:**
- Right-click panel → Add to Panel → Custom Application Launcher
- Browse to the desktop file location

### Xfce Desktop Environment

If using Xfce:

**1. Menu Editor:**
```bash
# Use menulibre or xfce4-appfinder to customize menu entries
sudo apt install menulibre
menulibre
```

---

## 🌐 Network Access (Optional)

To access the web GUI from other devices on your network:

### 1. Find Your IP Address
```bash
hostname -I | awk '{print $1}'
```

### 2. Access from Another Device
Open browser on another device and navigate to:
```
http://YOUR_IP_ADDRESS:8050
```

Example: `http://192.0.2.21:8050`

### 3. Firewall Configuration (If Needed)
```bash
# Allow port 8050 through firewall
sudo ufw allow 8050/tcp
```

---

## 🔒 Security Considerations

### Token Encryption

Enable token encryption for enhanced security:

```bash
# Generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env file
echo "SCHWAB_ENCRYPT_TOKEN=true" >> .env
echo "MP5_ENCRYPTION_KEY=YOUR_GENERATED_KEY" >> .env
```

### File Permissions

Ensure your .env file has proper permissions:

```bash
chmod 600 .env
chmod 600 token.json  # If it exists
```

---

## 🧪 Testing the Installation

### 1. Check Dependencies
```bash
source venv/bin/activate
python3 -c "import dash, plotly, pandas, numpy, yfinance; print('All dependencies OK')"
```

### 2. Run Test Suite
```bash
# Set test environment
export PAPER_TRADING_MODE='true'
export ENABLE_PDT_RULES='false'
export SCHWAB_SANDBOX_MODE='true'

# Run tests
python3 -m unittest test_trading_bot -v
```

### 3. Test Web GUI
```bash
# Start in test mode
./start_web_gui.sh
# Open browser to http://localhost:8050
# Verify all tabs load correctly
```

---

## 📊 Performance Optimization for Linux Mint

### CPU Throttling

For older or lower-end systems:

```bash
# Edit .env file
nano .env
```

Add/modify:
```
BOT_MAX_CPU_PERCENT=60
BOT_MAX_MEMORY_PERCENT=70
BOT_ENABLE_THROTTLING=true
TRADING_FREQUENCY=5
```

### Memory Management

Monitor resource usage:

```bash
# Install monitoring tools
sudo apt install htop
htop

# Check bot memory usage
ps aux | grep python3
```

---

## 🐛 Troubleshooting

### Issue: "No module named 'tkinter'"

**Solution:**
```bash
sudo apt install python3-tk
```

### Issue: "Port 8050 already in use"

**Solution:**
```bash
# Find and kill process using port 8050
sudo lsof -t -i:8050 | xargs kill -9

# Or change the port in web_gui.py
```

### Issue: "Permission denied" when running scripts

**Solution:**
```bash
chmod +x start_bot.sh start_web_gui.sh install.sh
```

### Issue: Virtual environment activation fails

**Solution:**
```bash
# Ensure python3-venv is installed
sudo apt install python3-venv

# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Display/GUI doesn't open

**Solution:**
```bash
# Check DISPLAY variable
echo $DISPLAY

# If empty, set it
export DISPLAY=:0

# Verify X server is running
ps aux | grep X
```

---

## 🔄 Updating the Bot

### Pull Latest Changes

```bash
cd ~/market-pie5-bot
git pull origin main

# Reactivate virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt --upgrade
```

---

## 📚 Additional Resources

- **Main Documentation:** [README.md](README.md)
- **User Guide:** [USER_GUIDE.md](USER_GUIDE.md)
- **Web GUI Guide:** [WEB_GUI_GUIDE.md](WEB_GUI_GUIDE.md)
- **Trading Modes:** [SANDBOX_LIVE_DISTINCTION.md](SANDBOX_LIVE_DISTINCTION.md)
- **Security:** [TOKEN_ENCRYPTION_GUIDE.md](TOKEN_ENCRYPTION_GUIDE.md)

---

## 💡 Tips for Linux Mint Users

### 1. Use Update Manager
Keep your system updated using Linux Mint's Update Manager for best compatibility.

### 2. Software Manager
You can install Python and dependencies using the Software Manager GUI if you prefer.

### 3. System Monitor
Use Linux Mint's System Monitor (Ctrl+Esc) to watch bot resource usage.

### 4. Multiple Desktops
Use virtual desktops to keep the bot GUI separate from other work.

### 5. Backup Configuration
```bash
# Backup your configuration
cp .env .env.backup
cp token.json token.json.backup  # If exists
```

---

## 🤝 Getting Help

If you encounter issues:

1. Check [KNOWN_ISSUES.md](KNOWN_ISSUES.md)
2. Review [Troubleshooting](#-troubleshooting) section above
3. Search existing [GitHub Issues](https://github.com/operator/market-pie5-bot/issues)
4. Open a new issue with:
   - Linux Mint version (`cat /etc/lsb-release`)
   - Python version (`python3 --version`)
   - Error messages (sanitize any credentials!)
   - Steps to reproduce

---

## ✅ Compatibility Verified

This bot has been tested and verified to work on:
- ✅ Linux Mint 21.x (Cinnamon, MATE, Xfce)
- ✅ Linux Mint 20.x (Cinnamon, MATE, Xfce)
- ✅ Ubuntu 22.04 LTS and 20.04 LTS
- ✅ Debian 11 and 12
- ✅ Other Debian-based distributions

**Note:** While originally optimized for Raspberry Pi 5, the bot is fully compatible with any Linux distribution and standard x86_64/AMD64 hardware.

---

## 📝 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

**Happy Trading on Linux Mint! 🚀📈**
