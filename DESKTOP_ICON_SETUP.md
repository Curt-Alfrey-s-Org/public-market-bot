# Desktop Icon Setup

## ✅ Desktop Launcher Created

A desktop launcher has been created for the Market Bot GUI application.

### Files Created:

1. **`market-bot-gui.desktop`** - Desktop launcher file
   - Location: `/home/operator/market-bot/market-pie5-bot/market-bot-gui.desktop`
   - Executable: Yes
   - Icon: `assets/icon.png`

2. **`start_gui.sh`** - Unified startup script
   - Starts both FastAPI backend and React frontend
   - Handles virtual environment setup
   - Manages process IDs for cleanup
   - Location: `/home/operator/market-bot/market-pie5-bot/start_gui.sh`
   - Executable: Yes

3. **`assets/icon.png`** - Application icon
   - Professional trading bot icon
   - Location: `/home/operator/market-bot/market-pie5-bot/assets/icon.png`

---

## 🚀 How to Install Desktop Icon

### Option 1: Copy to Desktop (Quick)

```bash
cp /home/operator/market-bot/market-pie5-bot/market-bot-gui.desktop ~/Desktop/
chmod +x ~/Desktop/market-bot-gui.desktop
```

### Option 2: Install System-Wide (Recommended)

```bash
# Copy to applications directory
sudo cp /home/operator/market-bot/market-pie5-bot/market-bot-gui.desktop /usr/share/applications/

# Or for user-specific installation:
cp /home/operator/market-bot/market-pie5-bot/market-bot-gui.desktop ~/.local/share/applications/
```

### Option 3: Make Executable and Trust

```bash
# Make executable
chmod +x /home/operator/market-bot/market-pie5-bot/market-bot-gui.desktop

# Trust the desktop file (if needed)
gio set /home/operator/market-bot/market-pie5-bot/market-bot-gui.desktop metadata::trusted true
```

---

## 📋 Desktop Entry Details

- **Name:** Market Bot GUI
- **Comment:** Modern React + FastAPI Trading Bot Dashboard
- **Exec:** `/home/operator/market-bot/market-pie5-bot/start_gui.sh`
- **Icon:** `/home/operator/market-bot/market-pie5-bot/assets/icon.png`
- **Terminal:** true (shows terminal for logs)
- **Categories:** Finance, Trading, Development

---

## 🎯 Usage

1. **Double-click the desktop icon** to launch the application
2. The script will:
   - Start FastAPI backend on `http://localhost:8000`
   - Start React frontend on `http://localhost:5173`
   - Open in your default browser automatically (if configured)

3. **To stop the application:**
   - Press `Ctrl+C` in the terminal
   - Or close the terminal window

---

## 🔧 Troubleshooting

### Icon Not Showing?

1. **Check icon path:**
   ```bash
   ls -la /home/operator/market-bot/market-pie5-bot/assets/icon.png
   ```

2. **Update icon path in desktop file:**
   ```bash
   nano /home/operator/market-bot/market-pie5-bot/market-bot-gui.desktop
   # Update the Icon= line with correct path
   ```

3. **Refresh desktop:**
   ```bash
   # KDE
   kbuildsycoca5
   
   # GNOME
   gtk-update-icon-cache
   ```

### Desktop File Not Executable?

```bash
chmod +x /home/operator/market-bot/market-pie5-bot/market-bot-gui.desktop
```

### Permission Denied?

Make sure the script is executable:
```bash
chmod +x /home/operator/market-bot/market-pie5-bot/start_gui.sh
```

---

## 📝 Notes

- The desktop launcher opens a terminal window to show server logs
- Both servers run in the background
- Process IDs are saved to `/tmp/` for cleanup
- Logs are written to `/tmp/market-bot-api.log` and `/tmp/market-bot-frontend.log`

---

**Status:** ✅ Desktop icon and launcher ready!
