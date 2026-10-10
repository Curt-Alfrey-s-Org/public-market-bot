# Market Pie5 Bot - User Guide

## Quick Start for Beginners

### First Time Setup on Raspberry Pi 5

1. **Install the bot** using the installation script:
   ```bash
   ./install.sh
   ```

2. **Configure your settings**:
   ```bash
   cd market-pie5-bot
   cp .env.example .env
   nano .env
   ```
   
   Fill in at minimum:
   - `SCHWAB_API_KEY` (if using live trading)
   - `SCHWAB_APP_SECRET` (if using live trading)
   - `HUGGINGFACE_API_KEY` (optional, for AI features)

3. **Launch the bot**:
   ```bash
   ./start_bot.sh
   ```

4. **Select GUI mode** (option 1) for the easiest experience

## Understanding the GUI

### Control Tab
- **Status Indicator**: Shows if bot is running (green) or stopped (red)
- **PDT Status**: Shows day trade count and compliance status
- **Start/Stop Buttons**: Control the trading bot
- **Quick Stats**: View key metrics at a glance
  - Total trades executed
  - Win rate percentage
  - Current allocation amount
  - Total capital

### Settings Tab
Configure all bot parameters without editing code:

**Bot Settings:**
- **Total Capital**: Your starting capital ($500 for small accounts)
- **Min Allocation**: Minimum amount per trade ($50 default)
- **Max Allocation**: Maximum amount per trade ($500 default)
- **Trailing Stop %**: Automatic stop loss percentage (5% default)

**Risk Settings:**
- **Risk Threshold %**: Max risk per trade as % of capital
- **Max Positions**: Maximum number of simultaneous open positions

**PDT Compliance:**
- **Enable PDT Protection**: Automatically prevent PDT violations
  - Enabled by default based on `ENABLE_PDT_RULES` in `.env`
  - Can be toggled in the GUI for individual sessions
  - For paper trading: disable to run unlimited trades for larger sample sizes
  - For live trading: PDT is always enforced regardless of setting
- **Capital Floor %**: Pause trading if capital drops below this % (10% default)

**Alerts:**
- **Enable Alerts**: Turn on/off alert notifications
- **Alert Email**: Email address for notifications (optional)

**Important**: Click "Apply Settings" to save changes!

### Logs Tab
- Real-time log viewer showing all bot activity
- Timestamps for each event
- Color-coded status messages
- Clear button to reset logs
- Auto-scroll to latest entries

### Resources Tab
Monitor your Raspberry Pi 5 system resources:

- **CPU Usage**: Current processor utilization
- **Memory Usage**: RAM utilization percentage
- **Disk Usage**: Storage space used
- **Network Activity**: Upload/download speeds
- **Bottleneck Warnings**: Automatic alerts when resources are constrained

**Why this matters**: High resource usage can slow down the bot and affect trade execution timing.

### Statistics Tab
Detailed performance metrics:
- Complete trade history analysis
- Win/loss breakdown
- Current position information
- PDT day trade tracking
- Capital tracking over time

## Trading Strategies for Small Accounts

### Starting with $500

With only $500 capital, you must be strategic:

#### 1. Avoid Pattern Day Trading (PDT) Violations
- **Rule**: Max 3 day trades per 5 business days
- **Day Trade**: Buying AND selling the same stock on the same day
- **Violation**: Can freeze your account for 90 days
- **Solution**: Focus on swing trades (hold overnight)

#### 2. Make Consistent Small Gains
- Target: $5-10 per day minimum
- This covers:
  - Trading fees (~$0.50-5 per trade)
  - Provides small profit margin
  - Compounds over time
- Avoid trying to "hit it big" on one trade

#### 3. Use Proper Position Sizing
With $500 capital:
- **Max per trade**: $50-100 (10-20% of capital)
- **Max positions**: 3-4 stocks at once
- **Why**: Diversification protects against single stock loss

#### 4. Protect Your Capital
- **Capital floor**: Bot pauses if capital drops below $50 (10%)
- **Trailing stops**: Protect profits automatically
- **Risk management**: Never risk more than 5% per trade

### Example Trading Day

