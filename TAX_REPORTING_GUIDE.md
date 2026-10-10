# Tax Reporting Guide for market-pie5-bot

## Overview

The market-pie5-bot now includes comprehensive tax reporting functionality to help you document all trades for tax filing purposes. The system generates IRS Form 8949 compatible reports, detects wash sales, and provides detailed summaries suitable for CPA review.

## Features

### 1. IRS Form 8949 CSV Export
- **Part I**: Short-term capital gains/losses (assets held ≤365 days)
- **Part II**: Long-term capital gains/losses (assets held >365 days)
- **Columns match IRS Form 8949 format**:
  - Description of property
  - Date acquired
  - Date sold
  - Proceeds (sales price)
  - Cost basis
  - Adjustment codes (W for wash sales)
  - Gain or loss
- **Schedule D totals** for easy tax return preparation

### 2. Wash Sale Detection
- Automatically detects potential wash sales per IRS 30-day rule
- Identifies when a security is repurchased within 30 days before or after a loss sale
- Flags affected trades in all reports
- Provides repurchase dates and timing details

### 3. Comprehensive Tax Summary (JSON)
- Machine-readable format for further analysis
- Detailed trade-by-trade breakdown
- Summary statistics by holding period
- Wash sale tracking
- Total capital gains/losses

### 4. CPA Review Report (Text)
- Human-readable format for professional review
- Executive summary with key statistics
- Detailed trade listings with all relevant data
- Wash sale section with explanations
- Disclaimers and verification notes

## Usage

### Quick Start

Generate all tax reports for the current year:

```bash
python3 tax_report_generator.py
```

Generate reports for a specific tax year:

```bash
python3 tax_report_generator.py 2024
```

### From Python Code

```python
from tax_report_generator import TaxReportGenerator

# Initialize the generator
generator = TaxReportGenerator(db_path="logs/trading_logs.db")

# Generate all reports for tax year 2024
reports = generator.generate_all_reports(2024)

# Or generate individual reports
form_8949_csv = generator.generate_form_8949_csv(2024)
tax_summary = generator.generate_tax_summary_json(2024)
cpa_report = generator.generate_cpa_report(2024)
```

### Integration with Trading Bot

The tax reporting system automatically uses the existing LogManager database. All trades executed through the bot are automatically available for tax reporting.

```python
from main import TradingBot
from log_manager import LogManager
from tax_report_generator import TaxReportGenerator

# Run your trading bot
bot = TradingBot(total_capital=10000.0)
# ... execute trades ...

# Save trade history
bot.save_trade_history()

# Generate tax reports
generator = TaxReportGenerator()
reports = generator.generate_all_reports(2024)
```

## Generated Files

When you run the tax report generator, three files are created:

### 1. `form_8949_tax_year_YYYY.csv`
IRS Form 8949 compatible CSV file that can be:
- Imported into tax preparation software
- Reviewed by your CPA
- Used to fill out Form 8949 manually

### 2. `tax_summary_YYYY.json`
Comprehensive JSON file containing:
- All trade details
- Summary statistics
- Wash sale information
- Notes and disclaimers

### 3. `cpa_report_YYYY.txt`
Human-readable text report with:
- Executive summary
- Trade-by-trade details
- Wash sale analysis
- Professional notes for CPA

## Understanding the Reports

### Holding Period Classification

**Short-Term Capital Gains/Losses**:
- Assets held for 365 days or less
- Taxed as ordinary income
- Reported in Part I of Form 8949

**Long-Term Capital Gains/Losses**:
- Assets held for more than 365 days
- Eligible for preferential tax rates (0%, 15%, or 20%)
- Reported in Part II of Form 8949

### Wash Sale Rules

The IRS wash sale rule disallows claiming a loss if you:
1. Sell a security at a loss
2. Purchase the same or substantially identical security within 30 days before or after the sale

**How the bot handles wash sales**:
- Automatically detects potential wash sales
- Flags affected trades with "W" adjustment code
- Provides details on repurchase timing
- Notes that loss deduction may be disallowed

**Example from report**:
```
Symbol: TSLA
  Sale Date: 2024-11-10
  Loss: $-150.00
  Repurchase Date: 2024-11-25
  Days Difference: 15
```

### Cost Basis Calculation

Cost basis for each trade includes:
- Entry price × Quantity
- Any commissions/fees (if captured in logs)

Proceeds calculation:
- Exit price × Quantity

Gain/Loss = Proceeds - Cost Basis

