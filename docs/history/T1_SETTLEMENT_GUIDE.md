# T+1 Settlement Rules Guide

## Overview

This guide explains the T+1 settlement rules implementation in market-pie5-bot. Settlement rules are critical for cash accounts (non-margin accounts) to comply with SEC regulations and prevent Good Faith Violations.

## What is T+1 Settlement?

**T+1** refers to the settlement timeline for stock trades:
- **T** = Trade date (the day you execute the trade)
- **+1** = Settlement occurs 1 business day after the trade date

As of May 2024, U.S. stock markets transitioned from T+2 to T+1 settlement to improve efficiency and reduce risk.

## Why Settlement Rules Matter

### Cash Accounts vs. Margin Accounts

**Cash Accounts** (what this bot assumes):
- Cannot use unsettled funds for new purchases
- Must wait for funds to settle before reusing them
- Using unsettled funds results in **Good Faith Violations**
- 3 violations in 12 months = 90-day account freeze

**Margin Accounts**:
- Can use unsettled funds (borrowing from broker)
- Pay margin interest on borrowed funds
- Subject to Pattern Day Trading (PDT) rules if under $25,000

### Good Faith Violations

A **Good Faith Violation** occurs when you:
1. Buy a security with unsettled funds
2. Sell that security before the original purchase settles

**Example of a Violation:**
```
Monday:    Sell AAPL for $1,000 (proceeds unsettled)
Tuesday:   Buy TSLA with that $1,000 ❌ GOOD FAITH VIOLATION
Wednesday: AAPL sale settles (too late)
```

**Consequences:**
- 1st violation: Warning
- 2nd violation: Warning
- 3rd violation: Account restricted to settled funds only for 90 days

## How the Bot Implements Settlement Rules

### 1. Unsettled Funds Tracking

The bot maintains a list of unsettled funds with settlement dates:

```python
self.unsettled_funds = [
    {
        'amount': 1000.0,
        'settlement_date': datetime(2024, 1, 9),  # Tuesday
        'reason': 'BUY AAPL',
        'created_at': datetime(2024, 1, 8)  # Monday
    }
]
```

### 2. Settlement Date Calculation

Business days are calculated automatically, skipping weekends:

```python
def _calculate_business_days_ahead(days: int, from_date: datetime) -> datetime:
    # Adds 'days' business days to from_date
    # Automatically skips Saturday and Sunday
    # Returns the settlement date
```

**Examples:**
- Trade on Monday → Settles Tuesday (T+1)
- Trade on Friday → Settles Monday (skips weekend)
- Trade on Thursday → Settles Friday (T+1)

### 3. Capital Availability Check

Before each BUY trade, the bot checks if enough settled capital is available:

```python
def check_settled_capital_available(required_amount: float) -> Tuple[bool, str]:
    settled_capital = total_capital - unsettled_funds
    if settled_capital >= required_amount:
        return True, "Capital available"
    else:
        return False, "Insufficient settled capital"
```

### 4. Automatic Fund Locking

**On BUY:**
```python
# Lock the capital used to purchase
trade_value = quantity * price
self._add_unsettled_funds(trade_value, f'BUY {symbol}')
```

**On SELL:**
```python
# Lock the proceeds from the sale
sale_proceeds = quantity * exit_price
self._add_unsettled_funds(sale_proceeds, f'SELL {symbol}')
```

### 5. Automatic Fund Release

Settled funds are automatically released when settlement date passes:

```python
def _clean_settled_funds():
    # Remove funds where settlement_date < now
    # Called automatically before each capital calculation
```

## Trading Examples

### Example 1: Simple Buy-Wait-Buy

```
Starting Capital: $10,000
All funds are settled

Monday 9:00 AM:
  Action: Buy $3,000 of AAPL
  Settled Capital: $7,000
  Unsettled: $3,000 (settles Tuesday)

Monday 2:00 PM:
  Action: Try to buy $8,000 of TSLA
  Result: ❌ BLOCKED
  Reason: Only $7,000 settled capital available
  Need: $8,000

Tuesday 9:00 AM:
  Settled Capital: $10,000 (AAPL purchase settled)
  Unsettled: $0

Tuesday 10:00 AM:
  Action: Buy $8,000 of TSLA
  Result: ✓ SUCCESS
  Settled Capital: $2,000
  Unsettled: $8,000 (settles Wednesday)
```

### Example 2: Buy-Sell-Buy Pattern

```
Starting Capital: $10,000

Monday:
  Buy $5,000 of AAPL
  Settled: $5,000
  Unsettled: $5,000 (purchase, settles Tuesday)

Tuesday:
  AAPL purchase settles
  Sell AAPL for $5,500 (made $500 profit)
  Total Capital: $10,500
  Settled: $5,000
  Unsettled: $5,500 (sale proceeds, settle Wednesday)

Wednesday:
  Sale proceeds settle
  Settled: $10,500
  Can use all $10,500 for new trades
```

### Example 3: Multiple Overlapping Trades

