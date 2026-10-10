# Trading Settings & Controls

What settings control trading, where those controls live in the UI, and how the code uses them.

---

## 1. Overview

| Control type | Where | What it does |
|-------------|--------|---------------|
| **Settings > Trading** | Sidebar → Settings → Trading | Capital, position sizing, trading modes (paper, dry run, backtest, etc.) |
| **Settings > Risk Management** | Settings → Risk Management | Risk threshold, stop loss, take profit |
| **Settings > Alerts** | Settings → Alerts | Email alerts on/off |
| **Settings > Advanced** | Settings → Advanced | Trading frequency, throttling, logging, exit refresh |
| **Dashboard: Mode Selector** | Dashboard widget | Quick mode switch: Sandbox / Live / YFinance / Dry Run Live |
| **Dashboard: Bot Controls** | Header (Start / Stop / Shutdown) | Start, stop, or shutdown the bot |
| **Pending Trades** | Sidebar → Pending Trades | Approve/reject trades when manual approval is on |

---

## 2. Settings > Trading

**Location:** Sidebar → **Settings** → **Trading** category.

**UI:** `SettingsSection` → `renderTradingSettings()`  
**Code:** `frontend/src/components/SettingsSection.tsx` (lines 96–256), `getCategorySettings('trading')` (lines 35–49).

### 2.1 Capital & position sizing

| Setting | UI label | Env var | Description |
|--------|----------|---------|-------------|
| **Total Capital** | Total Capital | `BOT_TOTAL_CAPITAL` | Capital available for trading |
| **Min Allocation** | Min Allocation | `BOT_MIN_ALLOCATION` | Minimum $ per trade |
| **Max Allocation** | Max Allocation | `BOT_MAX_ALLOCATION` | Maximum $ per trade |
| **Position Size (%)** | Position Size (%) | `BOT_POSITION_SIZE` | Position size as % of capital (stored as decimal) |
| **Max Open Positions** | Max Open Positions | `BOT_MAX_OPEN_POSITIONS` | Max concurrent positions |
| **Use margin** | Use margin | `USE_MARGIN` | OFF: settled capital only (T+1). ON: total capital (margin); unsettled counts as available. |

**Persistence:** Settings API `PUT /api/settings` → `api/routes/settings.py` → `.env` via `_update_env_file` and `setting_to_env_map` (lines 72–100, 104–127).

**Bot usage:**
- `BOT_TOTAL_CAPITAL`: read when the **bot starts** (`api/bot_manager.py` line 42, `initialize_bot_from_main`). Passed into `TradingBot(total_capital=capital)`. Updates apply on **next Start**.
- `BOT_MIN_ALLOCATION`, `BOT_MAX_ALLOCATION`, `BOT_POSITION_SIZE`, `BOT_MAX_OPEN_POSITIONS`: read at **process startup** from `os.getenv` in `main.py` (e.g. 353–356, 383, 445). Updates apply after **API/server restart**.
- `USE_MARGIN`: read at **runtime** (reloads .env) in `_is_margin_enabled()` and `get_available_capital()` / `check_settled_capital_available()`. When OFF, availability = settled only; when ON, availability = total capital.

**References:**  
`main.py` 353–356, 383, 445, 1273, 2582, 6498–6502; `api/bot_manager.py` 41–46; `api/routes/settings.py` 72–100, 172–177, 211–214.

### 2.2 Trading modes (checkboxes)

| Setting | UI label | Env var | Description |
|--------|----------|---------|-------------|
| **Manual Trade Approval** | Manual Trade Approval | `MANUAL_TRADE_APPROVAL_MODE` | Trades go to Pending Trades for approve/reject |
| **Paper Trading Mode** | Paper Trading Mode | `PAPER_TRADING_MODE` | Simulate trades (no real money) |
| **Dry Run Mode** | Dry Run Mode | `DRY_RUN_MODE` | Validate workflow, no orders |
| **Backtest Mode** | Backtest Mode | `BACKTEST_MODE` | Historical backtest only |
| **Schwab Sandbox Mode** | Schwab Sandbox Mode | `SCHWAB_SANDBOX_MODE` | Use Schwab sandbox API |
| **Schwab API Status** | Schwab API Status | `SCHWAB_API_ENABLED` | on = use Schwab, off = yfinance |

**Persistence:** Same as above (Settings API → `.env`).

**Bot usage:**
- `PAPER_TRADING_MODE`, `SCHWAB_SANDBOX_MODE`, `SCHWAB_API_ENABLED`: read **at runtime** via `_get_paper_trading_mode()`, `_get_schwab_sandbox_mode()`, `_get_schwab_api_enabled()` (`main.py` 668–698). Used for data source and mode (e.g. 5775–5782). Changes can apply without restart when bot reads env.
- `DRY_RUN_MODE`: `_get_dry_run_mode()` (712–723). Runtime.
- `MANUAL_TRADE_APPROVAL_MODE`: used in `main.py` (e.g. 410, 4382, 2293). Checked at runtime from env where those helpers apply; otherwise at startup.

