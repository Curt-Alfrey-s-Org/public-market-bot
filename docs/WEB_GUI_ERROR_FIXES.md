# Web GUI Error Fixes

**Date:** January 26, 2026  
**Issue:** Plotly errors and other Web GUI errors  
**Status:** ✅ **FIXED**

---

## Issues Found and Fixed

### 1. Plotly Chart Column Name Case Sensitivity (CRITICAL)

**Problem:**
- yfinance sometimes returns uppercase column names (`Open`, `Close`, `High`, `Low`, `Volume`)
- Code was checking for lowercase columns (`open`, `close`, `high`, `low`, `volume`)
- This caused `KeyError` when trying to access columns

**Error:**
```
KeyError: 'open'
Missing column 'open' in data for AAPL
```

**Fix:**
- Added column name normalization to lowercase before checking
- Improved error messages to show available columns
- Added better column validation

**Location:** `web_gui.py` → `update_chart()` function (line ~3998)

**Code Change:**
```python
# Before
required_cols = ['open', 'high', 'low', 'close', 'volume']
for col in required_cols:
    if col not in historical_data.columns:
        logger.error(f"Missing column '{col}' in data for {selected_ticker}")
        return get_empty_chart_figure()

# After
# Normalize column names to lowercase (yfinance sometimes returns uppercase)
historical_data.columns = historical_data.columns.str.lower()

# Ensure we have required columns
required_cols = ['open', 'high', 'low', 'close', 'volume']
missing_cols = [col for col in required_cols if col not in historical_data.columns]
if missing_cols:
    logger.error(f"Missing columns {missing_cols} in data for {selected_ticker}. Available columns: {list(historical_data.columns)}")
    return get_empty_chart_figure()
```

---

### 2. Data Type and Index Handling

**Problem:**
- Index might not be datetime
- Data might contain non-numeric values
- Data might not be sorted chronologically

**Fix:**
- Convert index to datetime if needed
- Sort data by index
- Convert columns to numeric with error handling
- Remove NaN values after conversion

**Code Added:**
```python
# Ensure index is datetime and data is sorted
if not isinstance(historical_data.index, pd.DatetimeIndex):
    try:
        historical_data.index = pd.to_datetime(historical_data.index)
    except Exception as e:
        logger.warning(f"Could not convert index to datetime for {selected_ticker}: {e}")

# Sort by index to ensure chronological order
historical_data = historical_data.sort_index()

# Ensure we have numeric data (handle any non-numeric values)
for col in ['open', 'high', 'low', 'close', 'volume']:
    historical_data[col] = pd.to_numeric(historical_data[col], errors='coerce')

# Remove any rows with NaN values after conversion
historical_data = historical_data.dropna(subset=['open', 'high', 'low', 'close', 'volume'])

if historical_data.empty:
    logger.error(f"No valid data after cleaning for {selected_ticker}")
    return get_empty_chart_figure()
```

---

### 3. Enhanced Error Handling for Data Fetching

**Problem:**
- Exceptions during data fetching were not caught properly
- No fallback handling for fetch failures

**Fix:**
- Added try-except blocks around data fetching
- Better error logging
- Graceful fallback to daily data if intraday fails

**Code Added:**
```python
# Fetch 1 day of 5-minute interval data
try:
    historical_data = data_fetcher.fetch_historical_data_yfinance(
        selected_ticker, 
        period='1d',
        interval='5m'
    )
except Exception as e:
    logger.warning(f"Error fetching intraday data for {selected_ticker}: {e}")
    historical_data = None

# Fallback to daily data
if historical_data is None or historical_data.empty:
    try:
        historical_data = data_fetcher.fetch_historical_data_yfinance(
            selected_ticker,
            period='1mo',
            interval='1d'
        )
    except Exception as e:
        logger.warning(f"Error fetching daily data for {selected_ticker}: {e}")
        historical_data = None
```

---

### 4. Chart Creation Error Handling

**Problem:**
- Candlestick chart creation could fail with invalid data
- Volume bar creation could fail
- Price range calculation could fail

**Fix:**
- Added try-except blocks around chart creation
- Fallback to default colors if volume colors fail
- Better error handling for price range calculation

**Code Added:**
```python
# Create candlestick chart with error handling
try:
    candlestick = go.Candlestick(...)
except Exception as e:
    logger.error(f"Error creating candlestick chart for {selected_ticker}: {e}")
    return get_empty_chart_figure()

# Create volume bars with error handling
try:
    volume_colors = [...]
    volume_bar = go.Bar(...)
except Exception as e:
    logger.warning(f"Error creating volume bars for {selected_ticker}: {e}, using default colors")
    volume_bar = go.Bar(..., marker={'color': COLORS['info'], ...})

# Calculate price range with error handling
try:
    price_min = float(historical_data['low'].min())
    price_max = float(historical_data['high'].max())
    ...
except Exception as e:
    logger.warning(f"Error calculating price range for {selected_ticker}: {e}")
    # Fallback calculation
    price_min = float(historical_data['close'].min())
    price_max = float(historical_data['close'].max())
    ...
```

---

## Files Modified

1. **`web_gui.py`**
   - Fixed column name case sensitivity (line ~3998)
   - Added data type validation and cleaning
   - Enhanced error handling for data fetching
   - Improved chart creation error handling
   - Added index datetime conversion
   - Added data sorting and NaN removal

---

## Testing

### Verification Steps

1. ✅ Column normalization works with uppercase/lowercase columns
2. ✅ Missing column detection works correctly
3. ✅ Candlestick chart creation works
4. ✅ Error handling prevents crashes
5. ✅ Fallback mechanisms work

### Test Cases

**Test 1: Uppercase Columns**
```python
data = pd.DataFrame({
    'Open': [100, 101],
    'Close': [101, 100],
    ...
})
# Should normalize to lowercase and work
```

**Test 2: Missing Columns**
```python
data = pd.DataFrame({
    'open': [100, 101],
    # Missing 'close', 'high', 'low', 'volume'
})
# Should detect missing columns and return empty chart
```

**Test 3: Non-Numeric Data**
```python
data = pd.DataFrame({
    'open': ['100', '101'],  # String instead of numeric
    ...
})
# Should convert to numeric and remove NaN
```

---

## Expected Behavior After Fixes

1. **Charts load correctly** with yfinance data (regardless of column case)
2. **Error messages are clear** when data is unavailable
3. **No crashes** when data is invalid or missing
4. **Graceful fallbacks** when data fetching fails
5. **Proper data cleaning** before chart creation

---

## Known Issues (Not Fixed - Expected Behavior)

1. **Schwab API Errors** - Skipped per user request (no credentials configured)
2. **Delisted Stocks** - yfinance returns errors for delisted stocks (expected)
3. **No Data Available** - Some symbols may not have data (shows empty chart with message)

---

## Status

✅ **ALL PLOTLY ERRORS FIXED**

- Column name case sensitivity: ✅ Fixed
- Data type validation: ✅ Fixed
- Error handling: ✅ Enhanced
- Chart creation: ✅ Improved
- Data fetching: ✅ More robust

---

**Last Updated:** January 26, 2026
