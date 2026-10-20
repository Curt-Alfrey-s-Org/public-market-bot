# New Stats Features Added

## Overview

Added three new professional trading metrics to the stats system:
1. **Profit Factor (PF)** - Risk-adjusted performance metric
2. **Monthly Dollar % Change** - Monthly return percentage
3. **Monthly Returns Chart** - Visual curve showing monthly returns over time

## Features

### 1. Profit Factor (PF)

**Calculation**: `PF = Total Gross Profit / Total Gross Loss`

- **PF > 1.0**: Profitable (more profit than loss)
- **PF = 1.0**: Break-even
- **PF < 1.0**: Losing (more loss than profit)
- **PF = 0.0**: No trades or no losses (only profits)

**Display**: 
- Added to StatsOverview as a stat card
- Shows 2 decimal places (e.g., "1.45")

### 2. Monthly Dollar % Change

**Calculation**: 
- Groups trades by month (YYYY-MM format)
- Calculates cumulative capital per month
- Computes percentage change: `((Current Month Capital - Previous Month Capital) / Previous Month Capital) * 100`

**Display**:
- Added to StatsOverview as "Monthly Return" stat card
- Shows current month's return percentage
- Updates in real-time

### 3. Monthly Returns Chart

**Features**:
- Bar chart showing monthly returns as percentages
- **Professional Benchmark Zone**: Highlighted 3-4% range (professional investor target)
- Color coding:
  - 🟢 Green bars: Returns in 3-4% goal range
  - 🔵 Blue bars: Positive returns below goal
  - 🔴 Red bars: Negative returns
- Average monthly return calculation
- Performance status indicator:
  - ✓ Meeting Goal: Average ≥ 3%
  - ⚠ Below Goal: Average > 0% but < 3%
  - ✗ Negative Returns: Average < 0%

**Display**:
- Full-width chart on Dashboard
- Shows all months with trades
- Y-axis shows return percentages
- X-axis shows month labels
- Benchmark zone clearly marked

## Implementation Details

### Backend Changes

**File**: `api/models/responses.py`
- Added `profit_factor: float` to `StatsResponse`
- Added `monthly_return_pct: float` to `StatsResponse`
- Added `monthly_returns: List[Dict[str, Any]]` to `StatsResponse`

**File**: `api/routes/stats.py`
- Added profit factor calculation from trade history
- Added monthly returns calculation:
  - Groups trades by month
  - Tracks cumulative capital
  - Calculates percentage returns
- Returns monthly data for chart

### Frontend Changes

**File**: `frontend/src/api/stats.ts`
- Added `MonthlyReturn` interface
- Updated `Stats` interface with new fields

**File**: `frontend/src/components/StatsOverview.tsx`
- Added "Profit Factor" stat card
- Added "Monthly Return" stat card
- Updated grid to accommodate 7 stat cards (xl:grid-cols-7)

**File**: `frontend/src/components/MonthlyReturnsChart.tsx` (NEW)
- New component for monthly returns visualization
- Bar chart with professional benchmark zone
- Performance status indicator
- Responsive design

**File**: `frontend/src/pages/Dashboard.tsx`
- Added `MonthlyReturnsChart` component
- Placed below equity and P&L charts

## Professional Investor Benchmark

**Goal**: 3-4% monthly returns

This is the minimum target for professional investors. The system:
- Highlights the 3-4% range on the chart
- Shows average monthly return
- Indicates if the bot is meeting the goal
- Provides visual feedback on performance

## Data Flow

1. **Trade History** → Backend calculates:
   - Gross profit (sum of positive P&L)
   - Gross loss (sum of negative P&L)
   - Monthly P&L grouped by month
   - Monthly capital progression

2. **Backend API** → Returns:
   - `profit_factor`: Calculated PF
   - `monthly_return_pct`: Current month's return
   - `monthly_returns`: Array of monthly data

3. **Frontend** → Displays:
   - PF in stat card
   - Monthly return % in stat card
   - Monthly returns chart with benchmark

## Example Data Structure

```json
{
  "profit_factor": 1.45,
  "monthly_return_pct": 3.2,
  "monthly_returns": [
    {
      "month": "2026-01",
      "return_pct": 3.2,
      "pnl": 320.00,
      "capital": 10320.00
    },
    {
      "month": "2025-12",
      "return_pct": 2.8,
      "pnl": 280.00,
      "capital": 10000.00
    }
  ]
}
```

## Testing

The new features are integrated into the existing stats endpoint:
- No new endpoints required
- Uses existing trade history data
- Backward compatible (returns 0.0 and [] for new fields when no data)

## Future Enhancements

Potential improvements:
- Annualized return calculation
- Sharpe ratio
- Maximum drawdown
- Win/loss ratio
- Average win vs average loss
- Monthly returns comparison to market benchmarks