**Morning (9:30 AM - 11:00 AM)**
1. Bot loads symbol scan list
2. Checks PDT status (2/3 day trades used)
3. Identifies entry opportunity on AAPL at $150
4. Buys $75 worth (0.5 shares)
5. Sets 5% trailing stop at $142.50

**Afternoon (2:00 PM)**
1. AAPL rises to $153
2. Trailing stop adjusts to $145.35 (5% below $153)
3. AAPL dips to $145
4. Trailing stop triggered, position closed
5. Profit: $3 (2% gain)

**End of Day**
1. Did NOT sell same day = NOT a day trade
2. Still have 1 day trade left for emergencies
3. Capital: $503 (covered fees and made $2 profit)

## Safety Features

### 1. Capital Floor Protection
- **Default**: 10% of starting capital
- **Action**: Bot automatically pauses trading
- **Resume**: Bot resumes when capital recovers to 120% of floor
- **Purpose**: Prevents complete account wipeout

### 2. PDT Compliance Checker
- **Tracks**: All same-day buy/sell transactions
- **Warns**: When approaching 3-trade limit
- **Blocks**: 4th day trade to prevent violation
- **Resets**: After 5 business days

### 3. Position Limits
- **Default**: Max 5 simultaneous positions
- **Purpose**: Prevents over-concentration
- **Benefit**: Allows monitoring and management

### 4. Stock Filtering
Before entering any trade, bot checks:
- **Price**: Must be > $5 (no penny stocks)
- **Volume**: Must have > 500k daily volume (liquidity)
- **Volatility**: Must be < 15% (manageable risk)

### 5. Dynamic Trailing Stops
- **Adapts**: Stop percentage based on stock volatility
- **Low volatility**: Tighter stops (2-3%)
- **High volatility**: Looser stops (8-10%)
- **Benefit**: Optimizes risk vs. reward

## Troubleshooting

### Bot Won't Start
1. Check .env file is configured
2. Verify virtual environment: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Check Python version: `python3 --version` (needs 3.8+)

### "PDT Limit Reached" Message
- **Cause**: You've made 3 day trades in 5 business days
- **Solution**: Wait for oldest day trade to age off (5 business days)
- **Alternative**: Focus on swing trades (hold overnight)
- **Long-term**: Build capital to $25k to remove limit

### "Capital Floor Breach" Message
- **Cause**: Capital dropped below 10% of starting amount
- **Action**: Bot automatically paused trading
- **Review**: Check what went wrong (too risky? bad strategy?)
- **Fix**: Adjust settings (lower allocation, tighter stops)
- **Resume**: Add capital or wait for recovery trades

### High Resource Usage Warning
- **Cause**: Pi5 CPU, RAM, or disk is constrained
- **Impact**: May slow down bot, affect timing
- **Solutions**:
  - Close other programs
  - Restart Pi5
  - Check for background processes
  - Free up disk space

### "No Symbols Loaded" Warning
- **Cause**: scan_symbols.txt missing or empty
- **Solution**: Create file with one symbol per line:
  ```
  AAPL
  MSFT
  GOOGL
  ```

## Best Practices

### Daily Routine
1. **Morning**: 
   - Review overnight market news
   - Check bot settings
   - Verify PDT status
   - Start bot before market open (9:30 AM ET)

2. **During Market Hours**:
   - Monitor bot logs periodically
   - Check resource usage
   - Review positions in Statistics tab

3. **End of Day**:
   - Review trade performance
   - Check win rate
   - Adjust settings if needed
   - Stop bot after market close (4:00 PM ET)

### Weekly Review
- Analyze win rate trend
- Calculate actual profit (including fees)
- Adjust strategy if consistently losing
- Review AI suggestions

### Monthly Goals
- Track capital growth
- Calculate return on investment (ROI)
- Refine symbol scan list
- Update bot settings based on performance

## Advanced Features

### AI Integration
The bot can send performance data to AI for analysis:

1. **Automatic**: Bot sends data after each trading session
2. **Analysis**: AI reviews win rate, allocation, trade count
3. **Suggestions**: AI recommends settings adjustments
4. **Review**: Check suggestions in logs
5. **Apply**: Manually adjust settings or enable auto-tweak

**Note**: Requires HUGGINGFACE_API_KEY in .env