**References:**  
`main.py` 394, 410, 668–698, 712–723, 4378–4382, 5775–5782; `SettingsSection.tsx` 159–253; `api/routes/settings.py` 80–86, 181–186, 227–232.

---

## 3. Settings > Risk Management

**Location:** Settings → **Risk Management**.

**UI:** `renderRiskSettings()` in `SettingsSection.tsx` (lines 259–295).

| Setting | UI label | Env var | Description |
|--------|----------|---------|-------------|
| **Risk Threshold (%)** | Risk Threshold (%) | `BOT_RISK_THRESHOLD` | Max risk per trade as % |
| **Stop Loss (%)** | Stop Loss (%) | `BOT_STOP_LOSS_PERCENT` | Stop loss % |
| **Take Profit (%)** | Take Profit (%) | `BOT_TAKE_PROFIT_PERCENT` | Take profit % |

**Persistence:** Settings API → `.env` (same mechanism as Trading).

**Bot usage:** Read at **startup** in `main.py` (353, 446, 450). Used for risk and exit logic (e.g. 2270, 2582). **Restart required** for changes.

**References:**  
`main.py` 353, 446, 450, 2270, 2582; `api/routes/settings.py` 175–176, 179; `SettingsSection.tsx` 261–293.

---

## 4. Settings > Alerts

**Location:** Settings → **Alerts**.

**UI:** `renderAlertsSettings()` (lines 297–332). Toggle **Email Alerts** on/off.

| Setting | Env var | Description |
|--------|---------|-------------|
| **Email Alerts** | `ALERT_EMAIL_ENABLED` | ON = send email alerts; OFF = no emails |

**Persistence:** Settings API → `.env`. `ALERT_EMAIL_ENABLED` in `setting_to_env_map` and `get_setting_bool` (settings.py 99–100, 199–200).

**Bot usage:** Checked **at send-time** in `AlertSystem._is_email_alerts_enabled()` (reloads `.env`), then `_should_send_email()`. **No restart needed.**

**References:**  
`main.py` 827–851 (`_is_email_alerts_enabled`, `_should_send_email`); `api/routes/settings.py` 99–100, 199–200, 228; `SettingsSection.tsx` 56–59, 297–332.

---

## 5. Settings > Advanced

**Location:** Settings → **Advanced**.

**UI:** `renderAdvancedSettings()` in `SettingsSection.tsx` (lines 334–454).

| Setting | Env var | Description |
|--------|---------|-------------|
| **Trading Frequency** | `TRADING_FREQUENCY` | Seconds between trades |
| **Exit Price Refresh** | `EXIT_REFRESH_PRICE` | Refresh price before SELL/COVER |
| **Log Level** | `LOG_LEVEL` | Min log level |
| **Debug Mode** | `DEBUG` | Debug logging |
| **Top Performers Refresh** | `TOP_PERFORMERS_REFRESH_INTERVAL` | Seconds between watchlist updates |
| **Async Request Timeout** | `ASYNC_REQUEST_TIMEOUT` | API timeout |
| **Max CPU / Memory %** | `BOT_MAX_CPU_PERCENT`, `BOT_MAX_MEMORY_PERCENT` | Throttling thresholds |
| **Throttle Delay** | `BOT_THROTTLE_DELAY` | Delay when throttling |
| **Enable Throttling** | `BOT_ENABLE_THROTTLING` | Throttling on/off |

**Persistence:** Settings API → `.env` (same mechanism).

**Bot usage:** Read at **startup** in `main.py` (e.g. 586–593, 343–365). **Restart required** for changes.

**References:**  
`main.py` 343–365, 586–593; `api/routes/settings.py` 89–96, 188–196, 219–226; `SettingsSection.tsx` 61–70, 334–454.

---

## 6. Dashboard: Mode Selector

**Location:** **Dashboard** → **Mode Selector** widget (draggable).

**UI:** `ModeSelector` in `frontend/src/components/ModeSelector.tsx`. Dashboard passes `currentMode` and `botRunning` from `useBotStatus()`.

**Modes:**

| Mode | Env set | Description |
|------|---------|-------------|
| **Sandbox** | `PAPER_TRADING_MODE=true`, `SCHWAB_SANDBOX_MODE=true`, `SCHWAB_API_ENABLED=on` | Paper + Schwab sandbox |
| **Live** | `PAPER_TRADING_MODE=false`, `SCHWAB_SANDBOX_MODE=false`, `SCHWAB_API_ENABLED=on` | Live trading |
| **YFinance** | `PAPER_TRADING_MODE=true`, `SCHWAB_SANDBOX_MODE=false`, `SCHWAB_API_ENABLED=off` | Simulation with yfinance |
| **Dry Run Live** | `PAPER_TRADING_MODE=false`, `DRY_RUN_MODE=true`, `SCHWAB_API_ENABLED=on` | Live data, no orders |

