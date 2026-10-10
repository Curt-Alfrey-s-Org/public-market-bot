# Creating Market-Mint-Bot - A Linux Mint Fork Guide

This guide explains how to create a Linux Mint-focused fork of the Market Pie5 Bot called "Market-Mint-Bot".

---

## 🎯 Overview

**Market-Mint-Bot** is a Linux Mint-optimized fork of the original Market Pie5 Bot, specifically tailored for Linux Mint users while maintaining full compatibility with all features.

### Why a Separate Repository?

- **Focused Branding:** Linux Mint-specific branding and documentation
- **Platform Optimization:** Optimized defaults for desktop Linux systems
- **Community:** Dedicated community for Linux Mint users
- **Simplified Onboarding:** Linux Mint users get a tailored experience

---

## 📋 Steps to Create Market-Mint-Bot Repository

### Step 1: Fork/Create Repository on GitHub

#### Option A: Fork the Original Repository

1. Go to: https://github.com/operator/market-pie5-bot
2. Click the "Fork" button in the top-right
3. Name your fork: **Market-Mint-Bot**
4. Add description: "Intelligent trading bot optimized for Linux Mint - AI-powered strategy optimization, paper trading, and comprehensive GUI"
5. Click "Create fork"

#### Option B: Create New Repository

1. Go to: https://github.com/new
2. Repository name: **Market-Mint-Bot**
3. Description: "Intelligent trading bot optimized for Linux Mint - AI-powered strategy optimization, paper trading, and comprehensive GUI"
4. Visibility: Public (or Private)
5. Initialize with README: No (we'll add our own)
6. Click "Create repository"

### Step 2: Clone and Prepare

If you forked (Option A):
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Market-Mint-Bot.git
cd Market-Mint-Bot
```

If you created new (Option B):
```bash
# Clone the original and push to your new repo
git clone https://github.com/operator/market-pie5-bot.git Market-Mint-Bot
cd Market-Mint-Bot

# Remove original remote
git remote remove origin

# Add your new remote
git remote add origin https://github.com/YOUR_USERNAME/Market-Mint-Bot.git

# Push to your new repository
git branch -M main
git push -u origin main
```

### Step 3: Rebrand Files

Update the following files for Market-Mint-Bot branding:

#### 1. Update README.md

Find and replace references:
```bash
# In README.md
- Change "market-pie5-bot" to "Market-Mint-Bot"
- Change "Raspberry Pi 5" to "Linux Mint"
- Update repository URLs
- Update badge URLs
- Change description to focus on Linux Mint
```

Example changes:
```markdown
# Market-Mint-Bot

[![Linux Mint](https://img.shields.io/
[![Python](https://img.shields.io/

**An intelligent, self-scaling trading bot optimized for Linux Mint with AI-powered strategy optimization, paper trading, PDT compliance, and comprehensive GUI.**
```

#### 2. Update package.json

```json
{
  "name": "market-mint-bot",
  "version": "1.0.0",
  "description": "Trading bot optimized for Linux Mint - Enhanced web GUI with visual assets and styling",
  ...
}
```

#### 3. Rename Desktop Files

```bash
# Rename desktop files
mv market-pie5-bot.desktop market-mint-bot.desktop
mv market-pie5-web-gui.desktop market-mint-web-gui.desktop

# Update contents of both files:
# - Change Name= fields
# - Change Comment= fields to reference Linux Mint
# - Update Exec= paths to use /home/YOUR_USER/ or $HOME
```

Example for `market-mint-bot.desktop`:
```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Market Mint Bot (Desktop GUI)
Comment=Trading bot with desktop GUI for Linux Mint
Exec=/home/$USER/Market-Mint-Bot/start_bot.sh
Icon=utilities-terminal
Terminal=true
Categories=Finance;Office;
Keywords=trading;stock;bot;finance;desktop;gui;linuxmint;
StartupNotify=true
StartupWMClass=market-mint-bot
```

#### 4. Update install.sh

Change clone URL:
```bash
# Line 30 in install.sh
git clone https://github.com/YOUR_USERNAME/Market-Mint-Bot.git || {
    ...
}
```

#### 5. Update Documentation Files

Update references in all documentation:
```bash
# Files to update:
# - CONTRIBUTING.md (repository URLs)
# - USER_GUIDE.md (branding)
# - WEB_GUI_GUIDE.md (title references)
# - DOCUMENTATION_INDEX.md (update links)
# - All *_GUIDE.md files (check for hardcoded repo names)
```

#### 6. Create Linux Mint Specific README

Create a prominent notice at the top of README.md:
```markdown
## 🐧 Linux Mint Optimized

This is **Market-Mint-Bot**, a Linux Mint-optimized version of the Market Pie5 Bot. 

- ✅ Fully compatible with Linux Mint 20.x, 21.x, and newer
- ✅ Works on Ubuntu, Debian, and other Debian-based distributions
- ✅ Optimized for desktop Linux systems
- ✅ All features from the original bot included

**Original Repository:** [market-pie5-bot](https://github.com/operator/market-pie5-bot)
```

### Step 4: Update Configuration Defaults

Edit `.env.example` for Linux Mint-specific defaults:

```bash
# At the top of .env.example, add:
# Market-Mint-Bot Configuration Template
# Optimized for Linux Mint
# Copy this file to .env and customize for your setup
```

Consider adjusting defaults:
```bash
# More conservative defaults for desktop systems
BOT_MAX_CPU_PERCENT=70  # Allow more CPU for powerful desktops
BOT_MAX_MEMORY_PERCENT=75
BOT_ENABLE_THROTTLING=true  # But still enable throttling

# May have more processing power than Raspberry Pi
ASYNC_MAX_CONCURRENT_REQUESTS=10  # Increased from 5
```

### Step 5: Add Linux Mint Installation Instructions

Add a dedicated `INSTALL_LINUX_MINT.md` (you can use the LINUX_MINT_GUIDE.md created earlier):

```bash
# Copy the Linux Mint guide as the primary installation doc
cp LINUX_MINT_GUIDE.md INSTALL.md

# Update README to link to it prominently
```

### Step 6: Update GitHub Repository Settings

After pushing your changes:

1. **Repository Settings:**
   - Go to Settings → General
   - Update description
   - Add topics/tags:
     - `linux-mint`
     - `trading-bot`
     - `python`
     - `algorithmic-trading`
     - `stock-trading`
     - `debian`
     - `ubuntu-compatible`

2. **README Badges:**
   Update CI/CD badge URLs to point to your repository

3. **About Section:**
   Add website link (optional): Your documentation URL or project page

### Step 7: Create Initial Release

1. Commit all changes:
```bash
git add .
git commit -m "Initial Market-Mint-Bot release - Linux Mint optimized fork"
git push origin main
```

2. Create a release:
   - Go to Releases → Create a new release
   - Tag: `v1.0.0-mint`
   - Title: "Market-Mint-Bot v1.0.0 - Linux Mint Edition"
   - Description: Highlight Linux Mint optimizations and features
   - Click "Publish release"

### Step 8: Update Documentation

Create or update these files:

#### FORK_RELATIONSHIP.md
```markdown
# Relationship to Original Project

Market-Mint-Bot is a Linux Mint-optimized fork of [market-pie5-bot](https://github.com/operator/market-pie5-bot).

## Differences from Original

- Branding focused on Linux Mint
- Installation instructions optimized for Linux Mint
- Default configurations tuned for desktop Linux
- Documentation tailored for Linux Mint users

## Syncing with Upstream

To pull updates from the original repository:

\`\`\`bash
# Add upstream remote (one time)
git remote add upstream https://github.com/operator/market-pie5-bot.git

# Fetch and merge updates
git fetch upstream
git merge upstream/main

# Resolve conflicts if any, then push
git push origin main
\`\`\`

## Contributing

Contributions to Market-Mint-Bot are welcome! 
For contributions to the core trading engine, consider contributing to the upstream project.
```

---

## 🔄 Maintaining the Fork

### Regular Updates from Upstream

```bash
# Add upstream remote (if not already added)
git remote add upstream https://github.com/operator/market-pie5-bot.git

# Fetch upstream changes
git fetch upstream

# Merge upstream main into your main
git checkout main
git merge upstream/main

# Resolve conflicts (if any)
# Then push to your fork
git push origin main
```

### Keep Linux Mint Focus

When merging upstream:
- Preserve Linux Mint branding
- Keep Linux Mint-specific documentation
- Maintain Linux Mint-optimized defaults
- Update any new files with Market-Mint-Bot branding

---

## 📝 Branding Guidelines

### Naming Conventions

- **Repository:** Market-Mint-Bot
- **Package:** market-mint-bot
- **Display Name:** Market Mint Bot
- **Short Name:** MMB (for logs, configs)

### Color Scheme (Optional)

Consider Linux Mint's colors:
- Primary: #87CF3E (Linux Mint green)
- Dark: #5F9C32
- Background: Keep existing or adapt

### Logo (Optional)

Create a custom logo that:
- References Linux Mint branding
- Includes trading/financial elements
- Maintains professional appearance
- Add to assets/ directory

---

## 🎨 Optional Enhancements

### Linux Mint-Specific Features

Consider adding:

1. **Cinnamon Desklet** (Linux Mint's desktop widgets)
   - Real-time portfolio value
   - Today's P&L
   - Active positions count

2. **System Tray Integration**
   - Bot status indicator
   - Quick start/stop
   - Notification support

3. **Theme Integration**
   - Match Linux Mint themes
   - Support for dark/light mode detection

4. **Software Manager Package**
   - Create .deb package
   - Submit to Linux Mint Software Manager

### Installation Script Enhancement

Update `install.sh` with Linux Mint detection:

```bash
#!/bin/bash
# Market-Mint-Bot Installation Script for Linux Mint

echo "=== Market-Mint-Bot Installation Script ==="
echo "Optimized for Linux Mint"
echo ""

# Detect Linux Mint
if [ -f /etc/linuxmint/info ]; then
    echo "✓ Linux Mint detected"
    MINT_VERSION=$(grep RELEASE /etc/linuxmint/info | cut -d= -f2)
    echo "  Version: $MINT_VERSION"
elif [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "✓ Detected: $NAME $VERSION_ID"
else
    echo "⚠ Could not detect OS version"
fi

# Continue with installation...
```

---

## 📢 Promoting Market-Mint-Bot

### Community Engagement

1. **Linux Mint Forums:**
   - Post in Software & Applications
   - Share your project
   - Offer support

2. **Reddit:**
   - r/linuxmint
   - r/algotrading
   - r/Python

3. **Linux Mint Community:**
   - Share in Linux Mint blog comments
   - Contribute to Linux Mint ecosystem

### Documentation

Create comprehensive docs:
- Video tutorials (optional)
- Screenshots showing Linux Mint integration
- Step-by-step guides
- FAQ specific to Linux Mint

---

## ⚖️ Legal Considerations

### License Compliance

The original project uses MIT License, which allows:
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use

Requirements:
- ✅ Include original license
- ✅ Include copyright notice
- ✅ State changes made

### Attributing Original Work

Always include in your README:
```markdown
## Attribution

Market-Mint-Bot is based on [market-pie5-bot](https://github.com/operator/market-pie5-bot) by operators Alfrey.

Original project licensed under MIT License.
See [LICENSE](LICENSE) for details.
```

---

## 🚀 Launch Checklist

Before announcing Market-Mint-Bot:

- [ ] All branding updated (name, logos, docs)
- [ ] Repository properly configured
- [ ] Installation tested on Linux Mint 20.x and 21.x
- [ ] Desktop integration works correctly
- [ ] Documentation is complete and accurate
- [ ] License file includes attribution
- [ ] README has prominent Linux Mint notice
- [ ] All URLs point to correct repository
- [ ] Initial release created
- [ ] GitHub topics/tags added
- [ ] Fork relationship documented
- [ ] Contributing guidelines updated

---

## 📚 Resources

- **Linux Mint:** https://linuxmint.com/
- **Original Project:** https://github.com/operator/market-pie5-bot
- **GitHub Forks:** https://docs.github.com/en/get-started/quickstart/fork-a-repo
- **Maintaining Forks:** https://docs.github.com/

---

## 🤝 Questions?

If you need help creating Market-Mint-Bot:
- Review this guide carefully
- Check GitHub's fork documentation
- Ask in Linux Mint forums
- Open an issue in the original repository (for technical questions)

---

**Good luck with Market-Mint-Bot! 🚀🐧📈**
