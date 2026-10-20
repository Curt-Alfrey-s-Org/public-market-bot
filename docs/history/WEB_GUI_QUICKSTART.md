# Web GUI Quick Start Guide

## 🚀 Quick Start (3 Steps)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Web Dashboard
```bash
# Option A: Use the launcher script
./start_web_gui.sh

# Option B: Start directly
python3 web_gui.py
```

### 3. Open in Browser
```
http://localhost:8050
```

That's it! You're ready to trade! 🎉

---

## 📱 Access from Mobile/Tablet

1. Find your Pi's IP address:
   ```bash
   hostname -I
   ```

2. Open browser on mobile device to:
   ```
   http://<pi-ip-address>:8050
   ```
   Example: `http://192.0.2.21:8050`

3. Add to home screen for quick access!

---

## 🎯 Main Features at a Glance

### Trading Dashboard Tab
- **Start/Stop Bot**: One-click control
- **Live Stats**: Trades, win rate, P&L, capital
- **Symbol Selector**: Dropdown + manual input
- **Price Chart**: Real-time interactive chart
- **Terminal**: Live log output (green on black)
- **Trade Log**: Recent trades with win/loss

### Settings Tab
- Capital amount
- Min/Max allocation
- Trailing stop %
- Risk threshold %
- Apply button

### Statistics Tab
- Detailed trading summary
- Capital management metrics
- Open positions list
- Performance analytics

---

## 💡 Tips & Tricks

### Tip 1: Multiple Monitors
Open multiple browser tabs/windows to monitor different aspects simultaneously:
- Tab 1: Trading Dashboard
- Tab 2: Statistics
- Tab 3: Settings (for quick adjustments)

### Tip 2: Mobile Dashboard
Set up a dedicated tablet as a trading dashboard:
1. Open web GUI in browser
2. Add to home screen
3. Keep tablet always-on with dashboard displayed

### Tip 3: Fullscreen Mode
Press `F11` in your browser for distraction-free fullscreen trading view

### Tip 4: Quick Symbol Entry
Use the ticker input field to quickly add symbols without scrolling through dropdowns

### Tip 5: Keep Terminal Visible
The terminal output shows real-time status and errors - keep it visible while trading

---

## 🔧 Troubleshooting

### "Can't connect to dashboard"
- Check if web_gui.py is running
- Verify you're using the correct IP/port
- Check firewall: `sudo ufw allow 8050`

### "Charts not updating"
- Ensure bot is running (green status)
- Select a symbol from dropdown
- Check terminal for errors

### "Slow performance"
- Close unnecessary browser tabs
- Reduce update interval in code (change from 1s to 2s)
- Limit number of trading symbols

### "Settings won't apply"
- Click "Apply Settings" button
- Stop and restart bot for changes to take effect

---

## 📊 Understanding the Interface

### Status Indicator
- 🟢 **Running** = Bot is actively trading
- 🔴 **Stopped** = Bot is idle

### Trade Log Colors
- 🟢 **WIN** = Profitable trade
- 🔴 **LOSS** = Losing trade

### Chart Features
- **Hover**: See exact price and time
- **Zoom**: Click and drag on chart
- **Pan**: Click and drag on axes
- **Reset**: Double-click chart

### Terminal Colors
- Green text = Normal operations
- Would show red/yellow for errors/warnings (future enhancement)

---

## 🎨 Customization

### Change Port
Edit `web_gui.py`, line near bottom:
```python
app.run(debug=True, host='0.0.0.0', port=8050)
```
Change `port=8050` to your preferred port.

### Adjust Update Frequency
Edit `web_gui.py`, find:
```python
dcc.Interval(id='interval-component', interval=1000, n_intervals=0)
```
Change `interval=1000` (1 second) to `interval=2000` (2 seconds) or higher.

### Add More Symbols to Trade
Edit your symbol list file or use the ticker input to add symbols dynamically.

---

## 🔐 Security Notes

⚠️ **Important Security Reminders:**

1. **Local Network Only**: Dashboard is accessible on your local network by default
2. **Don't Expose to Internet**: Port 8050 should NOT be exposed to public internet without authentication
3. **Use VPN**: For remote access, use VPN instead of port forwarding
4. **Keep Software Updated**: Regularly update dependencies for security patches

---

## 🆚 Web GUI vs Desktop GUI

| Feature | Web GUI | Desktop GUI |
|---------|---------|-------------|
| **Access** | Any browser | Local display only |
| **Mobile** | ✅ Yes | ❌ No |
| **Charts** | Interactive Plotly | Basic |
| **Terminal** | Integrated | Separate log viewer |
| **Setup** | Just open browser | Requires X server |
| **Performance** | Good | Excellent |
| **Multi-device** | ✅ Yes | ❌ No |

**Recommendation**: Use Web GUI for better features and remote access!

---

## 📚 Additional Resources

- **Full Documentation**: See [WEB_GUI_GUIDE.md](WEB_GUI_GUIDE.md)
- **Main README**: See [README.md](README.md)
- **Trading Guide**: See [LIVE_MODE_GUIDE.md](LIVE_MODE_GUIDE.md)
- **Issue Tracker**: Report bugs on GitHub Issues

---

## 🎁 Bonus: Desktop Shortcut

Create a desktop shortcut to launch web GUI with one click:

**On Raspberry Pi (Linux):**

Create file `~/Desktop/web-dashboard.desktop`:
```ini
[Desktop Entry]
Type=Application
Name=Trading Web Dashboard
Exec=/home/pi/market-pie5-bot/start_web_gui.sh
Icon=stock
Terminal=true
Categories=Office;Finance;
```

Make executable:
```bash
chmod +x ~/Desktop/web-dashboard.desktop
```

Now double-click to launch!

---

**Happy Trading! 📈💰**
