# GUI Settings Persistence and Validation

## Overview

The GUI now includes comprehensive settings validation and persistence functionality. When you apply settings in the Settings tab, they are:
1. **Validated** to ensure all inputs are within acceptable ranges
2. **Persisted** to a `settings.json` file
3. **Automatically loaded** when the GUI starts up

This prevents runtime errors and ensures your settings are preserved across sessions.

## Features

### Input Validation

All settings inputs are validated when you click "Apply Settings":

| Setting | Validation Rules |
|---------|-----------------|
| **Total Capital** | Must be greater than 0 |
| **Min Allocation** | Must be greater than 0 |
| **Max Allocation** | Must be greater than 0 and >= Min Allocation |
| **Trailing Stop %** | Must be between 0 and 100 |
| **Risk Threshold %** | Must be between 0 and 100 |
| **Max Positions** | Must be greater than 0 (integer) |
| **Capital Floor %** | Must be between 0 and 100 |

If validation fails, you'll see an error message dialog explaining what needs to be corrected. No changes are saved when validation fails.

### Settings Persistence

- Settings are saved to `settings.json` in the project root directory
- The file is automatically created on first apply
- Settings are automatically loaded when the GUI starts
- If no `settings.json` exists, defaults from environment variables are used

### File Format

The `settings.json` file uses a simple JSON format:

```json
{
  "capital": 10000,
  "min_allocation": 100,
  "max_allocation": 500,
  "trailing_stop": 5.0,
  "risk_threshold": 5.0,
  "max_positions": 5,
  "capital_floor": 10.0,
  "enable_alerts": true,
  "alert_email": "operator@example.com"
}
```

## Usage

### Applying Settings

1. Open the GUI (`./start_bot.sh` or `python3 gui.py`)
2. Click on the **Settings** tab
3. Modify any settings you want to change
4. Click **Apply Settings**
5. If validation passes, you'll see: "Settings have been validated and saved successfully"
6. If validation fails, you'll see an error message with details

### Loading Settings

Settings are automatically loaded when the GUI starts:
- If `settings.json` exists, those settings are loaded
- If not, defaults from environment variables (`.env`) are used
- A log message confirms whether settings were loaded or defaults are being used

### Exporting/Importing Settings

You can also use the File menu to:
- **Export Settings**: Save current settings to a custom JSON file
- **Import Settings**: Load settings from a previously exported JSON file

This is useful for:
- Backing up your settings
- Sharing settings between installations
- Testing different configurations

## Error Handling

### Common Validation Errors

**"Total capital must be greater than 0"**
- You entered a negative number or zero for capital
- Enter a positive number (e.g., 10000)

**"Max allocation must be greater than 0 and >= min allocation"**
- Your max allocation is less than min allocation
- Ensure max allocation is at least equal to min allocation

**"Risk threshold must be between 0 and 100"**
- You entered a percentage outside the 0-100 range
- Enter a value between 0 and 100 (e.g., 5.0 for 5%)

**"Please enter valid numeric values"**
- You entered text instead of a number
- Ensure all numeric fields contain only numbers (e.g., 10000, not "ten thousand")

### File Errors

If settings cannot be saved or loaded, an error message will appear. Common causes:
- Insufficient disk space
- File permissions issues
- Corrupted `settings.json` file

Solution: Check file permissions and disk space. If `settings.json` is corrupted, delete it and apply settings again to create a new one.

## Integration with PDT Tracker

When you change the capital setting, the PDT (Pattern Day Trading) tracker is automatically updated with:
- New starting capital
- New capital floor (capital × capital_floor_percent)
- Updated current capital

This ensures PDT compliance tracking stays synchronized with your settings.

## Testing

The implementation includes comprehensive test coverage:

### Test Files

1. **`test_gui_settings_validation.py`**: Unit tests for validation logic (13 tests)
2. **`test_gui_integration.py`**: Integration tests for the full save/load cycle (6 tests)
3. **`test_gui_manual.py`**: Manual verification script

### Running Tests

```bash
# Run validation tests
python3 test_gui_settings_validation.py -v

# Run integration tests
python3 test_gui_integration.py -v

# Run manual verification
python3 test_gui_manual.py
```

All tests should pass with no errors.

## Technical Details

### Implementation

The settings persistence is implemented in `gui.py`:

- **`load_settings()`**: Called on GUI initialization to load settings from `settings.json`
- **`apply_settings()`**: Validates inputs and saves to `settings.json`

### Settings File Location

`settings.json` is stored in the project root directory and is excluded from Git (listed in `.gitignore`).

This is intentional because:
- Settings are user-specific and shouldn't be version controlled
- Different users may have different capital, risk preferences, etc.
- Sensitive information (email addresses) should not be committed

### Backward Compatibility

The implementation is fully backward compatible:
- If no `settings.json` exists, defaults from `.env` are used
- The GUI works exactly the same if you choose not to use persistence
- Existing functionality (Export/Import Settings via File menu) still works

## Benefits

✅ **No More Runtime Errors**: All inputs are validated before saving
✅ **Settings Persist**: Your preferences are saved across sessions
✅ **Better UX**: Clear error messages guide you to fix issues
✅ **Safe Defaults**: Missing settings file handled gracefully
✅ **Easy Testing**: Comprehensive test coverage ensures reliability

## Example Scenarios

### Scenario 1: First Time User

1. Start GUI - sees default settings from `.env`
2. Modifies capital to $15,000
3. Clicks Apply - settings validated and saved to `settings.json`
4. Restarts GUI - $15,000 capital automatically loaded

### Scenario 2: Invalid Input

1. User enters "abc" for capital
2. Clicks Apply
3. Error dialog: "Please enter valid numeric values"
4. Settings NOT saved
5. User corrects to "10000" and applies successfully

### Scenario 3: Configuration Management

1. User creates optimal settings for aggressive trading
2. File → Export Settings → saves as "aggressive.json"
3. Creates conservative settings
4. File → Export Settings → saves as "conservative.json"
5. Can switch between them via File → Import Settings

## Troubleshooting

### Settings Not Loading

**Problem**: GUI shows defaults instead of saved settings

**Solutions**:
- Check if `settings.json` exists in project root
- Check file permissions (should be readable)
- Check logs for error messages
- Try deleting `settings.json` and reapplying settings

### Validation Always Fails

**Problem**: Can't save settings even with valid inputs

**Solutions**:
- Check that numeric fields contain only numbers (no currency symbols, commas, etc.)
- Ensure max >= min for allocations
- Ensure percentages are 0-100, not 0-1 (use 5 not 0.05 for 5%)
- Check logs for specific validation error

### Settings Reset After Restart

**Problem**: Settings don't persist after closing GUI

**Solutions**:
- Verify `settings.json` is being created (check project root)
- Check that `settings.json` is not being deleted by cleanup scripts
- Ensure file permissions allow writing
- Check disk space

## See Also

- [User Guide](USER_GUIDE.md) - General GUI usage
- [Web GUI Guide](WEB_GUI_GUIDE.md) - Web interface settings persistence
- [Trading Enhancements Guide](TRADING_ENHANCEMENTS_GUIDE.md) - Risk management settings
