# Duplicate Browser Tab Fix

## Issue
The bot was opening 2 tabs in the browser when started.

## Root Causes

1. **Vite Auto-Open**: Vite dev server might have been configured to auto-open browser
2. **start_gui.sh Auto-Open**: The startup script explicitly opens the browser
3. **Multiple Script Executions**: If script runs twice, browser opens twice

## Fixes Applied

### 1. **Disabled Vite Auto-Open** ✅
- Added `open: false` to `vite.config.ts`
- Prevents Vite from automatically opening browser
- Only `start_gui.sh` handles browser opening now

### 2. **Added Duplicate Check in start_gui.sh** ✅
- Checks if browser is already opening (process check)
- Checks if browser tab is already connected (port check)
- Only opens browser if not already open

## Changes Made

### `frontend/vite.config.ts`
```typescript
server: {
  port: 5173,
  open: false, // Disable Vite's auto-open browser
  // ...
}
```

### `start_gui.sh`
- Added browser open detection
- Only opens if not already open
- Prevents duplicate tabs

## Result

✅ **Only one browser tab opens** when starting the bot
✅ **No duplicate tabs** even if script runs multiple times
✅ **Clean startup experience**

## Testing

1. Run `./start_gui.sh`
2. Verify only **one** browser tab opens
3. If you run the script again, it should detect the existing tab and not open another
