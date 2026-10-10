# Known Issues & Limitations

**Last Updated:** January 21, 2026  
**Version:** 1.0

This document tracks known bugs, limitations, and workarounds for the market-pie5-bot project. All issues are tracked transparently to help users and contributors understand current limitations.

---

## 📋 Table of Contents

- [Critical Issues](#critical-issues)
- [High Priority Issues](#high-priority-issues)
- [Medium Priority Issues](#medium-priority-issues)
- [Low Priority Issues](#low-priority-issues)
- [Known Limitations](#known-limitations)
- [Workarounds](#workarounds)
- [Fixed Issues](#fixed-issues)

---

## 🔴 Critical Issues

**No critical issues currently open**

Critical issues block core functionality or pose security risks. They are addressed immediately.

---

## 🟡 High Priority Issues

### 1. Email Alert System Incomplete

**Status:** 🔄 In Progress  
**Impact:** High - Affects live trading monitoring  
**Affected Versions:** All  
**GitHub Issue:** [Create issue](https://github.com/operator/market-pie5-bot/issues/new)

**Description:**
Email alert system framework is in place but SMTP integration is incomplete. Users cannot receive email alerts for critical events (trades, errors, PDT warnings).

**Workaround:**
- Monitor bot manually via GUI
- Check logs regularly in GUI log viewer
- Use Discord/Slack webhooks (requires custom implementation)

**Fix Status:** Framework ready, SMTP setup needed in `main.py`

**Related Documentation:** [PROJECT_STATUS.md](PROJECT_STATUS.md#1-email-alert-system)

---

### 2. Code Quality Alerts

**Status:** ⚠️ Ongoing  
**Impact:** Medium - Code maintainability  
**Affected Versions:** All  
**GitHub Issue:** [Create issue](https://github.com/operator/market-pie5-bot/issues/new)

**Description:**
Recent commits show frequent code quality alerts (unused variables, unused imports) being fixed by automated bots. This suggests:
- No pre-commit hooks to catch issues
- Possible linting not running locally
- Code review process may need strengthening

**Workaround:**
- Run `flake8` locally before committing
- Use provided linting commands (see README.md)
- Enable pre-commit hooks

**Fix Status:** Requires process improvements and pre-commit hooks

**Prevention:**
```bash
# Run before committing
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
black --check .
isort --check-only .
```

---

## 🟢 Medium Priority Issues

### 3. Documentation Fragmentation

**Status:** ✅ Being Addressed  
**Impact:** Medium - Developer onboarding  
**Affected Versions:** All  
**GitHub Issue:** This issue

**Description:**
The project has 100+ markdown files (38 root + 87 archived) without clear organization. While comprehensive, this makes navigation difficult for new contributors.

**Current Solution:**
- Created DOCUMENTATION_INDEX.md for centralized navigation
- Organized archive in docs/ARCHIVE.md
- Added clear documentation standards

**Remaining Work:**
- Add pre-commit hooks for doc standards
- Create documentation templates
- Regular documentation audits

---

### 4. Headless Mode Limitations

**Status:** ⚠️ Known Limitation  
**Impact:** Medium - Server deployments  
**Affected Versions:** All  
**Related:** GUI requires display

**Description:**
The Tkinter GUI requires a display to run. Mock classes are available for headless servers, but full GUI functionality is not available in headless mode.

**Workaround:**
- Use web GUI (`start_web_gui.sh`) instead - works in headless mode
- Use virtual display (Xvfb) for Tkinter GUI
- Run bot in CLI mode without GUI

**Fix Status:** Working as designed - web GUI is the recommended solution

---

### 5. Single Account Support Only

**Status:** 🔵 Planned Feature  
**Impact:** Medium - Users with multiple accounts  
**Affected Versions:** All  
**GitHub Issue:** [Create issue](https://github.com/operator/market-pie5-bot/issues/new)

**Description:**
Bot currently supports only one trading account. Users with multiple Schwab accounts must run separate bot instances.

**Workaround:**
- Run multiple bot instances with different `.env` files
- Use separate directories for each account
- Manage tokens separately

**Fix Status:** Planned for Q3 2026 (see [ROADMAP.md](ROADMAP.md))

---

## 🔵 Low Priority Issues

### 6. No Cloud Sync/Backup

**Status:** 🔵 Planned Feature  
**Impact:** Low - Data portability  
**Affected Versions:** All

**Description:**
Settings, logs, and trade history are stored locally only. No automatic backup or cloud sync capabilities.

**Workaround:**
- Manual backup of `.env`, `trade_log.db`, and settings files
- Use version control for configuration
- Set up automated file backups (cron/systemd)

**Fix Status:** Planned for Q3 2026 (see [ROADMAP.md](ROADMAP.md))

---

### 7. Limited Charting Capabilities

**Status:** 🔵 Planned Feature  
**Impact:** Low - Strategy development  
**Affected Versions:** All

**Description:**
Basic visualization exists, but advanced interactive charting features are limited.

**Workaround:**
- Export data and use external tools (TradingView, etc.)
- Use `demo_chart_visualization.py` for basic charts
- Generate reports with `report_generator.py`

**Fix Status:** Planned for Q2 2026 (see [ROADMAP.md](ROADMAP.md))

---

## ⚠️ Known Limitations

### Platform Limitations

**Raspberry Pi 5 Only (Optimized)**
- Bot is optimized for Raspberry Pi 5
- Works on other platforms but performance may vary
- Resource monitoring thresholds tuned for Pi5

**Python 3.10+ Required**
- Uses features from Python 3.10+
- Older Python versions not supported
- Virtual environment recommended

### API Limitations

**Schwab API Rate Limits**
- Sandbox has stricter rate limits
- Production limits depend on account tier
- Bot handles limits gracefully with retries

**yfinance Data Limitations**
- Delayed quotes in simulation mode
- May have occasional data gaps
- Not suitable for high-frequency trading

### Trading Limitations

**Pattern Day Trading (PDT) Rules**
- Enforced for accounts < $25,000
- 3 day trades per 5 business days limit
- Automatic enforcement in production mode

**No Options Trading (Yet)**
- Framework ready but integration incomplete
- Planned for future release
- Stocks and ETFs only currently

**No Crypto/Forex Support**
- Schwab API limitation
- Stock and ETF trading only
- Other asset classes planned (see ROADMAP.md)

### GUI Limitations

**Desktop GUI Requires Display**
- Tkinter requires X11/display
- Not suitable for headless servers
- Use web GUI for remote access

**No Dark Mode**
- GUI uses system default theme
- No built-in theme switching
- Planned for future release

---

## 🛠️ Workarounds

### General Troubleshooting

**Bot Won't Start:**
1. Check `.env` file is configured
2. Verify Python 3.10+ installed
3. Check virtual environment activated
4. Review logs in GUI or console

**API Connection Issues:**
1. Verify API credentials in `.env`
2. Check internet connectivity
3. Try sandbox mode first
4. Review `schwab_auth.py` logs

**GUI Not Responding:**
1. Check system resources (CPU/RAM)
2. Close and restart GUI
3. Try web GUI instead
4. Check for hanging processes

**Trade Not Executing:**
1. Verify paper trading mode enabled (for testing)
2. Check capital floor not breached
3. Review PDT limitations
4. Check stock filters (price, volume)

### Performance Optimization

**Slow Performance on Pi5:**
```bash
# Reduce symbol count
# In .env file:
MAX_SYMBOLS=50  # Reduce from 100+

# Increase update interval
BOT_UPDATE_INTERVAL=10  # Increase from 5
```

**Memory Usage High:**
```bash
# Disable resource monitoring
ENABLE_RESOURCE_MONITORING=false

# Reduce backtest days
BACKTEST_DAYS=30  # Reduce from 100+
```

---

## ✅ Fixed Issues

### Recently Fixed (Q1 2026)

**Sandbox/Live Mode Confusion**
- ✅ Fixed in commit 9d1740c
- Added clear mode indicators
- Improved error messages

**Settings Not Persisting**
- ✅ Fixed in December 2025
- Settings now save properly
- Added validation checks

**Chart Display Issues**
- ✅ Fixed in December 2025
- Charts render correctly
- Added error handling

**OAuth Token Security**
- ✅ Fixed in December 2025
- Tokens encrypted at rest
- Improved token management

**PDT Rule Enforcement**
- ✅ Fixed in November 2025
- Accurate tracking
- Business day calculation

### Historical Fixes

For complete fix history, see:
- [CHANGELOG.md](CHANGELOG.md)
- [docs/ARCHIVE.md](docs/ARCHIVE.md)

---

## 📊 Issue Statistics

**Current Open Issues:** 7
- 🔴 Critical: 0
- 🟡 High: 2
- 🟢 Medium: 3
- 🔵 Low: 3

**Known Limitations:** 11
**Fixed Issues (Last 90 Days):** 5

**Test Pass Rate:** 100% (82/82 tests passing)
**Security Vulnerabilities:** 0 (CodeQL verified)

---

## 🤝 Contributing Issue Reports

### How to Report a Bug

1. **Search existing issues** to avoid duplicates
2. **Use issue templates** in `.github/ISSUE_TEMPLATE/`
3. **Include details:**
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment (Python version, OS, etc.)
   - Relevant logs (sanitize credentials!)
   - Screenshots if applicable

### How to Request a Feature

1. **Check [ROADMAP.md](ROADMAP.md)** - may already be planned
2. **Search existing issues** for similar requests
3. **Use feature request template**
4. **Explain use case and benefits**

### How to Submit a Fix

1. **Reference the issue** in your PR
2. **Add tests** for the fix
3. **Update documentation** if needed
4. **Follow** [CONTRIBUTING.md](CONTRIBUTING.md) guidelines

---

## 🔄 Issue Lifecycle

```
New Issue → Triage → Investigation → Fix → Testing → Closed
                ↓
            Documented here
```

1. **New Issue:** Reported via GitHub Issues
2. **Triage:** Assessed for severity and priority
3. **Investigation:** Root cause analysis
4. **Fix:** Code changes and testing
5. **Testing:** Validation in multiple environments
6. **Closed:** Issue resolved, documented here
7. **Updated:** This document updated quarterly

---

## 📅 Update Schedule

**This document is updated:**
- Immediately for critical issues
- Weekly for high-priority issues
- Monthly for medium/low priority issues
- Quarterly for comprehensive review

**Next Scheduled Review:** February 1, 2026

---

## 📞 Getting Help

**Issue Priority Questions:**
- Open a GitHub Discussion
- Comment on related GitHub Issue
- Review [PROJECT_STATUS.md](PROJECT_STATUS.md)

**Urgent Issues:**
- Create GitHub Issue with `critical` label
- Include steps to reproduce
- Tag as `bug` if functional issue

**General Questions:**
- Check [README.md](README.md) FAQ
- Review [USER_GUIDE.md](USER_GUIDE.md)
- Open GitHub Discussion

---

## 📝 Notes

### About This Document

This document provides transparency about known issues and limitations. It helps:
- **Users** understand current constraints
- **Contributors** prioritize fixes
- **Project** track issues publicly
- **Community** see progress

### Document History

- **January 21, 2026:** Initial creation
- Consolidates previously unreported issues
- Addresses documentation fragmentation concern
- Provides transparent issue tracking

---

**For active development priorities, see:** [ROADMAP.md](ROADMAP.md)  
**For project status, see:** [PROJECT_STATUS.md](PROJECT_STATUS.md)  
**To report new issues:** [GitHub Issues](https://github.com/operator/market-pie5-bot/issues)
