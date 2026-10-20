# Documentation Index

**A comprehensive guide to all documentation in the market-pie5-bot project**

Last Updated: January 25, 2026

---

## 📋 Quick Navigation

- [Essential Documents](#essential-documents)
- [Getting Started](#getting-started)
- [User Guides](#user-guides)
- [Developer Documentation](#developer-documentation)
- [Feature Guides](#feature-guides)
- [Troubleshooting & Support](#troubleshooting--support)
- [Historical Archive](#historical-archive)

---

## 🎯 Essential Documents

**Start here if you're new to the project:**

| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](README.md) | Project overview, quick start, and features | Everyone |
| [MISSION.md](MISSION.md) | Bot mission: Phase 1 (stocks buy/short) → Phase 2 (options); production scope | Everyone |
| [DEV_DEPLOY_WORKFLOW.md](DEV_DEPLOY_WORKFLOW.md) | Build on Windows → run on Linux Mint (python3, venv); Git workflow, line endings, debug logs for Cursor | Developers |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Current project state, priorities, and metrics | Developers & Contributors |
| [ROADMAP.md](ROADMAP.md) | Development roadmap and TODO list | Developers & Contributors |
| [KNOWN_ISSUES.md](KNOWN_ISSUES.md) | Known bugs and limitations | Everyone |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute to the project | Contributors |

---

## 🚀 Getting Started

**Installation and Initial Setup:**

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Main installation instructions |
| [LINUX_MINT_GUIDE.md](LINUX_MINT_GUIDE.md) | **NEW!** Linux Mint installation and setup guide |
| [MARKET_MINT_BOT_GUIDE.md](MARKET_MINT_BOT_GUIDE.md) | **NEW!** Guide for creating a Linux Mint-focused fork |
| [USER_GUIDE.md](USER_GUIDE.md) | Complete user guide and walkthrough |
| [MANUAL_START_GUIDE.md](MANUAL_START_GUIDE.md) | Manual trading start with safety confirmation |
| [DESKTOP_ICONS_GUIDE.md](DESKTOP_ICONS_GUIDE.md) | Desktop integration for Raspberry Pi and Linux |
| [WEB_GUI_QUICKSTART.md](WEB_GUI_QUICKSTART.md) | Quick start for web interface |

---

## 👥 User Guides

**Comprehensive guides for using the trading bot:**

### Core Functionality
- **[USER_GUIDE.md](USER_GUIDE.md)** - Complete user guide with all features
- **[WEB_GUI_GUIDE.md](WEB_GUI_GUIDE.md)** - Web-based GUI documentation
- **[GUI_SETTINGS_GUIDE.md](GUI_SETTINGS_GUIDE.md)** - GUI settings and configuration
- **[SHUTDOWN_BUTTON_GUIDE.md](SHUTDOWN_BUTTON_GUIDE.md)** - Safe bot shutdown

### Trading Modes
- **[LIVE_MODE_GUIDE.md](LIVE_MODE_GUIDE.md)** - Live trading setup and safety
- **[YFINANCE_SIM_MODE.md](YFINANCE_SIM_MODE.md)** - yfinance simulation mode
- **[docs/YFINANCE_OPERATIONS.md](docs/YFINANCE_OPERATIONS.md)** - yfinance mode operations (start, test, see trades)
- **[BETTER_SIM_MIMIC_GUIDE.md](BETTER_SIM_MIMIC_GUIDE.md)** - Improved simulation behavior
- **[SANDBOX_LIVE_DISTINCTION.md](SANDBOX_LIVE_DISTINCTION.md)** - Sandbox vs Live mode differences

### Trading Features
- **[TRADING_ENHANCEMENTS_GUIDE.md](TRADING_ENHANCEMENTS_GUIDE.md)** - Advanced trading features
- **[docs/ENTRY_EXIT_PRICE_AUDIT.md](docs/ENTRY_EXIT_PRICE_AUDIT.md)** - Entry/exit price and order-type audit (current behavior, gaps, roadmap)
- **[STOCK_SCREENER_GUIDE.md](STOCK_SCREENER_GUIDE.md)** - Stock screening and filtering
- **[docs/SCREENER_TEST_ANALYSIS.md](docs/SCREENER_TEST_ANALYSIS.md)** - Capturing screener test output for Cursor analysis (timing, etc.)
- **[BACKTESTING_GUIDE.md](BACKTESTING_GUIDE.md)** - Strategy backtesting
- **[SENTIMENT_PORTFOLIO_GUIDE.md](SENTIMENT_PORTFOLIO_GUIDE.md)** - Sentiment analysis integration

### Security & Configuration
- **[TOKEN_ENCRYPTION_GUIDE.md](TOKEN_ENCRYPTION_GUIDE.md)** - API token encryption
- **[DATA_PRIVACY.md](DATA_PRIVACY.md)** - Data privacy and security
- **[EMAIL_ALERTS_GUIDE.md](EMAIL_ALERTS_GUIDE.md)** - Email alerts for trading events and errors
- **[ENV_CONFLICT_CHECKER_GUIDE.md](ENV_CONFLICT_CHECKER_GUIDE.md)** - Environment variable validation
- **[docs/ENV_SIMPLIFICATION.md](docs/ENV_SIMPLIFICATION.md)** - .env simplification, mode buttons, what affects what
- **[BRANCH_PROTECTION_GUIDE.md](BRANCH_PROTECTION_GUIDE.md)** - GitHub branch protection setup (NEW! ✅)
- **[COPILOT_SENTINEL_VISUAL_GUIDE.md](COPILOT_SENTINEL_VISUAL_GUIDE.md)** - Copilot Sentinel workflow diagrams (NEW! ✅)
 - **Copilot Label Gate**
     - [README.md](README.md#copilot-pr-label-gate) — Overview and manual fallback
     - [.github/workflows/copilot-label-gate.yml](.github/workflows/copilot-label-gate.yml) — Gate requiring `copilot-completed`
     - [.github/workflows/copilot-auto-label.yml](.github/workflows/copilot-auto-label.yml) — Auto-label when checks succeed
     - [CONTRIBUTING.md](CONTRIBUTING.md#copilot-pr-label-gate) — Contributor guidance

---

## 💻 Developer Documentation

**For contributors and developers:**

### Project Management
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current state, metrics, and priorities
- **[ROADMAP.md](ROADMAP.md)** - Development roadmap and active tasks
- **[KNOWN_ISSUES.md](KNOWN_ISSUES.md)** - Known bugs and limitations
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

### Development Guides
- **[VERIFICATION_GUIDE.md](VERIFICATION_GUIDE.md)** - Testing and validation guide
- **[PRE_COMMIT_HOOK_GUIDE.md](PRE_COMMIT_HOOK_GUIDE.md)** - Code quality pre-commit hook
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - Code style and conventions
- **[docs/README.md](docs/README.md)** - Documentation organization
- **[debug_logs/README.md](debug_logs/README.md)** - Debug logging system and Cursor integration

### Technical Implementation
- **[ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)** - Enhanced feature documentation
- **[WHATS_NEW.md](WHATS_NEW.md)** - Recent additions and changes
- **[PERFORMANCE_BENCHMARKS.md](PERFORMANCE_BENCHMARKS.md)** - Performance metrics

---

## 🔧 Feature Guides

**Detailed guides for specific features:**

### AI & Machine Learning
- **[ML_GUIDE.md](ML_GUIDE.md)** - Machine learning integration
- **[AI_IMPROVEMENTS_GUIDE.md](AI_IMPROVEMENTS_GUIDE.md)** - AI-powered features
- **[AI_RECOMMENDATIONS_ANALYSIS.md](AI_RECOMMENDATIONS_ANALYSIS.md)** - AI recommendations

### Stock Analysis
- **[STOCK_SCREENER_GUIDE.md](STOCK_SCREENER_GUIDE.md)** - Stock screening
- **[STOCK_SCREENER_ENHANCEMENTS.md](STOCK_SCREENER_ENHANCEMENTS.md)** - Advanced screening
- **[IMPLEMENTATION_SUMMARY_STOCK_SCREENER.md](IMPLEMENTATION_SUMMARY_STOCK_SCREENER.md)** - Implementation details

### Backtesting
- **[BACKTESTING_GUIDE.md](BACKTESTING_GUIDE.md)** - Backtesting framework
- **[SWING_BACKTEST_SUMMARY.md](SWING_BACKTEST_SUMMARY.md)** - Swing trading backtests

### Competitive Analysis
- **[COMPETITIVE_ANALYSIS.md](COMPETITIVE_ANALYSIS.md)** - Comparison with other bots
- **[GITHUB_TOPICS.md](GITHUB_TOPICS.md)** - GitHub topics and discoverability

---

## 🆘 Troubleshooting & Support

**Getting help and solving problems:**

### Issue Tracking
- **[KNOWN_ISSUES.md](KNOWN_ISSUES.md)** - Known bugs and workarounds
- **[GitHub Issues](https://github.com/operator/market-pie5-bot/issues)** - Report new issues

### Validation & Verification
- **[docs/TEST_FAILURES_ANALYSIS.md](docs/TEST_FAILURES_ANALYSIS.md)** - Test failure breakdown (92 fail, 41 error), root causes, fix order
- **[ISSUE_VALIDATION_REPORT.md](ISSUE_VALIDATION_REPORT.md)** - Issue validation results
- **[ISSUE_RESOLUTION_SUMMARY.md](ISSUE_RESOLUTION_SUMMARY.md)** - Resolved issues
- **[ISSUE_RESOLUTION_CONFIRMATION_DIALOGS.md](ISSUE_RESOLUTION_CONFIRMATION_DIALOGS.md)** - Confirmation dialogs

### Support Resources
- **[README.md](README.md)** - Troubleshooting section
- **[USER_GUIDE.md](USER_GUIDE.md)** - Common questions
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Getting help section

---

## 📚 Historical Archive

**Historical documentation preserved for reference:**

The project has extensive historical documentation from various development phases. These documents are preserved in the `docs/archive/` directory and catalogued in:

- **[docs/ARCHIVE.md](docs/ARCHIVE.md)** - Complete archive index with 87 historical documents

### Archive Categories
- **Implementation Summaries:** Feature development documentation
- **Fix Summaries:** Bug fixes and issue resolution (12+ fix summary documents)
- **PR Summaries:** Pull request documentation
- **Feature Comparisons:** Visual comparisons and analysis
- **Validation Reports:** Testing and validation documentation

**Note:** Archive documents are for reference only and are not actively maintained. For current documentation, use the guides in this index.

---

## 📁 Documentation Organization

### Directory Structure
```
market-pie5-bot/
├── README.md                          # Main project documentation
├── DOCUMENTATION_INDEX.md             # This file - central navigation
├── PROJECT_STATUS.md                  # Project status and priorities
├── ROADMAP.md                         # Development roadmap
├── KNOWN_ISSUES.md                    # Known bugs and limitations
├── CONTRIBUTING.md                    # Contribution guidelines
├── *.md (38 files)                    # Feature and user guides
├── .github/
│   ├── copilot-instructions.md        # Development standards
│   └── ISSUE_TEMPLATE/                # Issue templates
└── docs/
    ├── README.md                      # Docs directory guide
    ├── ARCHIVE.md                     # Archive index
    └── archive/                       # Historical documents (87 files)
```

### Document Types

| Type | Location | Maintenance |
|------|----------|-------------|
| **Core Docs** | Root directory | Actively maintained |
| **User Guides** | Root directory | Updated with features |
| **Developer Docs** | Root + .github/ | Updated as needed |
| **Archive** | docs/archive/ | Preserved, not updated |

---

## 🔍 Finding What You Need

### By Role

**New User:**
1. Start with [README.md](README.md)
2. Read [USER_GUIDE.md](USER_GUIDE.md)
3. Follow [WEB_GUI_QUICKSTART.md](WEB_GUI_QUICKSTART.md)

**Mission & Production Readiness:**
1. Read [MISSION.md](MISSION.md) — Phase 1 (stocks buy/short) → Phase 2 (options)
2. Use Phase 1 production checklist and gap analysis in MISSION
3. Align work with [ROADMAP.md](ROADMAP.md) and [PROJECT_STATUS.md](PROJECT_STATUS.md)

**Build on Windows, run on Linux Mint:**
1. See [DEV_DEPLOY_WORKFLOW.md](DEV_DEPLOY_WORKFLOW.md) — edit on Windows, push to GitHub, pull on Linux Mint
2. Run tests and bot with `python3` in venv on the server
3. Use [.gitattributes](.gitattributes) for LF line endings (shell scripts, Python)

**Developer/Contributor:**
1. Review [MISSION.md](MISSION.md) and [PROJECT_STATUS.md](PROJECT_STATUS.md)
2. Check [ROADMAP.md](ROADMAP.md) for tasks
3. Read [CONTRIBUTING.md](CONTRIBUTING.md)
4. Check [KNOWN_ISSUES.md](KNOWN_ISSUES.md)

**Trader (Production Use):**
1. Study [LIVE_MODE_GUIDE.md](LIVE_MODE_GUIDE.md)
2. Review [TRADING_ENHANCEMENTS_GUIDE.md](TRADING_ENHANCEMENTS_GUIDE.md)
3. Test with [BACKTESTING_GUIDE.md](BACKTESTING_GUIDE.md)
4. Check [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for limitations

### By Topic

Use the search function (Ctrl+F / Cmd+F) in this document to find:
- Specific features (e.g., "backtesting", "sentiment")
- Document types (e.g., "guide", "summary")
- Areas of interest (e.g., "security", "trading")

---

## 📝 Documentation Standards

### When to Update Documentation
- New features added
- Feature behavior changed
- Bug fixes affecting user experience
- Configuration changes
- Breaking changes

### How to Contribute Documentation
1. Follow the style guide in [CONTRIBUTING.md](CONTRIBUTING.md)
2. Keep language clear and simple
3. Include examples and screenshots
4. Link between related documents
5. Update this index if adding new documents

### Quality Standards
- **Accuracy:** Keep documentation in sync with code
- **Clarity:** Write for the intended audience
- **Completeness:** Cover all important aspects
- **Maintainability:** Regular reviews and updates
- **Discoverability:** Link from this index

---

## 🔄 Recent Documentation Updates

**January 2026:**
- ✅ **Created [MISSION.md](MISSION.md)** — Canonical mission: Phase 1 (stocks buy/short) → Phase 2 (options); production scope, gap analysis, Phase 1 checklist
- ✅ Updated README, PROJECT_STATUS, ROADMAP, DOCUMENTATION_INDEX to reference MISSION
- ✅ Short selling (Phase 1) added as top priority in ROADMAP and PROJECT_STATUS
- ✅ Created DOCUMENTATION_INDEX.md (this file)
- ✅ Added KNOWN_ISSUES.md for transparent issue tracking
- ✅ Updated PROJECT_STATUS.md with known issues section
- ✅ Consolidated archive documentation in docs/ARCHIVE.md
- ✅ Added GitHub issue templates for better tracking

**Previous Updates:**
- See [CHANGELOG.md](CHANGELOG.md) for version history
- See [docs/ARCHIVE.md](docs/ARCHIVE.md) for historical summaries

---

## 💡 Tips for Navigation

1. **Bookmark this page** for quick access to all documentation
2. **Use browser search** (Ctrl+F / Cmd+F) to find specific topics
3. **Check dates** - newer documents may supersede older ones
4. **Start specific** - use feature guides for detailed information
5. **Go broad** - use README/USER_GUIDE for general information

---

## 📞 Need Help?

**Can't find what you need?**

1. Search this index for keywords
2. Check [README.md](README.md) table of contents
3. Review [KNOWN_ISSUES.md](KNOWN_ISSUES.md)
4. Search [GitHub Issues](https://github.com/operator/market-pie5-bot/issues)
5. Create a new issue with the `question` label

**Found outdated documentation?**

1. Open an issue with the `documentation` label
2. Submit a PR with corrections
3. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines

---

## ✅ Documentation Health

**Current Status: Good**

- **Total Documents:** 126 (38 active + 87 archived + 1 index)
- **Active Maintenance:** Core docs regularly updated
- **Archive Management:** Historical docs properly catalogued
- **Discoverability:** Centralized via this index
- **Standards:** Defined in CONTRIBUTING.md

**Quality Metrics:**
- ✅ Core documentation up-to-date
- ✅ User guides comprehensive
- ✅ Developer docs available
- ✅ Archive properly organized
- ✅ Navigation centralized

---

**Last Updated:** January 25, 2026

For questions about documentation, open an issue with the `documentation` label.
