# Desktop Icons Installation Guide

This guide explains how to install desktop application icons for the Market Pie5 Bot on Raspberry Pi 5 (or any Linux desktop environment).

> **🔧 Recent Fix (Jan 2026):** Desktop icons now work correctly when clicked! The launch scripts have been updated to:
> - Auto-detect desktop icon launches (non-interactive mode)
> - Start the GUI directly without prompting for input
> - Keep terminal open on errors with helpful diagnostics
> - Show clear error messages for troubleshooting
> - **Auto-launch default web browser** when web GUI starts
> - **Display splash screen** on first load

## Overview

The bot comes with two desktop entry files:

1. **market-pie5-web-gui.desktop** - Web Dashboard (Recommended)
   - Launches the browser-based trading dashboard
   - **Automatically opens your default web browser** to `http://localhost:8050`
   - **Shows splash screen** with "Enter Dashboard" button
   - Modern, feature-rich interface
   - Works with any browser (Chrome, Firefox, Safari, Edge, etc.)

2. **market-pie5-bot.desktop** - Desktop GUI (Alternative)
   - Launches the Tkinter desktop GUI
   - Native desktop application
   - Lower resource usage

## Quick Installation (Recommended)

Use the automated installation script:

```bash
cd market-pie5-bot
./install_desktop_icons.sh
```

This script will:
- ✅ Automatically detect your installation path
- ✅ Update desktop files with correct paths
- ✅ Install icons to your application menu
- ✅ Update the desktop database
- ✅ Make icons appear in Finance/Office categories

After installation, find the icons in your application launcher:
- Search for "Market Pie5" or "trading"
- Look in Finance or Office categories
- Both icons will be available

## Manual Installation

If you prefer to install manually:

### Step 1: Update Paths

Edit each desktop file and update the `Exec` path to match your installation:

```bash
# Edit Web GUI desktop file
nano market-pie5-web-gui.desktop
# Change: Exec=/home/pi/market-pie5-bot/start_web_gui.sh
# To:     Exec=/your/actual/path/market-pie5-bot/start_web_gui.sh

# Edit Desktop GUI file
nano market-pie5-bot.desktop
# Change: Exec=/home/pi/market-pie5-bot/start_bot.sh
# To:     Exec=/your/actual/path/market-pie5-bot/start_bot.sh
```

### Step 2: Copy to Applications Directory

```bash
# Create directory if it doesn't exist
mkdir -p ~/.local/share/applications

# Copy both desktop files
cp market-pie5-web-gui.desktop ~/.local/share/applications/
cp market-pie5-bot.desktop ~/.local/share/applications/

# Make them executable
chmod +x ~/.local/share/applications/market-pie5-web-gui.desktop
chmod +x ~/.local/share/applications/market-pie5-bot.desktop
```

### Step 3: Update Desktop Database

```bash
update-desktop-database ~/.local/share/applications/
```

## Desktop File Details

### Web GUI Desktop File (`market-pie5-web-gui.desktop`)

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Market Pie5 Web Dashboard
Comment=Browser-based trading dashboard for Raspberry Pi 5
Exec=/home/pi/market-pie5-bot/start_web_gui.sh
Icon=/home/pi/market-pie5-bot/market-pie5-icon.svg
Terminal=true
Categories=Finance;Office;Network;
Keywords=trading;stock;bot;finance;web;dashboard;
StartupNotify=true
```

**Note:** The `Icon` path uses the custom Market Pie5 Bot icon (SVG format). The installation scripts automatically update this path to match your installation directory.

### Desktop GUI File (`market-pie5-bot.desktop`)

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Market Pie5 Bot (Desktop GUI)
Comment=Trading bot with desktop GUI for Raspberry Pi 5
Exec=/home/pi/market-pie5-bot/start_bot.sh
Icon=/home/pi/market-pie5-bot/market-pie5-icon.svg
Terminal=true
Categories=Finance;Office;
Keywords=trading;stock;bot;finance;desktop;gui;
StartupNotify=true
```

**Note:** Both desktop files use the same custom icon (`market-pie5-icon.svg`) for a consistent visual identity. See [ICON_README.md](ICON_README.md) for icon details and customization options.

## Customization

### Custom Icon Included

The bot now includes a custom icon (`market-pie5-icon.svg`) that features:
- Colorful pie chart representing portfolio diversification
- Pi symbol (π) in the center
- Gear icon indicating automation
- Upward arrow for financial growth
- Number "5" referencing Raspberry Pi 5

See [ICON_README.md](ICON_README.md) for details on the icon design and how to customize it.

### Change Icon

The default installation uses the custom Market Pie5 Bot icon. If you want to use a different icon:

1. Place your icon file (PNG, SVG, or ICO) in a standard location:
   ```bash
   mkdir -p ~/.local/share/icons
   cp your-icon.png ~/.local/share/icons/market-pie5.png
   ```

2. Edit the desktop file:
   ```bash
   nano ~/.local/share/applications/market-pie5-web-gui.desktop
   ```

3. Update the `Icon` line:
   ```ini
   Icon=/home/YOUR_USERNAME/.local/share/icons/market-pie5.png
   ```
   Or use a system icon name:
   ```ini
   Icon=stock
   ```

4. Update desktop database:
   ```bash
   update-desktop-database ~/.local/share/applications/
   ```

### Add to Desktop (Shortcut)

To add an icon directly to your desktop:

