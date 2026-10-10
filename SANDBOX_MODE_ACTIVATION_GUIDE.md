# Sandbox Mode Activation & Testing Guide

## Overview

Switch the bot from **yfinance simulation** to **Schwab Sandbox API** for more realistic testing with actual API calls.

---

## Prerequisites

1. ✅ Schwab account created (has OAuth token at `token.json`)
2. ✅ Schwab Sandbox API credentials configured
3. ✅ Bot currently running successfully in yfinance mode
4. ✅ Network access from operator to Schwab servers

---

## Step-by-Step: Activate Sandbox Mode

### Step 1: SSH to Bot Server
```bash
ssh operator@192.0.2.21
cd ~/market-bot/market-pie5-bot
```

### Step 2: Update Configuration
```bash
# Edit .env file
nano .env

# Change these lines:
# OLD:
PAPER_TRADING_MODE=true
SCHWAB_SANDBOX_MODE=false

# NEW:
PAPER_TRADING_MODE=false
SCHWAB_SANDBOX_MODE=true

# Save and exit (Ctrl+X, then Y, then Enter)
```

### Step 3: Verify OAuth Token
```bash
# Check that Schwab token exists
ls -la token.json

# Should output: -rw-r--r-- ... token.json (with a recent timestamp)
# If missing, run OAuth flow first:
# python schwab_auth.py
```

### Step 4: Stop Current Bot
```bash
# Kill any running bot processes
pkill -9 -f "python main.py"

# Verify it's stopped
pgrep -f "python main.py" && echo "Still running" || echo "Stopped"
```

### Step 5: Start Bot in Sandbox Mode
```bash
# Start bot with output to log file
nohup python main.py > /tmp/bot_output_sandbox.log 2>&1 &

# Verify it started
sleep 3
pgrep -f "python main.py" && echo "Bot started" || echo "Failed to start"

# Watch initial logs
tail -20 /tmp/bot_output_sandbox.log
```

### Step 6: Monitor Startup
```bash
# Watch logs as bot initializes (Ctrl+C to stop)
tail -f /tmp/bot_output_sandbox.log

# Look for:
# - "SCHWAB_SANDBOX_MODE=true"
# - "OAuth token loaded"
# - "Schwab API authenticated"
# - "Trading cycle #1 starting"
```

---

## Verify Sandbox Mode is Active

### Check Configuration
```bash
# Should show sandbox mode enabled
grep SCHWAB_SANDBOX ~/.env
# Output: SCHWAB_SANDBOX_MODE=true

# Should show paper trading disabled
grep PAPER_TRADING ~/.env
# Output: PAPER_TRADING_MODE=false
```

### Check API Usage
```bash
# Should see Schwab API calls in logs
grep -i "schwab\|api.*call" /tmp/bot_output_sandbox.log | head -10

# Should see real account data
grep -i "account.*balance\|position" /tmp/bot_output_sandbox.log | head -5
```

### Check Bot Status
```bash
# From local machine:
curl http://192.0.2.21:8004/api/bot/status | json_pp

# Should show mode as "sandbox" or "schwab_api"
```

---

## Run Sandbox Mode Tests

### From Local Machine (Windows)

#### 1. Set Environment Variables (Optional)
```bash
# Windows PowerShell - if needed to specify API endpoint
$env:BOT_API_URL = "http://192.0.2.21:8004"
```

#### 2. Run the Sandbox Test Suite
```bash
python test_sandbox_mode_comprehensive.py
```

#### Expected Output
```
================================================================================
SCHWAB SANDBOX MODE TESTING SUITE
Time: 2026-02-01 20:30:00
================================================================================

[20:30:00] TEST: Running: Sandbox Mode Configured
[20:30:00] ✓: PASS: Sandbox Mode Configured
[20:30:00] TEST: Running: Schwab API Credentials
[20:30:00] ✓: PASS: Schwab API Credentials
...
[20:30:15] TEST: Running: Continuous Operation
[20:30:15] ✓: PASS: Continuous Operation

================================================================================
SANDBOX MODE TEST SUMMARY
================================================================================
Passed: 10
Failed: 0
Total:  10

Detailed Results:
✓ PASS  - Sandbox Mode Configured
✓ PASS  - Schwab API Credentials
✓ PASS  - API Responds
✓ PASS  - Schwab API Connected
✓ PASS  - Trades Execute
✓ PASS  - Paper Money Mode
✓ PASS  - Order Confirmations
✓ PASS  - No Unhandled Exceptions
✓ PASS  - No Rate Limit Issues
✓ PASS  - Continuous Operation

================================================================================
```

---

## What Gets Tested in Sandbox Mode

### Configuration Verification
- ✅ SCHWAB_SANDBOX_MODE enabled
- ✅ OAuth token exists and valid
- ✅ Schwab API credentials configured

### API Connectivity
- ✅ Schwab API responds to requests
- ✅ Bot connects to Schwab endpoints
- ✅ Real-time data flowing

### Trading Operations
- ✅ Orders placed through Schwab API
- ✅ Trades execute and confirm
- ✅ Paper money (no real risk)
- ✅ Account balance tracking

### System Stability
- ✅ No crashes with API calls
- ✅ Error handling for API failures
- ✅ Continuous operation
- ✅ No rate limiting issues

---

## Sandbox Mode Advantages

### vs. Yfinance Mode
- ✅ Real API calls (like production)
- ✅ Real market data from Schwab
- ✅ Realistic order execution
- ✅ Actual account balance sync
- ✅ Better performance validation
- ✅ API error handling testing

### vs. Production Mode
- ✅ No real money at risk
- ✅ Can test freely
- ✅ No PDT restrictions
- ✅ Unlimited trading
- ✅ Can restart anytime
- ✅ Lower commitment