## Tax Filing Workflow

### Step 1: Generate Reports
```bash
python3 tax_report_generator.py 2024
```

### Step 2: Verify Accuracy
1. Compare generated reports with broker statements (Form 1099-B)
2. Verify all trades are included
3. Check cost basis calculations
4. Review wash sale detections

### Step 3: Provide to CPA
Give your CPA all three files:
- Form 8949 CSV for data import
- Tax summary JSON for detailed review
- CPA report for professional analysis

### Step 4: File with Tax Return
- Form 8949 must be filed with your tax return
- Attach to Schedule D
- Keep copies for your records (7 years recommended)

## Important Notes and Disclaimers

### ⚠️ Professional Tax Advice Required
This tool generates reports for informational purposes only. It does NOT:
- Constitute tax advice
- Replace professional CPA review
- Guarantee accuracy for tax filing

**Always consult with a qualified tax professional before filing.**

### ⚠️ Verify Against Broker Statements
- Compare bot-generated reports with official Form 1099-B from your broker
- Discrepancies may occur due to:
  - Corporate actions (splits, mergers)
  - Broker cost basis adjustments
  - Timing differences
  - Commission/fee handling

### ⚠️ Wash Sale Disclaimer
Wash sale detection is automated but may not catch all cases:
- "Substantially identical" securities determination requires professional judgment
- Options and futures may trigger wash sales
- Multiple brokerage accounts are not cross-checked
- Review all flagged trades with your CPA

### ⚠️ Paper Trading vs Live Trading
The reports distinguish between:
- **Live trading**: Real money trades (use for tax filing)
- **Paper trading**: Simulated trades (NOT for tax filing)
- **Sandbox mode**: Test environment trades (NOT for tax filing)

Only use reports from **live trading mode** for actual tax filing.

## Data Fields in Trade Logs

Each trade record includes:

| Field | Description | Tax Relevance |
|-------|-------------|---------------|
| symbol | Stock ticker | Identifies security |
| action | BUY or SELL | Determines completed trades |
| timestamp | Date/time of trade | Acquisition/sale dates |
| quantity | Number of shares | Calculates basis/proceeds |
| entry_price | Purchase price per share | Cost basis calculation |
| exit_price | Sale price per share | Proceeds calculation |
| pnl | Profit/loss in dollars | Gain/loss amount |
| pnl_percent | P&L percentage | Performance metric |
| is_win | Win/loss flag | Trade classification |
| exit_reason | Why position closed | Trading context |
| mode | Trading mode | Live vs paper distinction |

## Examples

### Example 1: Generate Reports for 2024

```bash
$ python3 tax_report_generator.py 2024

Tax Report Generator
================================================================================
Generating tax reports for year 2024...

Generating all tax reports for tax year 2024...
================================================================================

✓ Generated IRS Form 8949 CSV: form_8949_tax_year_2024.csv
  Short-term trades: 15
  Long-term trades: 3
  Total capital gain/loss: $2,450.00

✓ Generated tax summary JSON: tax_summary_2024.json

✓ Generated CPA report: cpa_report_2024.txt

✓ All tax reports generated successfully!

Generated files:
  - form_8949_tax_year_2024.csv
  - tax_summary_2024.json
  - cpa_report_2024.txt

================================================================================
Tax report generation complete!

Next steps:
1. Review all generated files for accuracy
2. Compare with brokerage statements (Form 1099-B)
3. Provide files to your CPA for tax preparation
4. Keep copies for your records (7 years recommended)
```

### Example 2: Review CPA Report

The CPA report provides a comprehensive summary:

```
================================================================================
TRADING TAX REPORT FOR CPA REVIEW
================================================================================
Tax Year: 2024
Generated: 2026-01-23 15:30:00

EXECUTIVE SUMMARY
--------------------------------------------------------------------------------
Total Completed Trades: 18
Short-Term Trades (≤365 days): 15
Long-Term Trades (>365 days): 3
Potential Wash Sales Detected: 2

Short-Term Capital Gain/(Loss): $1,800.00
Long-Term Capital Gain/(Loss): $650.00
Net Capital Gain/(Loss): $2,450.00

SHORT-TERM CAPITAL GAINS AND LOSSES (≤365 days)
--------------------------------------------------------------------------------
Symbol     Qty      Acquired     Sold         Cost Basis      Proceeds        Gain/Loss       Wash Sale
--------------------------------------------------------------------------------
AAPL       10.00    2024-01-15   2024-03-20   $1,500.00       $1,650.00       $150.00         NO
MSFT       5.00     2024-02-10   2024-04-15   $1,900.00       $1,950.00       $50.00          NO
...
```