```bash
# Copy desktop file to Desktop folder
cp market-pie5-web-gui.desktop ~/Desktop/
chmod +x ~/Desktop/market-pie5-web-gui.desktop

# Or for Desktop GUI
cp market-pie5-bot.desktop ~/Desktop/
chmod +x ~/Desktop/market-pie5-bot.desktop
```

**Note:** Some desktop environments (like GNOME) may require you to right-click the icon and select "Allow Launching" or "Trust" before it becomes clickable.

## Troubleshooting

### Icons Don't Appear

**Problem:** Desktop icons don't show up in the application menu

**Solutions:**
1. **Refresh the desktop database:**
   ```bash
   update-desktop-database ~/.local/share/applications/
   ```

2. **Log out and log back in** - This forces the desktop environment to reload

3. **Restart your desktop environment:**
   - LXDE/Openbox (Raspberry Pi OS): `sudo systemctl restart lightdm`
   - GNOME: Press `Alt+F2`, type `r`, press Enter
   - KDE: `killall plasmashell && plasmashell &`

4. **Check file permissions:**
   ```bash
   ls -la ~/.local/share/applications/market-pie5*.desktop
   ```
   Files should be executable (`-rwxr-xr-x`)

### Icons Launch But Nothing Happens

**Problem:** Clicking icon briefly opens a terminal that closes immediately, or nothing happens

**This issue has been fixed!** The launch scripts now:
- Auto-detect when launched from desktop icons (non-interactive mode)
- Launch the GUI directly without prompting for input
- Keep the terminal open on errors with helpful diagnostic messages
- Show clear error messages if dependencies or configuration issues exist

**If you still experience issues:**

1. **Re-run the installer to update desktop files:**
   ```bash
   cd /your/path/market-pie5-bot
   ./install_desktop_icons.sh
   ```

2. **Check the Exec path is correct:**
   ```bash
   cat ~/.local/share/applications/market-pie5-web-gui.desktop | grep Exec
   ```
   Verify the path matches your actual installation

3. **Test the launch script directly:**
   ```bash
   # For Web GUI
   /your/path/market-pie5-bot/start_web_gui.sh
   
   # For Desktop GUI
   /your/path/market-pie5-bot/start_bot.sh
   ```

4. **Check if dependencies are installed:**
   ```bash
   cd /your/path/market-pie5-bot
   ./venv/bin/pip list | grep -E "(dash|plotly|tkinter)"
   ```

5. **Check for error messages:**
   - Both desktop icons now show a terminal window (Terminal=true)
   - If the application fails to start, the terminal stays open showing the error
   - Read the error message for diagnostic information

### Wrong Icon Appears

**Problem:** Generic icon shows instead of intended icon

**Solutions:**
1. **Use absolute path for icon:**
   ```ini
   Icon=/usr/share/icons/hicolor/48x48/apps/stock.png
   ```

2. **Install icon theme that has the `stock` icon:**
   ```bash
   sudo apt install gnome-icon-theme
   ```

3. **Use a standard icon name** that exists on your system:
   ```bash
   # See available icons
   ls /usr/share/icons/hicolor/48x48/apps/
   ```

## Raspberry Pi 5 Specific Notes

### Performance Considerations

- **Web GUI**: Recommended for most users
  - Runs efficiently on Pi 5's quad-core CPU
  - Uses hardware-accelerated browser rendering
  - Can be accessed from other devices

- **Desktop GUI**: Alternative option
  - Lower memory footprint
  - Direct display output (no browser overhead)
  - Better for minimal setups

### Autostart on Boot

To launch the bot automatically on Pi 5 startup:

1. **For Web GUI:**
   ```bash
   mkdir -p ~/.config/autostart
   cp market-pie5-web-gui.desktop ~/.config/autostart/
   ```

2. **For Desktop GUI:**
   ```bash
   mkdir -p ~/.config/autostart
   cp market-pie5-bot.desktop ~/.config/autostart/
   ```

**Note:** Only autostart one interface at a time to avoid conflicts.

### Display Considerations

On Raspberry Pi 5:
- Web GUI works on any screen resolution (responsive)
- Desktop GUI optimized for 1920x1080 but adapts to smaller screens
- Both support multiple monitor setups

## Uninstalling Desktop Icons

To remove the desktop icons:

```bash
# Remove from application menu
rm ~/.local/share/applications/market-pie5-web-gui.desktop
rm ~/.local/share/applications/market-pie5-bot.desktop

# Remove from desktop (if added)
rm ~/Desktop/market-pie5-web-gui.desktop
rm ~/Desktop/market-pie5-bot.desktop

# Remove from autostart (if configured)
rm ~/.config/autostart/market-pie5-web-gui.desktop
rm ~/.config/autostart/market-pie5-bot.desktop

# Update desktop database
update-desktop-database ~/.local/share/applications/
```

## Additional Resources

- **Web GUI Guide**: [WEB_GUI_GUIDE.md](WEB_GUI_GUIDE.md)
- **Web GUI Quick Start**: [WEB_GUI_QUICKSTART.md](WEB_GUI_QUICKSTART.md)
- **Main README**: [README.md](README.md)
- **Installation Guide**: [README.md#installation](README.md#installation)

## Support

If you encounter issues not covered here:
1. Check the main README troubleshooting section
2. Verify all dependencies are installed: `pip list`
3. Test launching manually first: `./start_web_gui.sh`
4. Check system logs: `journalctl --user -xe`
5. Open an issue on GitHub with error details

---

**Enjoy easy access to your trading bot from the application menu!** 🚀📈