---

## Troubleshooting Sandbox Mode

### Bot Won't Start
```bash
# Check for errors in logs
tail -50 /tmp/bot_output_sandbox.log

# Common issues:
# 1. OAuth token expired - regenerate with: python schwab_auth.py
# 2. Schwab API down - check status.schwab.com
# 3. Network issue - verify connectivity: ping api.schwab.com
```

### API Authentication Fails
```bash
# Refresh OAuth token
python schwab_auth.py

# Restart bot
pkill -f "python main.py"
sleep 2
nohup python main.py > /tmp/bot_output_sandbox.log 2>&1 &
```

### No Trades Executing
```bash
# Check if strategies are generating signals
grep -i "signal\|BUY\|SELL" /tmp/bot_output_sandbox.log | head -10

# Check if bot is running continuously
grep "Trading Cycle" /tmp/bot_output_sandbox.log | tail -5

# Check for API errors
grep -i "error\|failed" /tmp/bot_output_sandbox.log | head -10
```

### Rate Limiting Errors
```bash
# Check API rate limits
grep -i "rate" /tmp/bot_output_sandbox.log

# Solution: Increase delay between API calls in config
# Reduce number of symbols to trade
# Spread trades across longer timeframe
```

---

## Monitoring Sandbox Trades

### View Live Trades
```bash
# Real-time log following
ssh operator "tail -f /tmp/bot_output_sandbox.log"

# Look for patterns like:
# "Processing trade for AAPL (BUY)"
# "Order filled via Schwab"
# "P&L: $XX.XX"
```

### Check Trade Statistics
```bash
# Count trades executed
ssh operator "grep 'Processing trade' /tmp/bot_output_sandbox.log | wc -l"

# Count winning trades
ssh operator "grep '✓ WIN' /tmp/bot_output_sandbox.log | wc -l"

# Count losing trades
ssh operator "grep '✗ LOSS' /tmp/bot_output_sandbox.log | wc -l"

# View current account balance
ssh operator "grep 'account.*balance\|cash.*available' /tmp/bot_output_sandbox.log | tail -1"
```

---

## Comparing Modes

### Before and After Metrics

```
Metric                  Yfinance Mode    Sandbox Mode
────────────────────────────────────────────────────
Data Source             yfinance API     Schwab API
API Calls               None             Frequent
Trade Confirmation      Simulated        Real
Account Balance         Simulated        Real from Schwab
Execution Speed         Fast             Slower (API)
Error Realism           Low              High
Real-World Readiness    Moderate         High
Risk Level              None             None (paper)
Effort Required         Low              Medium
Cost                    Free             Free (paper)
```

---

## Next Steps

### After Successful Sandbox Testing
1. ✅ Run test suite and verify all pass
2. ✅ Monitor bot for 24 hours
3. ✅ Verify trade execution consistency
4. ✅ Check account balance tracking
5. ✅ Document any API quirks
6. ✅ Document performance metrics
7. ✅ Create production readiness report

### Preparation for Production (Future)
1. ⚠️ Complete sandbox 24-hour test
2. ⚠️ Review all PDT rules
3. ⚠️ Set capital preservation limits
4. ⚠️ Set position size limits
5. ⚠️ Get explicit user approval
6. ⚠️ Prepare failover procedures

---

## Quick Commands Reference

### Switch to Sandbox
```bash
ssh operator << 'EOF'
cd ~/market-bot/market-pie5-bot
sed -i 's/PAPER_TRADING_MODE=true/PAPER_TRADING_MODE=false/' .env
sed -i 's/SCHWAB_SANDBOX_MODE=false/SCHWAB_SANDBOX_MODE=true/' .env
pkill -f "python main.py"
sleep 2
nohup python main.py > /tmp/bot_output_sandbox.log 2>&1 &
sleep 3
pgrep -f "python main.py" && echo "Sandbox mode active" || echo "Failed"
EOF
```

### Switch Back to Yfinance
```bash
ssh operator << 'EOF'
cd ~/market-bot/market-pie5-bot
sed -i 's/PAPER_TRADING_MODE=false/PAPER_TRADING_MODE=true/' .env
sed -i 's/SCHWAB_SANDBOX_MODE=true/SCHWAB_SANDBOX_MODE=false/' .env
pkill -f "python main.py"
sleep 2
nohup python main.py > /tmp/bot_output.log 2>&1 &
sleep 3
pgrep -f "python main.py" && echo "Yfinance mode active" || echo "Failed"
EOF
```

### Run Sandbox Tests
```bash
python test_sandbox_mode_comprehensive.py
```

### Monitor Sandbox Logs
```bash
ssh operator "tail -f /tmp/bot_output_sandbox.log"
```

---

## Safety Checklist

Before switching to sandbox mode, ensure:

- [ ] Yfinance mode tests are all passing
- [ ] Bot stable for 30+ minutes in current mode
- [ ] OAuth token exists and recent
- [ ] Schwab account has paper money
- [ ] Network connectivity verified
- [ ] Bot logs accessible
- [ ] Backup of current configuration
- [ ] Rollback procedure understood

---

## Summary

**Ready to test Schwab Sandbox API integration?**

1. Run: `ssh operator` and follow "Step-by-Step" section above
2. Wait 2 minutes for bot to initialize
3. Run: `python test_sandbox_mode_comprehensive.py` from local machine
4. Monitor logs: `ssh operator "tail -f /tmp/bot_output_sandbox.log"`

Expected result: 10/10 tests passing in ~20 seconds

---

*Last Updated: February 1, 2026*  
*Difficulty Level: Medium*  
*Estimated Time: 15 minutes setup + 10 minutes testing*
