# Phase 1 Setup Guide - React + FastAPI

## ✅ Phase 1.1: Backend Setup - COMPLETED

### What's Been Created:

1. **API Structure:**
   - `api/main.py` - FastAPI application with CORS, health check, WebSocket
   - `api/routes/` - Route handlers for bot, stats, settings, trades, system
   - `api/models/` - Pydantic models for API responses
   - `api/bot.py` - Bot wrapper interface

2. **Endpoints Created:**
   - `GET /api/health` - Health check
   - `GET /api/bot/status` - Bot status
   - `POST /api/bot/start` - Start bot
   - `POST /api/bot/stop` - Stop bot
   - `POST /api/bot/shutdown` - Shutdown bot
   - `GET /api/stats` - Bot statistics
   - `GET /api/settings` - Get settings
   - `PUT /api/settings` - Update settings
   - `GET /api/trades` - Get trade history (with filters)
   - `GET /api/system` - System resource info
   - `WS /ws` - WebSocket for real-time updates

3. **Files Created:**
   - `api/__init__.py`
   - `api/main.py`
   - `api/bot.py`
   - `api/routes/bot.py`
   - `api/routes/stats.py`
   - `api/routes/settings.py`
   - `api/routes/trades.py`
   - `api/routes/system.py`
   - `api/models/responses.py`
   - `requirements-api.txt`
   - `start_api.sh`

### Next Steps:

1. **Install Dependencies:**
   ```bash
   # Install pip if not available
   sudo apt-get install python3-pip
   
   # Install FastAPI dependencies
   pip3 install -r requirements-api.txt
   ```

2. **Test API Server:**
   ```bash
   # Start the API server
   ./start_api.sh
   
   # Or manually:
   python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Verify Endpoints:**
   - Visit: http://localhost:8000/docs (FastAPI auto-generated docs)
   - Visit: http://localhost:8000/api/health (should return {"status": "healthy"})

### Integration with Existing Bot:

The API is designed to work with your existing `TradingBot` class. To connect:

1. In your bot startup code, initialize the API:
   ```python
   from api.bot import initialize_bot
   
   # After creating bot instance
   bot = TradingBot(...)
   initialize_bot(bot)
   ```

2. The API will then have access to bot data through `get_bot_instance()`

---

## 🔄 Phase 1.2: Frontend Setup - NEXT

### Prerequisites:
- Node.js 18+ installed
- npm or yarn package manager

### Steps:

1. **Create React App:**
   ```bash
   cd frontend
   npm create vite@latest . -- --template react-ts
   ```

2. **Install Dependencies:**
   ```bash
   npm install
   npm install -D tailwindcss postcss autoprefixer
   npm install @tanstack/react-query axios zustand
   npm install @radix-ui/react-*  # For Shadcn/ui components
   ```

3. **Configure Tailwind:**
   ```bash
   npx tailwindcss init -p
   ```

4. **Set up Shadcn/ui:**
   ```bash
   npx shadcn-ui@latest init
   ```

---

## 📝 Notes

- The API runs on port 8000 by default (configurable via `API_PORT` env var)
- CORS is configured to allow React dev server (localhost:5173)
- WebSocket endpoint is ready for real-time updates
- All endpoints return JSON responses with proper error handling

---

**Status:** Phase 1.1 Complete ✅ | Phase 1.2 Next 🔄
