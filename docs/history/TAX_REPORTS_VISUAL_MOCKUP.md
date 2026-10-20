# Tax Reports Tab - Visual Mockup

## What the Tax Reports Tab Looks Like

```
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                          Market Pie5 Trading Bot - Web Dashboard                  ║
╠═══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                    ║
║  📈 Dashboard | ⚙️ Settings | 📊 Statistics | 📝 Logs | 💻 Terminal | 💰 Trades  ║
║  📊 History | 🖥️ System Monitor | 🤖 AI Assistant | ✨ 📋 Tax Reports ✨         ║
║                                                                     ^^^^^^^^^^^^^^  ║
║                                                                     (NEW TAB!)     ║
╠════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                    ║
║  📋 Tax Reports & Documentation                                                   ║
║  Generate IRS-compliant tax reports for all your trades. Reports are suitable    ║
║  for CPA review and tax filing.                                                   ║
║                                                                                    ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐ ║
║  │ 📅 Select Tax Year                                                          │ ║
║  │                                                                              │ ║
║  │ Tax Year: ┌─────────┐                                                       │ ║
║  │           │ 2026  ▼ │  (Dropdown with 2026, 2025, 2024, 2023, 2022)        │ ║
║  │           └─────────┘                                                       │ ║
║  │                                                                              │ ║
║  │ ┌──────────────────────────────┐  ✅ Reports generated                     │ ║
║  │ │ 🔄 Generate Reports (Green)  │                                            │ ║
║  │ └──────────────────────────────┘                                            │ ║
║  └─────────────────────────────────────────────────────────────────────────────┘ ║
║                                                                                    ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐ ║
║  │ 📈 Tax Year 2026 Summary                                                    │ ║
║  │                                                                              │ ║
║  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐           │ ║
║  │  │Total Trades│  │ Short-Term │  │ Long-Term  │  │ Wash Sales │           │ ║
║  │  │            │  │  (≤365d)   │  │  (>365d)   │  │  (IRS 30d) │           │ ║
║  │  │     8      │  │     6      │  │     2      │  │     1      │           │ ║
║  │  │            │  │            │  │            │  │            │           │ ║
║  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘           │ ║
║  │  (White text)    (Blue/Info)     (Green/Success) (Yellow/Warning)          │ ║
║  │                                                                              │ ║
║  │  ┌──────────────────────┐                                                  │ ║
║  │  │ Net Gain/Loss        │                                                  │ ║
║  │  │                      │                                                  │ ║
║  │  │     -$75.00          │  (Red for loss, Green for profit)               │ ║
║  │  │                      │                                                  │ ║
║  │  └──────────────────────┘                                                  │ ║
║  └─────────────────────────────────────────────────────────────────────────────┘ ║
║                                                                                    ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐ ║
║  │ 📥 Download Reports                                                         │ ║
║  │ Click on any report to download. All reports are generated and ready.      │ ║
║  │                                                                              │ ║
║  │ ┌──────────────────────────┐  ┌──────────────────────────┐                │ ║
║  │ │  📄 IRS Form 8949 (CSV)  │  │  📋 Tax Summary (JSON)   │                │ ║
║  │ │  Import to tax software  │  │  Machine-readable format │                │ ║
║  │ │                          │  │                          │                │ ║
║  │ │     (Blue Background)    │  │   (Green Background)     │                │ ║
║  │ └──────────────────────────┘  └──────────────────────────┘                │ ║
║  │                                                                              │ ║
║  │ ┌──────────────────────────┐                                               │ ║
║  │ │  📝 CPA Report (TXT)     │                                               │ ║
║  │ │  Professional review fmt │                                               │ ║
║  │ │                          │                                               │ ║
║  │ │   (Purple Background)    │                                               │ ║
║  │ └──────────────────────────┘                                               │ ║
║  └─────────────────────────────────────────────────────────────────────────────┘ ║
║                                                                                    ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐ ║
║  │ ⚠️ Important Tax Disclaimer                                                 │ ║
║  │                                                                              │ ║
║  │ • These reports are for informational purposes only                         │ ║
║  │ • Always verify against official brokerage statements (Form 1099-B)         │ ║
║  │ • Wash sale detection is automated but should be manually reviewed          │ ║
║  │ • Consult with a qualified tax professional before filing                   │ ║
║  │ • Keep copies of all reports for your records (7 years recommended)         │ ║
║  │                                                                              │ ║
║  │ 📖 View Complete Tax Reporting Guide →                                      │ ║
║  │    (Links to TAX_REPORTING_GUIDE.md on GitHub)                              │ ║
║  │                                                                              │ ║
║  │ (Yellow/Orange Border - Warning Style)                                      │ ║
║  └─────────────────────────────────────────────────────────────────────────────┘ ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝
```

