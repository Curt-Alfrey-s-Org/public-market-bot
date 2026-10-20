# Error Log Collection System

## Overview

This implementation adds a comprehensive error log collection system to the market-pie5-bot project. The system collects all logs, self-test results, debug logs, and errors into a single `errorlogs.txt` file that can be analyzed by GitHub Copilot or shared with maintainers for debugging.

## Files Created

### 1. `collect_errorlogs.py`
Main Python script that collects logs from multiple sources:
- Application logs (*.log files in root directory)
- API logs (/tmp/market-bot-api.log)
- Debug logs (debug_logs/ directory)
- Trade logs and debug traces (logs/ directory)
- Test results (test_report_*.json, test_results.txt, test_failures.txt)
- Self-test results (selftest_debug.log)
- Error files (errors-i-found.txt)
- Backtest reports (backtest_report*.json)
- ML optimization reports (ml_optimization_*.json)
- Stock screener results (screener_results.txt)
- Git status and environment information

**Key Features:**
- Sanitizes sensitive data (API keys, tokens, passwords)
- Creates a table of contents for easy navigation
- Supports custom output filenames
- Handles large files with truncation
- Comprehensive error handling
- JSON file support with pretty printing

### 2. `collect_logs.sh`
Convenience shell script wrapper that:
- Calls the Python script with optional custom filename
- Provides clear output and usage instructions
- Shows commands for committing and pushing to remote

### 3. `test_collect_errorlogs.py`
Comprehensive unit tests covering:
- Section addition and management
- File content collection
- Line truncation for large files
- Directory scanning
- Output file generation
- Environment information collection
- Script existence and executability

**Test Results:** All 11 tests pass successfully.

### 4. `errorlogs.txt`
Generated output file containing all collected logs in a structured format:
- Header with timestamp and generation info
- Table of contents with source references
- Numbered sections for each log source
- Source file paths and metadata

## Documentation Updates

Updated `README.md` Troubleshooting section with:
- Instructions for collecting error logs
- List of what gets collected
- Usage examples
- Integration with existing troubleshooting workflow

## Security Considerations

The script properly sanitizes sensitive information:
- Environment variables containing: PASSWORD, SECRET, TOKEN, KEY, API_KEY, APP_SECRET, ENCRYPTION_KEY
- These are replaced with `***REDACTED***` in the output
- No sensitive credentials are exposed in the collected logs

## Usage

### Basic Usage
```bash
# Using the shell script (recommended)
./collect_logs.sh

# Using Python directly
python3 collect_errorlogs.py

# Custom output filename
./collect_logs.sh my_logs.txt
python3 collect_errorlogs.py my_logs.txt
```

### Workflow Integration
1. Run the script to collect logs: `./collect_logs.sh`
2. Review the generated `errorlogs.txt` file
3. Commit to repository: `git add errorlogs.txt`
4. Push for Copilot analysis: `git commit -m "Update error logs" && git push`

### Example Output Structure
```
================================================================================
ERROR LOGS AND DEBUG INFORMATION
Collected by collect_errorlogs.py
Generated: 2026-01-30T01:57:18.794173
================================================================================

Total Sections: 23

================================================================================
TABLE OF CONTENTS
================================================================================
1. Environment Information
2. Debug Log: README.md
3. Debug Log: env_info.txt
...
23. Git Status

[Each section follows with full content]
```

## Testing

All tests pass successfully:
```bash
python3 -m unittest test_collect_errorlogs -v
# Ran 11 tests in 0.004s
# OK
```

Tests cover:
- ✅ Section management
- ✅ File collection
- ✅ Directory scanning
- ✅ Line truncation
- ✅ Output generation
- ✅ Environment info collection
- ✅ Script executability

## Benefits

1. **Centralized Log Collection**: All logs in one place for easy analysis
2. **Copilot Integration**: Designed for GitHub Copilot to analyze bot behavior
3. **Debugging Efficiency**: Reduces time to gather diagnostic information
4. **Security**: Automatically sanitizes sensitive data
5. **Maintainability**: Well-tested and documented code
6. **Flexibility**: Supports custom output filenames and selective collection

## Integration with Existing Systems

The script integrates with existing logging infrastructure:
- **LogManager**: Collects trade logs and backtest results from logs/ directory
- **CopilotDebugLogger**: Collects debug traces from logs/copilot_debug_*.jsonl
- **Test Infrastructure**: Collects test reports and failure logs
- **Self-Test System**: Collects self-test debug logs
- **Git**: Captures current branch and status for context

## File Size Management

- Large files are truncated to prevent excessive output size
- Default max lines for API logs: 1000 lines
- Directory scanning limited to 50 files by default
- Most recent files prioritized for test reports and backtests

## Future Enhancements

Potential improvements:
- Add compression for very large log collections
- Support for log rotation and historical analysis
- Integration with CI/CD for automated log collection
- Web interface for log browsing
- Advanced filtering and search capabilities
- Automatic upload to cloud storage

## Conclusion

This implementation successfully addresses the requirement to "create script called errorlogs.txt push all logs, selftest results, debug logs, errors, to remote so copilot can analyze them." The script collects comprehensive diagnostic information, sanitizes sensitive data, and generates a well-structured output file that can be easily committed and pushed to the remote repository for analysis.