**Flow:** User chooses mode → `POST /api/bot/mode` with `{ mode }` → `api/routes/bot.py` `set_bot_mode` updates `os.environ` and `.env` (lines 325–451). Mode applies when user **starts the bot** (bot not running during mode change).

**References:**  
`ModeSelector.tsx`; `api/routes/bot.py` 325–451; `api/bot_manager.py` 50–62 (mode from env on init); `Dashboard.tsx` 22–28, 74–75.

---

## 7. Dashboard: Bot Controls

**Location:** **Dashboard** header (top right).

**UI:** `BotControls` in `frontend/src/components/BotControls.tsx`.

**Actions:**
- **Start:** `POST /api/bot/start` → `start_bot()` in `bot_manager.py`. (Re)initializes bot from env (capital, mode) and starts it.
- **Stop:** `POST /api/bot/stop` → `stop_bot()`. Pauses trading, keeps instance.
- **Shutdown:** `POST /api/bot/shutdown-server` → stops bot and shuts down API server.

**References:**  
`BotControls.tsx` 8–93; `api/routes/bot.py` 96–145; `api/bot_manager.py` 76–145; `Dashboard.tsx` 74–75.

---

## 8. Pending Trades (manual approval)

**Location:** Sidebar → **Pending Trades**.

**When:** Only relevant when **Manual Trade Approval** is ON (Settings → Trading).

**UI:** `PendingTrades` page lists pending trades; `PendingTradeCard` has **Approve** / **Reject**. Approve → `pendingTradesApi.approveTrade(trade_id)`; Reject → `pendingTradesApi.rejectTrade(trade_id, reason)`.

**API:** `api/routes/pending_trades.py` — `POST /api/pending-trades/approve`, `POST /api/pending-trades/reject`. Uses `bot.approve_pending_trade` / `bot.reject_pending_trade` (lines 86–124).

**References:**  
`PendingTrades.tsx`, `PendingTradeCard.tsx` 42–67; `api/pendingTrades.ts` (approveTrade, rejectTrade); `api/routes/pending_trades.py` 86–124; `SettingsSection` Manual Trade Approval (above).

---

## 9. Code verification checklist

| Item | Status | Location |
|------|--------|----------|
| Settings API reads/writes .env for trading, risk, alerts, advanced | ✅ | `api/routes/settings.py` 54–144, 172–201, 205–267 |
| `setting_to_env_map` includes all trading-related keys | ✅ | `api/routes/settings.py` 72–100 |
| `SettingsSection` Trading UI (capital, modes, Schwab) | ✅ | `SettingsSection.tsx` 96–256, `getCategorySettings` 35–49 |
| `SettingsSection` Risk UI | ✅ | `SettingsSection.tsx` 259–295, 50–55 |
| `SettingsSection` Alerts UI (email toggle) | ✅ | `SettingsSection.tsx` 56–59, 297–332 |
| `SettingsSection` Advanced UI | ✅ | `SettingsSection.tsx` 60–70, 334–454 |
| Settings page categories (Trading, Risk, Alerts, Advanced) | ✅ | `Settings.tsx` 47–54, 163–166 |
| Settings API types (`Settings` interface) | ✅ | `api/settings.ts` 7–36, 38–47 |
| Mode Selector (Dashboard) | ✅ | `ModeSelector.tsx`; `Dashboard.tsx` 22–28, 74–75 |
| Mode API updates .env | ✅ | `api/routes/bot.py` 325–451 |
| Bot reads capital on start | ✅ | `api/bot_manager.py` 41–46 |
| Bot reads mode from env on start | ✅ | `api/bot_manager.py` 50–62 |
| Bot uses allocation, risk, position size | ✅ | `main.py` 353–356, 383, 445–450, 2270, 2582, 6498–6502 |
| Runtime mode helpers (paper, sandbox, API enabled, dry run) | ✅ | `main.py` 668–698, 712–723, 5775–5782 |
| Email toggle respected at send-time | ✅ | `main.py` 827–851 |
| Pending Trades approve/reject | ✅ | `PendingTradeCard.tsx` 42–67, `api/pendingTrades.ts`, `api/routes/pending_trades.py` 86–124 |
| Start / Stop / Shutdown | ✅ | `BotControls.tsx`, `api/routes/bot.py` 96–145 |

---

## 10. When changes take effect

| Change | Takes effect |
|--------|----------------|
| **Email Alerts** (Settings → Alerts) | Immediately (checked at send-time) |
| **Use margin** (Settings → Trading) | Immediately (re-read from .env at check time) |
| **Mode** (Dashboard Mode Selector or Settings → Trading modes) | On **next Start** (env updated; bot re-reads on init) |
| **Total Capital** (Settings → Trading) | On **next Start** (read in `initialize_bot_from_main`) |
| **Risk, allocation, position size, advanced** (Settings) | After **API/server restart** (read at process startup) |

---

*Generated from codebase review. Update this doc when adding or moving trading controls.*