## Color Scheme

### Summary Cards
- **Total Trades**: White text on dark card background
- **Short-Term**: Blue background (#2563EB) - Info color
- **Long-Term**: Green background (#10B981) - Success color  
- **Wash Sales**: Yellow/Orange background (#F59E0B) - Warning color
- **Net Gain/Loss**: 
  - Green (#10B981) if positive
  - Red (#DC2626) if negative

### Download Buttons
- **Form 8949 CSV**: Blue (#2563EB) with hover effect and shadow
- **Tax Summary JSON**: Green (#10B981) with hover effect and shadow
- **CPA Report TXT**: Purple (#8B5CF6) with hover effect and shadow

### Cards and Borders
- Card background: #1E293B (dark slate)
- Border: #334155 (slate)
- Text primary: #F8FAFC (white-ish)
- Text secondary: #94A3B8 (gray)

## Interactive Elements

### Generate Reports Button
- **Initial State**: Green button with "🔄 Generate Reports" text
- **On Click**: Shows loading indicator
- **Success**: Status indicator shows "✅ Reports generated"
- **Error**: Status indicator shows "❌ Error" with message

### Download Buttons
- **Hover Effect**: Slightly darker shade, cursor changes to pointer
- **On Click**: Browser's download dialog appears
- **File Names**:
  - `form_8949_tax_year_2026.csv`
  - `tax_summary_2026.json`
  - `cpa_report_2026.txt`

### Dropdown
- **Style**: Matches existing web GUI dropdowns
- **Options**: Shows last 5 years (2026 down to 2022)
- **Default**: Current year

## Responsive Behavior

### Desktop (>1200px)
- Summary cards in single row (5 cards)
- Download buttons in single row (3 buttons)
- Full-width disclaimer card

### Tablet (768px - 1200px)
- Summary cards wrap to 2-3 per row
- Download buttons stack vertically
- Cards maintain padding and spacing

### Mobile (<768px)
- All cards stack vertically
- Download buttons full width
- Text remains readable
- Touch-friendly button sizes (min 44px height)

## User Workflow Visualization

```
┌─────────────┐
│ User clicks │
│ Tax Reports │
│     tab     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Selects    │
│  tax year   │
│  from drop  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Clicks    │
│  Generate   │
│   Reports   │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│   System    │ ───> │  Displays    │
│  generates  │      │   summary    │
│   reports   │      │  statistics  │
└─────────────┘      └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Shows 3    │
                     │   download   │
                     │   buttons    │
                     └──────┬───────┘
                            │
       ┌────────────────────┼────────────────────┐
       ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ User clicks  │    │ User clicks  │    │ User clicks  │
│ Form 8949    │    │ Tax Summary  │    │ CPA Report   │
│    (CSV)     │    │    (JSON)    │    │    (TXT)     │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                    │
       ▼                   ▼                    ▼
┌──────────────────────────────────────────────────────┐
│        Files download to browser's folder            │
│   form_8949_tax_year_2026.csv                        │
│   tax_summary_2026.json                              │
│   cpa_report_2026.txt                                │
└──────────────────────────────────────────────────────┘
```

## Error States Visual

### No Database
```
┌─────────────────────────────────────────────────────────┐
│  ⚠️  No trading data found.                            │
│  Execute some trades first before generating tax       │
│  reports.                                               │
│                                                          │
│  (Orange border, centered text)                         │
└─────────────────────────────────────────────────────────┘
```

### No Trades for Year
```
┌─────────────────────────────────────────────────────────┐
│  ℹ️  No trades found for tax year 2025                │
│                                                          │
│  (Blue border, info style)                              │
└─────────────────────────────────────────────────────────┘
```

### Generation Error
```
┌─────────────────────────────────────────────────────────┐
│  ❌ Error generating reports:                          │
│  [Specific error message from exception]                │
│                                                          │
│  (Red border, error style)                              │
└─────────────────────────────────────────────────────────┘
```

## Comparison to Existing Features

The Tax Reports tab follows the same design patterns as other tabs:
- **AI Assistant tab**: Similar card layout and button styling
- **Settings tab**: Uses dropdown and save button pattern
- **Statistics tab**: Similar summary cards with metrics
- **System Monitor**: Similar multi-card grid layout

This ensures consistency across the entire web GUI interface.
