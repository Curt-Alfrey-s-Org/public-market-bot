# Data Privacy and Third-Party Service Statement

## Overview

The market-pie5-bot is designed to ensure your trading data remains private and under your control. This document explains what services the bot uses and how your data is handled.

## Third-Party Services Used

### 1. Schwab API (Required for Live/Sandbox Trading)
- **Purpose**: Execute trades and fetch market data
- **What data is sent**: Trading orders, account queries, market data requests
- **When**: Only when using live trading mode or sandbox mode
- **Library**: `schwab-py` (official Schwab API client)
- **Your control**: You provide API credentials; all data goes directly to Schwab's API
- **Privacy**: Your data goes directly to Schwab, a regulated financial institution

### 2. Yahoo Finance (Optional, Fallback Only)
- **Purpose**: Fetch stock prices when Schwab API is unavailable
- **What data is sent**: Stock symbol queries
- **When**: Only in simulation mode when Schwab API fails, or as fallback in live mode
- **Library**: `yfinance` (public market data API)
- **Your control**: No authentication required; public market data only
- **Privacy**: Only symbol names are queried; no personal or trading data

### 3. HuggingFace AI API (Optional)
- **Purpose**: AI-powered trading strategy analysis
- **What data is sent**: Trading statistics (win rate, allocation, P&L percentages)
- **When**: Only when you explicitly call AI analysis features
- **Library**: Direct HTTPS requests to HuggingFace API
- **Your control**: You provide API key; feature is optional
- **Privacy**: No personal identifiers; only aggregated performance metrics

## Services NOT Used

### ❌ Lumibot
**The bot does NOT use Lumibot or send any data to Lumibot services.**

- Lumibot was previously listed as a dependency but has been **completely removed**
- All Schwab API integration is done directly using `schwab-py`
- No data is routed through Lumibot's infrastructure
- No Lumibot APIs are called

### How We Ensure This
1. ✅ Lumibot removed from `requirements.txt`
2. ✅ No `import lumibot` statements in code
3. ✅ No calls to Lumibot APIs
4. ✅ Direct use of `schwab-py` for all Schwab interactions
5. ✅ All code is open source and auditable

## Data Storage

### Local Storage Only
All trading data is stored **locally on your machine**:

- **Trade history**: Stored in memory and optionally in local JSON files
- **OAuth tokens**: Stored in `token.json` (never transmitted to third parties)
- **Logs**: Written to local files (`trading_bot.log`, `alerts.log`)
- **Database**: SQLite database stored locally (`trading_logs.db`)

### No Remote Storage
- No data is uploaded to cloud services (except to APIs listed above)
- No telemetry or analytics collected
- No usage tracking

## Your Control

You have complete control over your data:

1. **API Credentials**: You provide and manage all API keys
2. **Local Execution**: Bot runs on your hardware
3. **Open Source**: All code is visible and auditable
4. **Optional Features**: AI analysis is opt-in only
5. **Data Deletion**: Simply delete local files to remove all data

## Simulation Mode

When using pure simulation mode (no API credentials configured):
- **No external API calls** are made
- Random price data is generated locally
- No network connectivity required
- No data leaves your machine

## Verification

To verify the bot doesn't use Lumibot:

```bash
# Search for any lumibot imports in the codebase
grep -r 'import.*lumibot' --include="*.py" .
grep -r 'from.*lumibot' --include="*.py" .
# (Should return no results)

# Check requirements.txt
grep -i lumibot requirements.txt
# (Should return no results)
```

## Questions or Concerns?

If you have questions about data privacy or third-party services:

1. Review the source code (it's fully open source)
2. Check network traffic using tools like Wireshark
3. Run in simulation mode for completely offline operation
4. Open an issue on GitHub for clarification

## Summary

✅ **Direct Schwab Integration**: Uses `schwab-py` directly, not Lumibot  
✅ **Local Data Storage**: All data stays on your machine  
✅ **Transparent APIs**: Only calls to Schwab, Yahoo Finance (optional), and HuggingFace (optional)  
✅ **No Lumibot**: Completely removed from the project  
✅ **Open Source**: All code is auditable  
✅ **Your Control**: You manage all credentials and data  

**Your trading data remains private and under your complete control.**
