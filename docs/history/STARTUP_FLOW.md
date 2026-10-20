# Startup Flow - Desktop Icon Double-Click

## Complete Startup Sequence

When you **double-click the desktop icon** (`market-pie5-web-gui.desktop`), here's exactly what happens:

### Step 1: Desktop Entry Execution
- **Action**: Desktop environment reads `.desktop` file
- **Executes**: `/usr/local/bin/market-pie5-launch-web-gui`
- **Terminal**: Opens terminal window (because `Terminal=true` in desktop file)

### Step 2: Launch Script Execution
- **Script**: `/usr/local/bin/market-pie5-launch-web-gui` (or `start_gui.sh` if symlinked)
- **Location**: Changes to project directory
- **Checks**: 
  - Virtual environment exists
  - Python dependencies installed
  - Node.js/npm available
  - Frontend dependencies installed

### Step 3: Virtual Environment Setup
- **Check**: If `venv/` directory exists
- **If missing**: Creates virtual environment (`python3 -m venv venv`)
- **Activates**: `source venv/bin/activate`
- **Status**: ✅ Virtual environment ready

### Step 4: Backend Dependencies Check
- **Check**: If `uvicorn` is installed
- **If missing**: Installs from `requirements-api.txt`
- **Status**: ✅ Backend dependencies ready

### Step 5: FastAPI Backend Startup
- **Command**: `uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload`
- **Process**: Starts in background
- **Logs**: Written to `/tmp/market-bot-api.log`
- **PID**: Saved to `/tmp/market-bot-api.pid`
- **Wait**: Script waits up to 30 seconds for API to respond
- **Health Check**: `curl http://localhost:8000/api/health`
- **Status**: ✅ API running on port 8000

### Step 6: API Startup Event
- **Event**: FastAPI `@app.on_event("startup")` triggers
- **Action**: Runs startup self-tests
  - Tests API health endpoint
  - Tests bot status endpoint
  - Tests stats endpoint
  - Tests trades endpoint
  - Tests messages endpoint
- **Logs**: Results logged to console
- **Status**: ✅ Startup tests complete

### Step 7: Frontend Dependencies Check
- **Check**: If `frontend/node_modules` exists
- **If missing**: Runs `npm install` in `frontend/` directory
- **Status**: ✅ Frontend dependencies ready

### Step 8: React Frontend Startup
- **Command**: `npm run dev` (runs `vite`)
- **Process**: Starts in background
- **Logs**: Written to `/tmp/market-bot-frontend.log`
- **PID**: Saved to `/tmp/market-bot-frontend.pid`
- **Wait**: Script waits up to 30 seconds for frontend to respond
- **Health Check**: `curl http://localhost:5173`
- **Status**: ✅ Frontend running on port 5173

### Step 9: Browser Auto-Open
- **Delay**: Waits 3 seconds
- **Attempts**: Tries to open browser automatically:
  1. `xdg-open http://localhost:5173`
  2. `gnome-open` (fallback)
  3. `kde-open` (fallback)
  4. `firefox` (fallback)
  5. `google-chrome` (fallback)
  6. `chromium-browser` (fallback)
- **If none work**: Shows message to open manually
- **Status**: ✅ Browser opens (or manual instruction shown)

### Step 10: Frontend Initialization
- **Browser**: Loads `http://localhost:5173`
- **Vite**: Serves React application
- **React**: Initializes and renders
- **API Connection**: Frontend connects to `http://localhost:8000`
- **Status**: ✅ Frontend loaded

### Step 11: Frontend Data Fetching
- **Queries**: React Query fetches initial data:
  - Bot status (`/api/bot/status`)
  - Stats (`/api/stats`)
  - Trades (`/api/trades`)
  - Messages (`/api/messages`)
  - System health (`/api/system/health`)
- **Status**: ✅ Data loaded

### Step 12: GUI Ready State
- **Display**: Dashboard shows:
  - Bot status (Stopped - not started yet)
  - Mode selector (all modes available, user can select)
  - Stats overview (empty or from previous session)
  - Control buttons (Start button available)
  - Sidebar with navigation
