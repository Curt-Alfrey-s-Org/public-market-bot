# Current Copilot Task

## Task Overview

Add comprehensive tests for dry-run (Live) mode configuration to ensure the mode override system works correctly for the fourth mode button in the web GUI.

## Branch Information

**Branch Name:** `copilot/add-dryrun-live-mode-tests`

**Base Branch:** `main`

## Task Description

The dry-run (Live) mode feature has been implemented in the web GUI as a fourth mode button. This mode acts like Live mode (using real credentials and risk checks) but with `DRY_RUN_MODE=true` to prevent actual order placement. We need to add tests to `test_mode_override.py` to validate this configuration.

### Background

The web GUI has four modes:
1. **Sandbox**: Paper trading with Schwab sandbox API
2. **Live**: Real trading with real money
3. **Training (yfinance)**: Simulation mode without API
4. **Dry-run (Live)**: Live-like mode but no orders placed (NEW)

The dry-run (Live) mode sets:
- `PAPER_TRADING_MODE=false` (treated as live)
- `SCHWAB_SANDBOX_MODE=false` (not sandbox)
- `SCHWAB_API_ENABLED=on` (API active)
- `DRY_RUN_MODE=true` (prevents order execution)

## Acceptance Criteria

- [ ] Add test for dry-run (Live) mode configuration in `test_mode_override.py`
- [ ] Test validates that `DRY_RUN_MODE` can be set and read dynamically
- [ ] Test verifies dry-run mode works with live-like settings
- [ ] All existing tests continue to pass
- [ ] CHANGELOG.md updated with new entry
- [ ] `.github/copilot-instructions.md` updated with "Current task" section
- [ ] Code follows existing test patterns and conventions
- [ ] Tests run successfully with `pytest test_mode_override.py -v`

## Implementation Steps

1. **Update Documentation**
   - Add "Current task" section to `.github/copilot-instructions.md` linking to this file
   - Update CHANGELOG.md with new entry

2. **Add Tests**
   - Add test method `test_dry_run_live_mode_configuration` to validate:
     - `DRY_RUN_MODE` environment variable can be set/read
     - Dry-run mode uses live-like settings (paper=false, sandbox=false, api=on)
     - DRY_RUN_MODE defaults to false when not set
   - Add test method `test_dry_run_mode_helper_function` (if helper exists in main.py)

3. **Run Tests**
   - Execute: `pytest test_mode_override.py -v`
   - Verify all tests pass

4. **Complete PR**
   - Request code review
   - Add `copilot-completed` label when finished

## Related Files

- `test_mode_override.py` - Test file to modify
- `main.py` - Contains mode configuration logic
- `web_gui.py` - Implements dry-run (Live) mode button
- `CHANGELOG.md` - Documentation to update
- `.github/copilot-instructions.md` - Copilot instructions to update

## References

- CHANGELOG.md: Dry-run (Live) mode implementation details
- web_gui.py: Sets `DRY_RUN_MODE=true`
- main.py: `DRY_RUN_MODE` environment variable definition

## Labels

When complete, add the following label to the PR:
- `copilot-completed` - Signals Copilot Sentinel that the task is done

### Auto-Label and Gate Notes

- Copilot branches (`copilot/<task-slug>`) are auto-labeled `copilot-completed` once all required checks succeed.
- If the label is missing but checks are green, add it manually in the PR sidebar (Labels → `copilot-completed`).
- The label gate re-checks on labeling and will pass automatically once the label is present.


## Notes

- Follow existing test patterns in `test_mode_override.py`
- Maintain consistency with other mode configuration tests
- Ensure proper setup/teardown to avoid test pollution
- Keep changes minimal and focused on dry-run mode testing