### Dynamic Symbol Scanning
Load symbols from an API instead of static file:

1. Set up API endpoint that returns JSON symbol list
2. Configure `DYNAMIC_SCAN_API_URL` in .env
3. Bot fetches fresh symbols before each session
4. Falls back to file if API unavailable

**Use case**: Get symbols from a penny stock scanner service

### Email Alerts
Get notified of important events:

1. Configure `ALERT_EMAIL` in .env
2. Set up SMTP server (requires code modification)
3. Receive emails for:
   - Capital floor breaches
   - Large P&L changes
   - PDT warnings
   - Bot errors

## Support and Community

### Getting Help
1. Check this user guide
2. Review README.md for technical details
3. Check logs in Logs tab for error messages
4. Review alerts.log file for alert history

### Reporting Issues
When reporting problems, include:
- Bot version
- Error message from logs
- Steps to reproduce
- System info (Pi5 model, OS version)

### Contributing
The bot is open source! Contributions welcome:
- Bug fixes
- New features
- Documentation improvements
- Testing

## Legal and Compliance

### Disclaimer
- This bot is for educational and personal use
- No guarantees of profit
- Trading involves risk of loss
- You are responsible for your trading decisions
- Past performance does not guarantee future results

### Regulations
- **PDT Rule**: SEC regulation for accounts < $25k
- **Pattern Day Trader**: 4+ day trades in 5 business days
- **Day Trade**: Buy and sell same security same day
- **Margin**: Bot designed for cash accounts (no margin)

### Taxes
- Keep records of all trades
- Report capital gains/losses
- Consult tax professional
- Bot logs help with record keeping

## Appendix: Configuration Reference

### Environment Variables (.env)

```bash
# Required for live trading
SCHWAB_API_KEY=your_app_key
SCHWAB_APP_SECRET=your_app_secret
SCHWAB_ACCOUNT_ID=your_account_number

# Optional - AI features
HUGGINGFACE_API_KEY=your_hf_token

# Bot configuration
BOT_RISK_THRESHOLD=0.05          # 5% max risk per trade
BOT_MIN_ALLOCATION=50            # $50 minimum per trade
BOT_MAX_ALLOCATION=500           # $500 maximum per trade
BOT_TRAILING_STOP_PERCENT=0.05   # 5% trailing stop

# Capital protection
CAPITAL_FLOOR_PERCENT=0.10       # 10% floor (pause threshold)

# Position management
MAX_SIMULTANEOUS_POSITIONS=5     # Max 5 open positions
PARTIAL_EXIT_ENABLED=True        # Allow partial exits
PARTIAL_EXIT_PERCENTAGE=0.5      # Exit 50% on stop

# Stock filtering
MIN_STOCK_PRICE=5.0              # Avoid penny stocks
MIN_DAILY_VOLUME=500000          # Minimum liquidity
MAX_STOCK_VOLATILITY=0.15        # Max 15% volatility

# Alerts
ENABLE_ALERTS=True
ALERT_EMAIL=operator@example.com

# Dynamic scanning (optional)
DYNAMIC_SCAN_API_URL=https://api.example.com/symbols
```

### Default Symbols (scan_symbols.txt)
```
AAPL
MSFT
GOOGL
TSLA
NVDA
```

### Recommended Settings for Different Capital Levels

**$500 Account** (Starting):
- Min Allocation: $50 (10%)
- Max Allocation: $100 (20%)
- Max Positions: 3
- Risk Threshold: 5%
- Trailing Stop: 4%

**$1000 Account**:
- Min Allocation: $75 (7.5%)
- Max Allocation: $150 (15%)
- Max Positions: 4
- Risk Threshold: 5%
- Trailing Stop: 5%

**$5000 Account**:
- Min Allocation: $100 (2%)
- Max Allocation: $500 (10%)
- Max Positions: 5
- Risk Threshold: 5%
- Trailing Stop: 5%

**$25,000+ Account** (No PDT restrictions):
- Min Allocation: $500 (2%)
- Max Allocation: $2500 (10%)
- Max Positions: 10
- Risk Threshold: 5%
- Trailing Stop: 6%

---

**Good luck with your trading! Remember: Consistency and discipline are key to success.**