- **Status**: ✅ **GUI READY - USER INPUT REQUIRED**

---

## Where User Input is Required

### **Step 1: Select Trading Mode (REQUIRED BEFORE START)**
**The GUI is ready, but the bot is NOT started and mode is NOT set.**

User must:
1. **Select a trading mode** from the Mode Selector:
   - 🧪 **Sandbox** - Paper trading with Schwab sandbox API
   - ⚡ **Live** - Real trading with real money
   - 📊 **YFinance** - Pure simulation with Yahoo Finance data
   - 🔍 **Dry Run Live** - Test with live data but no trades
2. Mode is saved to `.env` file
3. Mode buttons are **enabled** (bot is not running)

### **Step 2: Start the Bot (REQUIRED TO BEGIN TRADING)**
**After selecting mode, user must explicitly start the bot.**

User must:
1. **Click "Start" button** in the Bot Controls section
2. This will:
   - Initialize bot instance with selected mode
   - Start trading loop in background thread
   - Begin trading operations
   - Mode buttons become **disabled** (cannot change while running)

### **Step 3: Stop Before Mode Change (REQUIRED TO CHANGE MODE)**
**If user wants to change mode after starting:**

User must:
1. **Click "Stop" button** to stop trading
2. Bot stops trading but instance remains
3. Mode buttons become **enabled** again
4. User can now select a different mode
5. User must click "Start" again to begin trading in new mode

### Optional User Actions (Available Anytime):
- View trades, logs, stats
- Configure settings
- View tax reports
- View messages and alerts

---

## Error Points (Where Things Can Fail)

### ❌ **Step 3 Failure**: Virtual environment creation fails
- **User sees**: Error message in terminal
- **Action needed**: Check Python installation, disk space

### ❌ **Step 4 Failure**: Backend dependencies fail to install
- **User sees**: Error message in terminal
- **Action needed**: Check internet connection, pip access

### ❌ **Step 5 Failure**: API fails to start
- **User sees**: "API may not be ready" warning
- **Action needed**: Check port 8000 availability, check logs

### ❌ **Step 6 Failure**: Startup tests fail
- **User sees**: Warning in API logs
- **Action needed**: Check API health, bot initialization

### ❌ **Step 7 Failure**: Frontend dependencies fail to install
- **User sees**: Error message in terminal
- **Action needed**: Check npm installation, internet connection

### ❌ **Step 8 Failure**: Frontend fails to start
- **User sees**: "Frontend may not be ready" warning
- **Action needed**: Check port 5173 availability, check logs

### ❌ **Step 9 Failure**: Browser doesn't auto-open
- **User sees**: Manual instruction message
- **Action needed**: Open browser manually to `http://localhost:5173`

### ❌ **Step 11 Failure**: API connection fails
- **User sees**: "Disconnected" status in GUI
- **Action needed**: Check API is running, check CORS settings

---

## Current Startup Flow Summary

```
Desktop Icon Double-Click
    ↓
Launch Script (/usr/local/bin/market-pie5-launch-web-gui)
    ↓
Check/Create Virtual Environment
    ↓
Check/Install Backend Dependencies
    ↓
Start FastAPI Backend (port 8000)
    ↓
Run Startup Self-Tests
    ↓
Check/Install Frontend Dependencies
    ↓
Start React Frontend (port 5173)
    ↓
Auto-Open Browser
    ↓
Frontend Loads & Connects to API
    ↓
Load All Data (stats, trades, messages, system health)
    ↓
✅ GUI READY - Bot NOT Started
    ↓
USER MUST: 1) Select Mode → 2) Click "Start" Button
    ↓
Bot Initializes with Selected Mode
    ↓
Trading Loop Begins
    ↓
Mode Buttons Disabled (must Stop to change mode)
```

---

## Optimization Opportunities

1. **Auto-start bot**: Could automatically start bot after GUI loads
2. **Faster startup**: Parallel dependency checks
3. **Better error handling**: More user-friendly error messages
4. **Progress indicator**: Show startup progress in terminal
5. **Health check page**: Show startup status in browser while waiting
