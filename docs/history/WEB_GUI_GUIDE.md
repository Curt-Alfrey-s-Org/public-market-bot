# Web-Based Trading Dashboard Guide

## Overview

The Market Pie5 Bot now includes a modern, browser-based trading dashboard built with Plotly Dash. This provides a ThinkorSwim-like experience with real-time charts, terminal output, and point-and-click controls.

### ✨ NEW: Draggable & Customizable Dashboard (v2.0)

The dashboard now features a **fully customizable layout** with drag-and-drop widgets! Personalize your trading workspace by:
- 🖱️ **Drag widgets** to rearrange your dashboard layout
- 📏 **Collapse/expand widgets** to focus on what matters
- 💾 **Save your layout** - positions persist across sessions
- 🔄 **Reset to default** anytime with one click
- 🎨 **Modern glassmorphism design** with smooth animations

![Dashboard Screenshot](https://github.com/

## Features

### 🎯 **Customizable Dashboard Layout (NEW)**
- **Drag-and-drop widgets** - Click and drag any widget to reposition it
- **Collapse widgets** - Click the chevron button to minimize/expand widgets
- **Persistent layouts** - Your custom layout is automatically saved to browser storage
- **Layout controls** - Save current layout or reset to default with dedicated buttons
- **Responsive grid** - Widgets automatically adjust to screen size

### 🎨 **Modern Visual Design (NEW)**
- **Glassmorphism effects** - Translucent cards with backdrop blur
- **Smooth animations** - Fade-in, slide, and scale transitions
- **Enhanced color palette** - Improved contrast and accessibility (WCAG AA compliant)
- **Professional shadows** - Multi-layer depth effects
- **Hover states** - Interactive feedback on all clickable elements

### 🎯 **Point-and-Click Interface**
- Start/Stop bot with single button clicks
- No command-line knowledge required
- Intuitive tabbed interface

### 📊 **Real-Time Stock Charts**
- Live price visualization for selected tickers
- Interactive Plotly charts with zoom, pan, and hover
- Automatic updates every second
- Historical price tracking

### 🎚️ **Dropdown Menus & Ticker Input**
- Select from predefined tickers via dropdown
- Add custom symbols on the fly
- Symbol search and filtering

### 💻 **Interactive Terminal**
- Real-time log output in terminal-style display
- **NEW**: Interactive command input with cursor
- Command support: help, status, clear, positions, stats
- Color-coded messages (green for success, red for errors)
- Scrollable history with timestamps
- Courier New monospace font for readability

### 📈 **Statistics Dashboard**
- Total trades, win rate, P&L tracking
- Capital management metrics
- Open positions monitoring
- Detailed performance analytics

### ⚙️ **Comprehensive Settings Management**
- **All .env parameters accessible in UI** (~35+ settings)
- Organized into logical sections:
  - **Profile & Appearance** - Customize your display name, avatar, and background
  - **Trading Mode** - Paper/Live, Sandbox, Non-Interactive
  - **Schwab API Configuration** - API keys, callback URL, token path
  - **Capital & Risk Management** - Total capital, allocation limits, risk thresholds
  - **Stop Loss & Take Profit** - Trailing stops, profit targets, risk/reward ratios
  - **Stock Filtering** - Price ranges, volume filters, sector preferences
  - **Position Management** - Max positions, holding periods
  - **Trading Frequency & Simulation** - Cycle delays, continuous trading
  - **Advanced Features** - Sentiment analysis, portfolio optimization, ML signals
  - **Resource Throttling** - CPU/memory limits for Raspberry Pi 5
  - **Beta Features** - AI auto-tweak and experimental options
- Save settings directly to .env file
- Validation, tooltips, and error checking
- Secure handling of sensitive API keys (automatic encryption)

### 📋 **Trade Log**
- Recent trade history display
- Win/loss indicators with color coding
- Timestamp, symbol, action, and price details

### 📄 **NEW: Logs Tab**
- View live session logs in real-time
- Access historical log files (trading_bot.log, alerts.log)
- Search and filter logs
- Color-coded log levels (ERROR, WARNING, INFO)
- Refresh and clear functionality
- 500-line history buffer for performance

## Installation

### Prerequisites

Make sure you have Python 3.8+ installed.

### Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

The web GUI requires:
- `dash>=2.14.0` - Web framework
- `plotly>=5.18.0` - Interactive charting

These are automatically included in `requirements.txt`.

## Usage

### Starting the Web Dashboard

```bash
# From the project directory
python3 web_gui.py
```

Or if using virtual environment:

```bash
./venv/bin/python3 web_gui.py
```

### Accessing the Dashboard

Once started, open your browser to:

```
http://localhost:8050
```

Or from another device on your network (e.g., from your phone/tablet):

```
http://<raspberry-pi-ip>:8050
```

To find your Raspberry Pi's IP address:
```bash
hostname -I
```

### Dashboard Tabs

#### 1. **Trading Dashboard (Main Tab)**

**NEW: Customizable Layout Controls:**
- **Drag Widgets**: Click and hold any widget's header to drag it to a new position
- **Collapse Widgets**: Click the chevron (▲/▼) button in the widget header to minimize/expand
- **Save Layout**: Click "Save Layout" button to persist your custom arrangement
- **Reset Layout**: Click "Reset Layout" to restore the default widget positions
- **Auto-Save**: Widget positions are automatically saved to browser's localStorage

**Dashboard Widgets:**
1. **Stats Overview Widget** - Displays Total Capital, Allocation per Trade, and Win Rate
2. **Price Chart Widget** - Real-time stock price visualization with ticker selection
3. **Top Performers Watchlist Widget** - Shows high-probability trading candidates
4. **Recent Activity Widget** - Displays recent trades and bot actions

**Controls Section:**
- **Start Bot**: Begins automated trading with current settings
- **Stop Bot**: Safely stops the trading bot

**Statistics Panel:**
- Total Trades: Number of trades executed
- Win Rate: Percentage of profitable trades
- Current Allocation: Amount allocated per trade
- Total Capital: Current account balance
- P&L: Profit/Loss with percentage

**Symbol Selection:**
- Choose ticker from dropdown or enter manually
- Click "Add" to include new symbols in the dropdown
- Select symbol to view its price chart

**Price Chart:**
- Real-time price visualization
- Interactive zoom and pan
- Hover for exact values

**Terminal Output:**
- Live log stream in terminal style
- **NEW**: Interactive command input with cursor (">")
- Type commands: help, status, clear, positions, stats
- Green text on black background
- Timestamps for all events
- Auto-scroll to latest messages

**Trade Log:**
- Recent 20 trades displayed
- Color-coded WIN (green) / LOSS (red)
- Timestamp, symbol, action, and price

#### 2. **Settings Tab**

**NEW: Comprehensive Configuration**

All environment variables are now accessible through organized sections:

**Trading Mode:**
- Paper Trading Mode (Simulation vs Live)
- Schwab Sandbox Mode (Sandbox (On) / Live / Off (Training Mode))
  - **Sandbox (On)**: Uses Schwab sandbox API for testing
  - **Live**: Uses Schwab production API
  - **Off (Training Mode)**: Disables Schwab API entirely, uses yfinance for training mode

**Capital & Risk Management:**
- Total Capital ($)
- Min Allocation ($)
- Max Allocation ($)
- Risk Threshold (%)
- Position Size (%)
- Capital Floor (%)
- Max Open Positions
- Max Consecutive Losses

**Stop Loss & Take Profit:**
- Trailing Stop (%)
- Stop Loss (%)
- Take Profit (%)
- Dynamic Stop Enabled
- Min Trailing Stop (%)
- Max Trailing Stop (%)

**Stock Filtering:**
- Min Stock Price ($)
- Min Daily Volume
- Max Stock Volatility
- Volatility Window (days)

**Position Management:**
- Partial Exit Enabled
- Partial Exit Percentage (%)

**Trading Frequency:**
- Trading Frequency (seconds between trades)

**Simulation Settings:**
- Simulated Win Rate

**Web GUI Settings:**
- Max Symbols to Trade
- Continuous Trading (vs Single Cycle)

Click **Save Settings to .env** to persist changes to the .env file. Bot must be restarted for changes to take effect.

#### 3. **Statistics Tab**

Detailed performance metrics:

**Trading Summary:**
- Mode (Paper/Live)
- Total, winning, and losing trades
- Win rate percentage
- Consecutive losses count

**Capital Management:**
- Starting and current capital
- Total P&L with percentage
- Current allocation amount
- Capital floor (auto-pause threshold)

**Open Positions:**
- List of currently open positions
- Entry price, quantity, and high water mark for each

#### 4. **NEW: Logs Tab**

**Log Viewer for Troubleshooting:**

The Logs tab provides comprehensive access to bot logs for troubleshooting and monitoring.

**Features:**
- **Live Session Logs**: Real-time view of current session logs
- **Historical Log Files**: Access to trading_bot.log and alerts.log
- **Search/Filter**: Find specific log entries by keyword
- **Color-Coded Levels**:
  - ERROR/ALERT: Red
  - WARNING: Orange
  - INFO: Blue
  - Default: Green
- **Log Controls**:
  - Refresh: Manually reload logs
  - Clear Live Logs: Clear current session logs
- **Performance**: 500-line buffer for smooth scrolling

**How to Use:**
1. Select log source from dropdown (Live, trading_bot.log, or alerts.log)
2. Use search box to filter logs by keyword
3. Click Refresh to update log display
4. Click Clear Live Logs to reset the current session view

**Use Cases:**
- Monitor bot activity in real-time
- Troubleshoot errors and warnings
- Review historical trading decisions
- Track API responses and rate limits
- Debug configuration issues

## Features Comparison with ThinkorSwim

| Feature | ThinkorSwim | Market Pie5 Web Dashboard |
|---------|-------------|---------------------------|
| Stock Charts | ✅ Advanced | ✅ Real-time interactive |
| Ticker Input | ✅ Symbol search | ✅ Dropdown + manual entry |
| Terminal | ❌ No | ✅ Integrated terminal |
| Drop-down Menus | ✅ Extensive | ✅ Symbol selection |
| Point-and-Click | ✅ Full GUI | ✅ Web-based interface |
| Real-time Updates | ✅ Live data | ✅ 1-second refresh |
| Settings Panel | ✅ Preferences | ✅ Dynamic configuration |
| Trade Log | ✅ Activity log | ✅ Recent trades view |
| Statistics | ✅ Performance | ✅ Detailed metrics |
| Browser-based | ❌ Desktop app | ✅ Any device with browser |
| Mobile Access | ❌ No | ✅ Responsive design |

## Advantages of Web-Based GUI

### 1. **Cross-Platform Access**
- Access from any device (PC, Mac, Linux, phone, tablet)
- No installation required on client devices
- Works on Raspberry Pi 5 and remotely

### 2. **Real-Time Updates**
- Live data refresh every second
- No manual refresh needed
- Automatic chart updates

### 3. **Lightweight & Responsive**
- Runs efficiently on Raspberry Pi 5
- Low resource usage compared to desktop apps
- Fast loading and interaction

### 4. **Remote Monitoring**
- Monitor trading from anywhere on local network
- Check bot status from phone/tablet
- No VNC or remote desktop needed

### 5. **Modern UI/UX**
- Clean, dark theme design
- Intuitive tab-based navigation
- Professional trading dashboard aesthetic

## Keyboard Shortcuts

While the web GUI is primarily point-and-click, your browser's standard shortcuts work:

- `Ctrl + R` / `Cmd + R`: Refresh page
- `Ctrl + T` / `Cmd + T`: New tab (open multiple dashboards)
- `Ctrl + W` / `Cmd + W`: Close tab
- `F11`: Toggle fullscreen (great for monitoring)

## Troubleshooting

### Dashboard Won't Load

**Issue**: Browser shows "Can't reach this page"

**Solution**:
1. Check if web_gui.py is running: `ps aux | grep web_gui`
2. Verify port 8050 is not in use: `netstat -tuln | grep 8050`
3. Check firewall settings: `sudo ufw status`
4. Try accessing via IP instead of localhost

### Port Already in Use

**Issue**: "Address already in use" error

**Solution**:
```bash
# Find process using port 8050
sudo lsof -i :8050

# Kill the process (replace PID with actual process ID)
kill -9 <PID>

# Or use a different port by editing web_gui.py:
# Change: app.run(debug=True, host='0.0.0.0', port=8050)
# To:     app.run(debug=True, host='0.0.0.0', port=8051)
```

### Charts Not Updating

**Issue**: Price charts remain static

**Solution**:
1. Check if bot is running (status indicator should show "Running")
2. Verify symbols are added to the dropdown
3. Select a symbol from the dropdown
4. Check terminal output for errors
5. Ensure `get_stock_price()` is working (check for API errors)

### Settings Won't Apply

**Issue**: Changed settings don't take effect

**Solution**:
1. Click "Apply Settings" button after making changes
2. Stop and restart the bot for changes to take effect
3. Check "Settings" feedback message for validation errors

### Slow Performance

**Issue**: Dashboard is laggy or slow

**Solution**:
1. Reduce update frequency by editing interval in web_gui.py:
   ```python
   # Change: dcc.Interval(id='interval-component', interval=1000, n_intervals=0)
   # To:     dcc.Interval(id='interval-component', interval=2000, n_intervals=0)
   ```
2. Limit number of symbols being traded (default is 5)
3. Close other browser tabs
4. Check system resources with `htop`

### Can't Access from Other Devices

**Issue**: Dashboard works on Pi but not from phone/tablet

**Solution**:
1. Ensure device is on same network as Raspberry Pi
2. Use Pi's IP address, not "localhost"
3. Check firewall: `sudo ufw allow 8050`
4. Verify web_gui.py is using `host='0.0.0.0'` (not `host='127.0.0.1'`)

## Advanced Configuration

### Custom Port

Edit `web_gui.py` and change:

```python
app.run(debug=DEBUG_MODE, host='0.0.0.0', port=8050)
```

To your preferred port, e.g., `port=9000`

### Environment Variables

The web GUI supports several environment variables for configuration:

```bash
# Set in .env file or export before running

# Maximum number of symbols to trade (default: 5)
export WEB_GUI_MAX_SYMBOLS=10

# Enable continuous trading instead of single cycle (default: false)
export WEB_GUI_CONTINUOUS_TRADING=true

# Enable debug mode for development (default: false, DISABLE IN PRODUCTION)
export WEB_GUI_DEBUG=false
```

**Production Configuration Example (.env file):**
```bash
# Web GUI Settings
WEB_GUI_MAX_SYMBOLS=3
WEB_GUI_CONTINUOUS_TRADING=true
WEB_GUI_DEBUG=false  # IMPORTANT: Keep false in production
```

**Development Configuration Example:**
```bash
# Web GUI Settings
WEB_GUI_MAX_SYMBOLS=5
WEB_GUI_CONTINUOUS_TRADING=false  # Single cycle for testing
WEB_GUI_DEBUG=true  # Enable for debugging
```

### HTTPS/SSL (for secure remote access)

For production deployments with HTTPS:

1. Install Nginx as reverse proxy:
   ```bash
   sudo apt install nginx
   ```

2. Configure Nginx with SSL certificate

3. Proxy requests to port 8050

(Detailed HTTPS setup guide available separately)

### Run as Background Service

Create a systemd service file `/etc/systemd/system/market-pie5-web.service`:

```ini
[Unit]
Description=Market Pie5 Web Dashboard
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/market-pie5-bot
ExecStart=/home/pi/market-pie5-bot/venv/bin/python3 /home/pi/market-pie5-bot/web_gui.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable market-pie5-web
sudo systemctl start market-pie5-web
```

Check status:
```bash
sudo systemctl status market-pie5-web
```

## Security Considerations

### Local Network Only

By default, the dashboard is accessible on your local network. For security:

1. **Do not** expose port 8050 to the internet without authentication
2. Keep dashboard on private network only
3. Use VPN if accessing remotely

### Adding Authentication (Future Enhancement)

To add password protection, consider:
- Flask-Login integration
- Dash-Auth middleware
- OAuth2 providers

## Comparison: Desktop GUI vs Web GUI

| Aspect | Desktop GUI (gui.py) | Web GUI (web_gui.py) |
|--------|---------------------|----------------------|
| Framework | Tkinter | Plotly Dash |
| Access | Local only | Network-wide |
| Charts | Basic | Interactive Plotly |
| Performance | Native | Browser-based |
| Mobile Support | ❌ No | ✅ Yes |
| Installation | Python + Tkinter | Python + Dash |
| Resources | Lower | Moderate |
| Customization | Limited | Extensive |
| Real-time Updates | Poll-based | WebSocket-based |

**Recommendation**: Use **Web GUI** for:
- Remote monitoring
- Mobile access
- Multiple users
- Better visualizations
- Modern UI

Use **Desktop GUI** for:
- Minimal resource usage
- Offline operation
- Direct Pi display

## Future Enhancements

Planned features for future releases:

- [ ] Advanced charting (candlesticks, volume bars, technical indicators)
- [ ] Multi-symbol chart comparison
- [ ] Trade execution buttons (manual buy/sell)
- [ ] Alert configuration UI
- [ ] Export trade history to CSV
- [ ] Dark/Light theme toggle
- [ ] Custom watchlists
- [ ] Strategy backtesting UI
- [ ] User authentication
- [ ] WebSocket for real-time updates (instead of polling)

## Contributing

Found a bug or have a feature request for the web GUI? Please open an issue on GitHub.

## License

Same as main project (MIT License).

---

**Enjoy your new browser-based trading dashboard! 🚀📈**
