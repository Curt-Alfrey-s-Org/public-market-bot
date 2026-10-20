# Desktop Icon Installation Guide

This guide explains how to install the Market Pie5 Web Dashboard desktop icon for all users and set it up to start automatically on login.

## Quick Installation

### For All Users (System-Wide)

Run the installation script with sudo:

```bash
cd /path/to/market-pie5-bot
sudo ./install-desktop-icon.sh
```

This will:
- Install the desktop icon system-wide (`/usr/share/applications/`)
- Install the icon image (`/usr/share/pixmaps/`)
- Create a universal launcher script (`/usr/local/bin/market-pie5-launch-web-gui`)
- Optionally set up autostart for all users

### For Current User Only

Run the installation script without sudo:

```bash
cd /path/to/market-pie5-bot
./install-desktop-icon.sh
```

This will:
- Install the desktop icon for your user (`~/.local/share/applications/`)
- Install the icon image (`~/.local/share/icons/`)
- Optionally set up autostart for your user only

## Manual Installation

### System-Wide Installation

1. **Install the launcher script:**
   ```bash
   sudo cp launch-web-gui.sh /usr/local/bin/market-pie5-launch-web-gui
   sudo chmod 755 /usr/local/bin/market-pie5-launch-web-gui
   ```

2. **Install the desktop file:**
   ```bash
   sudo cp market-pie5-web-gui.desktop /usr/share/applications/
   sudo chmod 644 /usr/share/applications/market-pie5-web-gui.desktop
   ```

3. **Install the icon:**
   ```bash
   sudo cp market-pie5-icon.svg /usr/share/pixmaps/market-pie5-icon.svg
   sudo chmod 644 /usr/share/pixmaps/market-pie5-icon.svg
   ```

4. **Update desktop database:**
   ```bash
   sudo update-desktop-database /usr/share/applications/
   ```

### User-Specific Installation

1. **Create directories (if they don't exist):**
   ```bash
   mkdir -p ~/.local/share/applications
   mkdir -p ~/.local/share/icons
   ```

2. **Copy and edit the desktop file:**
   ```bash
   cp market-pie5-web-gui.desktop ~/.local/share/applications/
   # Edit the Exec line to point to your installation directory
   nano ~/.local/share/applications/market-pie5-web-gui.desktop
   ```

3. **Copy the icon:**
   ```bash
   cp market-pie5-icon.svg ~/.local/share/icons/
   ```

4. **Update desktop database:**
   ```bash
   update-desktop-database ~/.local/share/applications/
   ```

## Autostart Configuration

### System-Wide Autostart (All Users)

To make the application start automatically for all users on login:

```bash
sudo cp market-pie5-web-gui.desktop /etc/xdg/autostart/
sudo chmod 644 /etc/xdg/autostart/market-pie5-web-gui.desktop
sudo update-desktop-database /etc/xdg/autostart/
```

### User-Specific Autostart

To make the application start automatically for your user only:

```bash
mkdir -p ~/.config/autostart
cp market-pie5-web-gui.desktop ~/.config/autostart/
chmod 644 ~/.config/autostart/market-pie5-web-gui.desktop
update-desktop-database ~/.config/autostart/
```

## How It Works

The desktop file uses a universal launcher script (`/usr/local/bin/market-pie5-launch-web-gui`) that automatically detects the installation directory by checking common locations:

- `$HOME/market-pie5-bot`
- `$HOME/market-bot/market-pie5-bot`
- `/opt/market-pie5-bot`
- `/usr/local/market-pie5-bot`
- `/home/operator/market-pie5-bot`
- `/home/pi/market-pie5-bot`

Once found, it changes to that directory and runs `start_web_gui.sh`.

## Verification

After installation, you should see the "Market Pie5 Web Dashboard" icon in your application menu under:
- **Finance** category
- **Office** category
- **Network** category

You can also search for "Market Pie5" or "trading" in your application launcher.

## Troubleshooting

### Icon Not Appearing

1. **Update desktop database:**
   ```bash
   # For system-wide
   sudo update-desktop-database /usr/share/applications/
   
   # For user-specific
   update-desktop-database ~/.local/share/applications/
   ```

2. **Check file permissions:**
   ```bash
   ls -l /usr/share/applications/market-pie5-web-gui.desktop
   ls -l /usr/local/bin/market-pie5-launch-web-gui
   ```

3. **Verify icon file exists:**
   ```bash
   ls -l /usr/share/pixmaps/market-pie5-icon.svg
   ```

### Application Won't Start

1. **Check launcher script:**
   ```bash
   /usr/local/bin/market-pie5-launch-web-gui
   ```

2. **Verify installation directory:**
   The launcher script looks for `start_web_gui.sh` in common locations. Make sure your installation is in one of these directories, or update the launcher script.

3. **Check script permissions:**
   ```bash
   chmod +x /path/to/market-pie5-bot/start_web_gui.sh
   ```

### Autostart Not Working

1. **Check autostart directory:**
   ```bash
   ls -l /etc/xdg/autostart/market-pie5-web-gui.desktop
   # or
   ls -l ~/.config/autostart/market-pie5-web-gui.desktop
   ```

2. **Verify desktop file:**
   Make sure the `Exec` line in the desktop file points to the correct launcher script.

3. **Check desktop environment:**
   Some desktop environments may not support autostart. Check your desktop environment's documentation.

## Removing the Installation

### System-Wide Removal

```bash
sudo rm /usr/local/bin/market-pie5-launch-web-gui
sudo rm /usr/share/applications/market-pie5-web-gui.desktop
sudo rm /usr/share/pixmaps/market-pie5-icon.svg
sudo rm /etc/xdg/autostart/market-pie5-web-gui.desktop  # If autostart was enabled
sudo update-desktop-database /usr/share/applications/
sudo update-desktop-database /etc/xdg/autostart/
```

### User-Specific Removal

```bash
rm ~/.local/share/applications/market-pie5-web-gui.desktop
rm ~/.local/share/icons/market-pie5-icon.svg
rm ~/.config/autostart/market-pie5-web-gui.desktop  # If autostart was enabled
update-desktop-database ~/.local/share/applications/
update-desktop-database ~/.config/autostart/
```

## Notes

- The desktop file is configured to work for all users when installed system-wide
- The launcher script automatically detects the installation directory
- Autostart is optional and can be configured during installation or later
- The icon will appear in the application menu after installation and desktop database update
