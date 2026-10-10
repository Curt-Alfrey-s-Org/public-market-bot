# Analyzing Self-Test Logs

Self-test output is written so you can **analyze debug logs** easily without digging through the full app log.

## Where to look

1. **API / startup log**  
   All self-test lines use the prefix **`[SELFTEST]`**.  
   - Example: `trading_bot.log`, or wherever the API process logs (e.g. `./start_api.sh` output).  
   - Search for: **`[SELFTEST]`**.

2. **Full run debug file (on failure)**  
   When you use **Run Tests** in the GUI (or call the run-tests API) and the run **fails** or has **stderr**, the full stdout and stderr are written to:
   ```text
   <project_root>/selftest_debug.log
   ```
   Open that file to analyze failures (stack traces, assertion messages, etc.).

## What you’ll see

- **Startup self-tests** (when the API starts):  
  One line per test, e.g.  
  `[SELFTEST] ✓ Module Imports (12ms)`  
  `[SELFTEST] ✗ Bot Manager Init (5ms): UnboundLocalError: ...`

- **Summary after startup:**  
  `[SELFTEST] ✓ Startup self-tests passed: 8/8 in 0.45s`  
  or  
  `[SELFTEST] ⚠ Startup self-tests: 6/8 passed, 2 failed in 0.52s`

- **Full suite (Run Tests button):**  
  `[SELFTEST] Run completed: PASS (returncode=0) in 12.34s`  
  or  
  `[SELFTEST] Run completed: FAIL (returncode=1) in 8.50s`  
  `[SELFTEST] Debug log written to .../selftest_debug.log`

## Quick analysis

- **Grep for failures:**  
  `grep '\[SELFTEST\] ✗' trading_bot.log`  
  (or your API log path)

- **Inspect a failed full run:**  
  Open `selftest_debug.log` in the project root and read the **STDERR** and **STDOUT** sections.

- **Log level:**  
  With `LOG_LEVEL=DEBUG`, the last 50 lines of the full-run output are also sent to the logger at DEBUG level (still prefixed with `[SELFTEST]`).
