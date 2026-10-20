# Market Pie5 Bot Icon

This directory contains the custom icon for the Market Pie5 Bot application.

## Icon File

**market-pie5-icon.svg** - Scalable Vector Graphics icon (128x128 logical size)

### Design Elements

The icon represents the "Market Pie5 Bot" concept with:
- **Pie Chart**: Colorful pie chart segments representing portfolio diversification
- **Pi Symbol (π)**: Mathematical symbol in the center, referencing "Pie5" name
- **Gear Icon**: Small gear at bottom representing automation/bot functionality
- **Upward Arrow**: Trading/financial growth indicator
- **Number "5"**: Reference to Raspberry Pi 5 platform
- **Green Background**: Financial/growth theme

### Color Palette
- Green background: #2E7D32 (financial growth)
- Pie segments: Red (#E53935), Blue (#1E88E5), Yellow (#FDD835), Purple (#8E24AA), Orange (#FF6F00), Green (#43A047)
- Gear: #455A64 (blue-grey)
- Text: White and dark green for contrast

## Usage

The icon is referenced in the desktop entry files:
- `market-pie5-bot.desktop` - Desktop GUI launcher
- `market-pie5-web-gui.desktop` - Web Dashboard launcher

Both use the SVG icon with absolute path:
```ini
Icon=/home/pi/market-pie5-bot/market-pie5-icon.svg
```

The installation scripts (`install.sh` and `install_desktop_icons.sh`) automatically update the path during installation to match your actual installation directory.

## File Formats

### SVG (Included)
- **market-pie5-icon.svg** - Scalable vector format
- Advantages: Perfect at any size, small file size, easily editable
- Supported by most modern desktop environments

### PNG (Optional)
To create PNG versions for better compatibility:

```bash
# Install librsvg2-bin for conversion
sudo apt install librsvg2-bin

# Generate various sizes
rsvg-convert -w 48 -h 48 market-pie5-icon.svg -o market-pie5-icon-48.png
rsvg-convert -w 64 -h 64 market-pie5-icon.svg -o market-pie5-icon-64.png
rsvg-convert -w 128 -h 128 market-pie5-icon.svg -o market-pie5-icon-128.png
rsvg-convert -w 256 -h 256 market-pie5-icon.svg -o market-pie5-icon-256.png
```

Common icon sizes for Linux desktop environments:
- 48x48 - Standard icon size
- 64x64 - Medium icon size
- 128x128 - Large icon size
- 256x256 - Hi-DPI displays

## Installation

The icon is automatically installed when you:

1. Run the main installer:
   ```bash
   ./install.sh
   # Answer 'y' to desktop icons prompt
   ```

2. Or use the standalone installer:
   ```bash
   ./install_desktop_icons.sh
   ```

Both scripts will:
- Copy desktop files to `~/.local/share/applications/`
- Update icon paths to match your installation directory
- Refresh the desktop database

## Manual Installation

If you want to install the icon manually:

1. Copy the icon to a standard location:
   ```bash
   mkdir -p ~/.local/share/icons/hicolor/scalable/apps/
   cp market-pie5-icon.svg ~/.local/share/icons/hicolor/scalable/apps/
   ```

2. Update icon cache:
   ```bash
   gtk-update-icon-cache ~/.local/share/icons/hicolor/
   ```

3. Edit desktop files to reference the icon:
   ```ini
   Icon=market-pie5-icon
   ```
   Or use absolute path:
   ```ini
   Icon=/path/to/market-pie5-bot/market-pie5-icon.svg
   ```

## Customization

To customize the icon:

1. Edit `market-pie5-icon.svg` with any vector graphics editor:
   - Inkscape (recommended, open-source)
   - Adobe Illustrator
   - Any text editor (it's XML-based)

2. Save your changes

3. Reinstall desktop icons:
   ```bash
   ./install_desktop_icons.sh
   ```

## Troubleshooting

**Icon doesn't appear:**
1. Make sure the file exists: `ls -la market-pie5-icon.svg`
2. Check desktop file icon path: `grep Icon ~/.local/share/applications/market-pie5*.desktop`
3. Refresh desktop database: `update-desktop-database ~/.local/share/applications/`
4. Log out and back in to reload desktop environment

**Generic icon shown instead:**
- Some desktop environments don't support SVG icons
- Solution: Generate PNG versions (see above) and reference them in desktop files

**Icon looks blurry:**
- Generate higher resolution PNG: `rsvg-convert -w 256 -h 256 ...`
- Or use SVG for perfect scaling (modern desktop environments)

## License

This icon is part of the Market Pie5 Bot project and follows the same license as the main project (GNU General Public License v3.0).