### Example 3: Programmatic Access

```python
from tax_report_generator import TaxReportGenerator
import json

# Initialize generator
generator = TaxReportGenerator(db_path="logs/trading_logs.db")

# Get trades for analysis
trades = generator.get_trades_for_tax_year(2024)
print(f"Total trades: {len(trades)}")

# Check for wash sales
trades_with_wash = generator.detect_wash_sales(trades)
wash_sales = [t for t in trades_with_wash if t.get('wash_sale', False)]
print(f"Wash sales detected: {len(wash_sales)}")

# Generate summary
generator.generate_tax_summary_json(2024, "my_summary.json")

# Load and analyze
with open("my_summary.json", 'r') as f:
    summary = json.load(f)
    print(f"Net gain/loss: ${summary['summary']['net_capital_gain_loss']:.2f}")
```

## Troubleshooting

### No trades found
**Problem**: "No trades found" error
**Solution**: 
- Ensure you've executed trades using the bot
- Check that the database exists: `logs/trading_logs.db`
- Verify the correct tax year

### Holding period seems wrong
**Problem**: Trades classified incorrectly as short/long-term
**Solution**:
- The system uses trade timestamps from logs
- For accurate holding period, ensure entry_price timestamps are correct
- Contact CPA if discrepancies persist

### Wash sale not detected
**Problem**: Expected wash sale not flagged
**Solution**:
- Wash sale detection only checks trades within the bot's database
- Manual verification recommended for multi-broker scenarios
- Check 30-day window includes both BUY and SELL trades

### Database not found
**Problem**: `FileNotFoundError: Trading logs database not found`
**Solution**:
```bash
# Check if database exists
ls -la logs/trading_logs.db

# If missing, run the bot first to generate logs
python3 main.py
```

## API Reference

### TaxReportGenerator Class

```python
class TaxReportGenerator:
    def __init__(self, db_path: str = "logs/trading_logs.db")
    
    def get_trades_for_tax_year(self, tax_year: int) -> List[Dict]
    def classify_holding_period(self, acquisition_date: str, sale_date: str) -> str
    def detect_wash_sales(self, trades: List[Dict]) -> List[Dict]
    def generate_form_8949_csv(self, tax_year: int, output_file: str = None) -> str
    def generate_tax_summary_json(self, tax_year: int, output_file: str = None) -> str
    def generate_cpa_report(self, tax_year: int, output_file: str = None) -> str
    def generate_all_reports(self, tax_year: int) -> Dict[str, str]
```

## Testing

Run the test suite to verify tax reporting functionality:

```bash
python3 test_tax_reporting.py -v
```

Tests cover:
- Trade retrieval by tax year
- Holding period classification
- Wash sale detection
- Form 8949 CSV generation
- Tax summary JSON generation
- CPA report generation
- Multi-year scenarios
- Empty database handling

## Additional Resources

### IRS Resources
- [IRS Form 8949 Instructions](https://www.irs.gov/forms-pubs/about-form-8949)
- [Schedule D Instructions](https://www.irs.gov/
- [Publication 550 - Investment Income and Expenses](https://www.irs.gov/publications/p550)

### Understanding Capital Gains Tax
- Short-term gains taxed as ordinary income (10%-37% based on bracket)
- Long-term gains eligible for 0%, 15%, or 20% rates
- Net capital losses can offset up to $3,000 of ordinary income per year
- Unused losses carry forward to future years

### Wash Sale Rules
- [IRS Topic 409 - Wash Sales](https://www.irs.gov/taxtopics/tc409)
- Applies 30 days before and after sale date
- Disallowed loss is added to cost basis of replacement shares
- Holding period includes original holding period

## Support and Feedback

For issues or questions about tax reporting:
1. Check this guide first
2. Review test examples in `test_tax_reporting.py`
3. Consult with a qualified tax professional
4. File an issue on GitHub for bugs or feature requests

## Version History

### Version 1.0 (2026-01-23)
- Initial release
- IRS Form 8949 CSV export
- Wash sale detection
- Tax summary JSON
- CPA review report
- Comprehensive test suite
- Full documentation

---

**Disclaimer**: This tool is provided as-is without warranty. Always verify tax information with official brokerage statements and consult with a qualified tax professional. The developers are not responsible for any tax filing errors or omissions.
