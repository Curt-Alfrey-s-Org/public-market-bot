# Shutdown Server Button - Expected Behavior

## What Should Happen

When the "Shutdown Server" button is pressed in the GUI:

### 1. Frontend (User Interaction)
- User clicks "Shutdown Server" button
- **Confirmation dialog appears**: "Are you sure you want to shutdown the entire server? This will stop the bot, close the API server, and you will need to restart it manually. The website will disconnect."
- If user clicks "Cancel": Nothing happens, operation cancelled
- If user clicks "OK": Proceeds to step 2

### 2. API Request
- Frontend sends `POST /api/bot/shutdown-server`
- Request is sent to backend

### 3. Backend Processing
- **Step 1**: Bot is shut down first (calls `shutdown_bot()`)
  - Bot instance is cleaned up
  - Bot thread is stopped
- **Step 2**: Response is sent immediately:
  ```json
  {
    "message": "API server shutdown initiated. The server will close in a moment.",
    "status": "shutting_down"
  }
  ```
- **Step 3**: Background thread is started
  - Waits 1 second (to allow response to be sent)
  - Calls `os._exit(0)` to terminate the process

### 4. Frontend Response Handling
- **Immediate alert**: "Server is shutting down. The connection will be lost in a moment."
- **After 2 seconds**: Alert "Server has been shut down. Please restart the API server to continue."
- All subsequent API queries fail with connection errors
- Frontend shows "Disconnected" status

### 5. Server Termination
- Process terminates (PID ends)
- Terminal closes (if started with `./start_api.sh`)
- Port 8000 becomes available
- All connections are closed

## Current Issue

The API server process is running but **not accessible** due to permission issues. This prevents testing the shutdown functionality.

**To test:**
1. Fix API permission issue (ensure API can bind to port 8000)
2. Start API: `./start_api.sh`
3. Click "Shutdown Server" button in GUI
4. Verify:
   - Confirmation dialog appears
   - Server shuts down after ~1 second
   - Process terminates
   - Frontend shows alerts

## Test Script

Run `test_shutdown_server.py` to test the shutdown functionality:

```bash
python3 test_shutdown_server.py
```

This will:
- Check if API is accessible
- Call shutdown-server endpoint
- Verify server actually shuts down
- Report results

## Expected Results

✅ **Success**: 
- API becomes inaccessible
- Process terminates
- Port 8000 is free

❌ **Failure**:
- API still accessible after shutdown
- Process still running
- Server didn't actually shut down