```
Starting Capital: $10,000

Monday:
  Buy $2,000 AAPL
  Settled: $8,000
  Unsettled: $2,000

Monday (later):
  Buy $3,000 TSLA
  Settled: $5,000
  Unsettled: $5,000 ($2,000 + $3,000)

Tuesday:
  Monday's trades settle
  Sell AAPL for $2,200
  Settled: $7,800 (10,000 - 2,200)
  Unsettled: $2,200 (sale proceeds)

Wednesday:
  Tuesday's sale settles
  Settled: $10,000
  All funds available again
```

## Bot Messages and Logging

### Trade Blocked by Settlement

When a trade is blocked due to insufficient settled capital:

```
[T+1 SETTLEMENT CHECK FAILED - TRADE SKIPPED]
  Symbol: TSLA
  Insufficient settled capital. Required: $8000.00,
  Available (settled): $7000.00,
  Total capital: $10000.00,
  Unsettled: $3000.00 (T+1 settlement pending)
```

### Settlement Tracking Logs

The bot logs settlement events:

```
INFO: Added unsettled funds: $3000.00 (BUY AAPL) - settles on 2024-01-09
INFO: Released 1 settled fund(s)
DEBUG: Capital Status: Total=$10000.00, Unsettled=$3000.00, Available=$7000.00
```

## Testing Settlement Rules

The bot includes comprehensive tests in `test_t1_settlement.py`:

```bash
# Run settlement tests
python3 -m unittest test_t1_settlement -v

# Tests include:
# - Business day calculation
# - Capital locking on BUY
# - Proceeds locking on SELL
# - Multiple overlapping trades
# - Settlement date expiration
# - Insufficient capital handling
```

## Configuration

Settlement rules are **always enforced** in all trading modes:
- Paper Trading Mode
- Sandbox Mode
- Live Trading Mode

This ensures realistic simulation and prevents violations when moving to live trading.

**No configuration needed** - settlement tracking is automatic and built-in.

## Compliance and Best Practices

### For Paper Trading
- Practice with settlement rules to understand timing
- Test multi-day trading scenarios
- Verify capital availability before planning trades

### For Sandbox Mode
- Use sandbox to test real API with settlement rules
- Validate that your strategy works with settlement delays
- Ensure you don't rely on immediate fund availability

### For Live Trading
- **Critical**: Settlement rules prevent Good Faith Violations
- Plan trades considering T+1 settlement delays
- Monitor unsettled funds through logs
- Don't attempt to bypass settlement checks

## Technical Implementation

### Key Functions

**Settlement Tracking:**
```python
# Add unsettled funds
_add_unsettled_funds(amount, reason)

# Check available capital
get_settled_capital() -> float

# Validate trade
check_settled_capital_available(amount) -> (bool, str)

# Calculate settlement date
_calculate_business_days_ahead(days, from_date) -> datetime

# Clean up settled funds
_clean_settled_funds()
```

### Data Structure

```python
unsettled_funds = [
    {
        'amount': 1000.0,              # Dollar amount locked
        'settlement_date': datetime,    # When funds settle
        'reason': 'BUY AAPL',          # Why funds are locked
        'created_at': datetime          # When lock was created
    }
]
```

## Troubleshooting

### Trade Blocked - "Insufficient settled capital"

**Problem**: Trade is blocked even though total capital is sufficient

**Solution**: Wait for unsettled funds to settle (T+1)

**Check**: Review bot logs for unsettled fund details

### All Funds Locked

**Problem**: All capital is unsettled, can't trade

**Solution**:
1. Review when funds settle (check logs)
2. Wait for settlement date to pass
3. Ensure your trading strategy accounts for settlement delays

### Settlement Date Not Updating

**Problem**: Funds not settling on expected date

**Check**:
1. Verify system date/time is correct
2. Check if settlement date fell on weekend (auto-skipped to Monday)
3. Review logs for settlement cleanup events

## FAQ

**Q: Can I disable settlement rules for faster testing?**
A: No. Settlement rules are always enforced to prevent bad habits and ensure compliance.

**Q: What if I need to trade faster?**
A: Consider using smaller position sizes to keep more capital settled, or plan trades 1-2 days ahead.

**Q: Do settlement rules apply to all trading modes?**
A: Yes - Paper Trading, Sandbox, and Live Trading all enforce settlement rules.

**Q: What happens if I try to trade with unsettled funds?**
A: The trade is automatically blocked with a clear message explaining the issue.

**Q: How do I check my settled capital?**
A: Check the bot logs for "Capital Status" messages showing Total, Unsettled, and Available amounts.

**Q: Does this affect PDT rules?**
A: No. Settlement rules and PDT rules are separate. Both are enforced independently.

## References

- [SEC: Settlement Cycles](https://www.sec.gov/tm/settlement-cycles)
- [FINRA: Understanding Settlement](https://www.finra.org/
- [Good Faith Violations Explained](https://www.finra.org/

## Support

If you encounter issues with settlement tracking:

1. Check bot logs for settlement messages
2. Review test suite: `test_t1_settlement.py`
3. Verify your trading strategy accounts for T+1 delays
4. Report issues with detailed logs and reproduction steps

---

**Note**: This implementation follows SEC T+1 settlement rules as of 2024. Always consult with a financial advisor for specific questions about your trading account.
