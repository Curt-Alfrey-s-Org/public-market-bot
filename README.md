# market-pie5-bot (public snapshot)

Intelligent trading bot with paper trading, GUI, and optional LiteLLM integration. This
repository is a **scrubbed snapshot**; see `docs/PUBLIC_SNAPSHOT.md`.

## Configure before you run

1. Copy `config/hosts.example.env` to `config/hosts.env` and set your market host and public URL (do not commit `hosts.env`).
2. Copy `.env.example` to `.env` and replace every `change-me` placeholder (database, JWT, Schwab keys, admin accounts). Never commit `.env`.
3. Merge any required lines from `env.required.example` into `.env` before production deploy.
4. Set `LITELLM_BASE_URL` to your own gateway (example: `http://192.0.2.30:8000`).

**Live trading and order schedulers are off in the shipped examples.** Use paper mode until you deliberately enable live features on your deployment.

## Run (Docker)

```bash
docker compose up -d
```

See `docs/PUBLIC_SNAPSHOT.md` and `docker-compose.yml` for ports and services.

---

# market-pie5-bot

**Workspace:** [All bots overview](../docs/BOTS_OVERVIEW.md) · [Quick reference](../docs/QUICK_REFERENCE.md)

## Shared dependency cache

This repo pulls pip and npm deps through the server-wide cache at **`/srv/dep-cache`** so containers don't redownload packages between rebuilds. `Dockerfile` and `frontend/Dockerfile` use BuildKit cache mounts with shared ids `bots-pip`, `bots-apt`, `bots-apt-lists`, `bots-npm`, shared across all bot repos. Manage with `/srv/dep-cache/bin/dep-cache {status,prune --older-than 30d,clear}`. Details: `/srv/dep-cache/README.md`.

## Production Ports (Server)

See `/home/operator/.github/PORT_ASSIGNMENTS.md` for the canonical list.

- **API host binding:** `127.0.0.1:8004`
- **Frontend host binding:** `5176:80` (optional local access)
- **Database host binding:** `127.0.0.1:5435`

Local dev uses the Vite default `5173` (not used in production).

[![Python](https://img.shields.io/
[![Raspberry Pi](https://img.shields.io/
[![Linux Mint](https://img.shields.io/
[![License](https://img.shields.io/
[![Tests](https://github.com/operator/market-pie5-bot/workflows/Tests/badge.svg)](https://github.com/operator/market-pie5-bot/actions/workflows/tests.yml)
[![Code Quality](https://github.com/operator/market-pie5-bot/workflows/Code%20Quality/badge.svg)](https://github.com/operator/market-pie5-bot/actions/workflows/lint.yml)
[![Security](https://github.com/operator/market-pie5-bot/workflows/Security%20Scan/badge.svg)](https://github.com/operator/market-pie5-bot/actions/workflows/security.yml)
[![E2E Tests](https://github.com/operator/market-pie5-bot/workflows/End-to-End%20Tests/badge.svg)](https://github.com/operator/market-pie5-bot/actions/workflows/e2e.yml)
[![Trading Bot](https://img.shields.io/
[![AI Powered](https://img.shields.io/

**An intelligent, self-scaling trading bot optimized for Raspberry Pi 5 and Linux Mint with AI-powered strategy optimization, paper trading, PDT compliance, and comprehensive GUI.**

---

## 🐧 **Platform Compatibility**

**Originally designed for Raspberry Pi 5, now fully compatible with Linux Mint and all Debian-based distributions!**

- ✅ **Raspberry Pi 5** - Optimized for ARM architecture and limited resources
- ✅ **Linux Mint** - Full desktop Linux support (20.x, 21.x, and newer)
- ✅ **Ubuntu** - Compatible with 20.04 LTS and newer
- ✅ **Debian** - Works on Debian 10+
- ✅ **Other Debian-based distros** - Pop!_OS, Elementary OS, Zorin OS, etc.

**📖 [Linux Mint Installation Guide →](LINUX_MINT_GUIDE.md)** | **[Creating Market-Mint-Bot Fork →](MARKET_MINT_BOT_GUIDE.md)**

---

## ⚠️ **DISCLAIMER - IMPORTANT LEGAL NOTICE**

**READ THIS CAREFULLY BEFORE USING THIS SOFTWARE**

### Use At Your Own Risk

This software is **EXPERIMENTAL** and provided for **EDUCATIONAL AND RESEARCH PURPOSES ONLY**. By using this software, you acknowledge and agree that:

#### No Warranty or Guarantee
- This software is provided "AS IS" without warranty of any kind, either express or implied, including but not limited to the implied warranties of merchantability and fitness for a particular purpose.
- The author makes **NO WARRANTIES**, express or implied, regarding the software's functionality, performance, accuracy, or reliability.
- There is **NO GUARANTEE** that this software will be profitable or perform as expected.

#### No Liability for Financial Losses
- The author of this software is **NOT RESPONSIBLE** for any financial losses, damages, or liabilities incurred through the use of this software.
- Trading stocks and financial instruments carries **SIGNIFICANT RISK** including the risk of complete loss of capital.
- **YOU ASSUME ALL RISKS** associated with using this software for trading.
- Past performance (backtested or simulated) does **NOT GUARANTEE** future results.

#### Experimental Software
- This is **EXPERIMENTAL SOFTWARE** under active development and may contain bugs, errors, or unintended behavior.
- The software may malfunction, execute unintended trades, or fail to execute intended trades.
- **You are solely responsible** for monitoring the software's behavior and any trades it executes.

#### No Professional Advice
- This software does **NOT** constitute financial, investment, legal, or tax advice.
- The author is **NOT** a registered financial advisor, broker, or investment professional.
- You should consult with qualified financial professionals before making any investment decisions.

#### Regulatory Compliance
- **YOU** are responsible for ensuring compliance with all applicable laws, regulations, and trading rules in your jurisdiction.
- This includes but is not limited to: Pattern Day Trading (PDT) rules, tax reporting, and brokerage account agreements.
- Failure to comply with regulations may result in account restrictions, penalties, or legal consequences.

#### User Responsibility
- By using this software, you accept **FULL RESPONSIBILITY** for:
  - All trades executed by the software
  - Configuration and settings
  - API credentials and security
  - Monitoring and oversight
  - Any resulting financial outcomes

#### License
This software is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for complete terms, including additional warranty disclaimers and liability limitations.

### ⚖️ By Using This Software, You Agree:
- ✅ You have read and understood this disclaimer
- ✅ You accept all risks associated with automated trading
- ✅ You will not hold the author liable for any losses or damages
- ✅ You will use this software responsibly and at your own risk
- ✅ You understand this is experimental software with no guarantees

**If you do not agree to these terms, DO NOT USE THIS SOFTWARE.**

---

**💡 RECOMMENDED:** Start with **paper trading mode** (`PAPER_TRADING_MODE=true`) to test the software without risking real money. Use yfinance simulation mode for learning and development.

**📋 New user?** See **[docs/INSTRUCTIONS_FOR_USERS.md](docs/INSTRUCTIONS_FOR_USERS.md)** for step-by-step instructions: start API + frontend, run the bot, where to look (Dashboard, Decision Report, Logs), performance check, and troubleshooting.

---

## 🆕 **NEW: TOS-like Stock Prioritization!**

**Bot now scans 100+ stocks and trades the best opportunities first!**

```bash
# Just enable stock screener - prioritization is automatic
ENABLE_STOCK_SCREENER=true
MAX_STOCKS_TO_SCAN=100
TOP_STOCKS_TO_TRADE=50
```

✨ **Features:**
- 🎯 **Smart Ranking** - Multi-factor scoring (momentum, volume, volatility, liquidity, sentiment)
- 📊 **TOS-like Scanning** - Scans many, trades best (just like ThinkOrSwim)
- 🥇 **Priority Trading** - Trades #1 first, then #2, #3... in order of quality
- ⚙️ **Customizable** - Adjust scoring weights to match your strategy
- 🔍 **Comprehensive** - Scans S&P 500, NASDAQ-100, and more

**📖 [Complete Prioritization Guide →](STOCK_PRIORITIZATION_GUIDE.md)**

---

## 🆕 **NEW: yfinance Simulation Mode with Auto-Fallback!**

**Bot automatically switches to yfinance simulation when Schwab API is unavailable!**

```bash
# Just run the bot - it will auto-switch to yfinance sim if needed
python3 main.py
```

✨ **Features:**
- 🔄 **Auto-fallback** to yfinance sim when Schwab API unavailable
- 📊 **Real market data** from yfinance for realistic simulations
- 📁 **Separate trade data** for sim vs real trades
- 🎓 **Perfect for learning** patterns without API credentials

**📖 [Complete yfinance Sim Guide →](YFINANCE_SIM_MODE.md)**

---

## 🆕 **Browser-Based Trading Dashboard (React + FastAPI)**

**Access the bot from any device with the modern web GUI.**

```bash
# 1. Start the API (required)
./start_api.sh
# 2. In another terminal: start the React frontend
cd frontend && npm install && npm run dev
# Open browser to http://localhost:5173
```

✨ **Features:** Dashboard • Start/Stop bot • Mode selection (yfinance, Sandbox, Live, Dry-run) • Stats • Trades • Logs • **Decision Report** • Settings • System • AI • Tax Reports

✨ **Login:** Splash screen requires sign-in. There are no built-in default accounts: set `ADMIN_USERNAME`/`ADMIN_PASSWORD` (and optionally director/user) in `.env`. Bot control (start/stop, mode, trade approval, settings writes) requires an **admin** login. See [Login/Auth](docs/LOGIN_AUTH.md).

> **Security update 2026-09-25 — do this before the next deploy** (details: [docs/LOGIN_AUTH.md](docs/LOGIN_AUTH.md), [docs/ENV_VARS.md](docs/ENV_VARS.md), placeholders in `env.required.example`):
> 1. Set `JWT_SECRET` (required in production; the API refuses to start without it).
> 2. Set `ADMIN_USERNAME`/`ADMIN_PASSWORD` (the old `admin/admin123`, `user/user123` defaults are gone).
> 3. Rotate `BOT_API_KEY` (the old one was built into the frontend bundle) and delete `VITE_API_KEY` from `.env`.
> 4. Set `LITELLM_API_KEY` (and keep `LITELLM_ENABLED=true`) so the bot can start with `BOT_REQUIRE_BRAIN=true`.
> 5. Rebuild the frontend image and recreate the containers: `docker compose --env-file .env up -d --build`.
>
> **Follow-up (same day):**
> - `GET /api/settings` masks third-party API keys (`********`). Set or rotate those keys in `.env`, not in the GUI.
> - In Docker, mode and settings changes made in the GUI are saved only if `BOT_RUNTIME_ENV_FILE` is set, e.g. `BOT_RUNTIME_ENV_FILE=/app/data/runtime.env` (on the mounted `./data` volume). Otherwise they last until the API restarts. Host installs keep using `.env`.
> - The API image now includes `web_scrapers/`, so earnings, macro, sentiment, options-flow and news filters become active in the container after the rebuild.
> - Operator scripts (`scripts/probe_all_modes.sh`, `scripts/monitor_bot.py`, `scripts/yfinance_long_run.py`, `scripts/yfinance_mode_optimizer.py`, `scripts/latency_probe.py`, `scripts/load_test_probe.py`) need `MARKET_BOT_ADMIN_TOKEN`, or `MARKET_BOT_ADMIN_USERNAME`/`MARKET_BOT_ADMIN_PASSWORD`.
> - `POST /api/assets/upload` (GUI asset upload) needs an **admin** login.
> - The old committed UI build in `api/static/` was removed. The UI is served by the frontend container (port 5176 / the tunnel), so nothing changes there; the API port itself now returns a JSON banner at `/` and 404 for other non-API paths.

✨ **Stack:** FastAPI backend (default port **8002**; do not use 8000 — reserved for Yacht) + React + TypeScript + Tailwind • Real-time polling • Responsive layout

**📖 [Migration Guide (React default) →](docs/MIGRATION_REACT_GUI.md)** | **[Phase 8 Test Plan →](docs/PHASE8_TEST_PLAN.md)** | **[Login/Auth →](docs/LOGIN_AUTH.md)** | **[Visual Enhancements →](assets/README.md)**

---

## 🆕 **NEW: Manual Start Confirmation!**

**Bot now requires explicit user confirmation before trading!**

```bash
# CLI Mode - Type 'START' when prompted
python3 main.py
# ... configuration review ...
Type 'START' to begin trading: START

# Web GUI - Start API + frontend, then click Start in dashboard
./start_api.sh   # then: cd frontend && npm run dev → open http://localhost:5173
# Click Start button when ready
```

✨ **Features:**
- 🛡️ **No Auto-Trading** - Bot never trades until you explicitly confirm
- ⚙️ **Immediate Settings** - Web GUI applies current settings on start (no restart)
- 📋 **Full Control** - Review configuration before trading begins
- 🎯 **Safe Testing** - Cancel at any time before trading starts

**📖 [Complete Manual Start Guide →](MANUAL_START_GUIDE.md)**

---

**#TradingBot #RaspberryPi #AlgorithmicTrading #Python #AI #MachineLearning #StockTrading #FinTech #AutomatedTrading #PaperTrading #SchwabAPI #ALFaAI #LiteLLM #TechnicalAnalysis #QuantTrading #RaspberryPi5 #OpenSource #InvestmentAutomation #DayTrading #SwingTrading #WebDashboard**

---

## 🆕 **NEW: Fully Integrated AI/ML System!**

**All advanced AI/ML tools are now fully integrated and working together!**

### ✅ **ML Signal Filter**
- Filters trading signals before execution
- Trained Random Forest model predicts signal quality
- **Impact:** +5-10% win rate improvement

### ✅ **Portfolio Optimizer**
- Modern Portfolio Theory for position sizing
- Optimized allocation across symbols
- **Impact:** +10-15% risk-adjusted returns

### ✅ **Adaptive Learning**
- Q-Learning and Multi-Armed Bandit
- Learns from trade outcomes
- Adapts strategy weights over time
- **Impact:** Continuous improvement

### ✅ **Real-Time Parameter Optimization**
- Backtest **heuristics** optimize parameters during trading (not LLM)
- Applied at runtime when `BOT_ENABLE_AI_AUTO_TWEAK=true` (default: off)
- **Impact:** Data-driven nudges within documented param ranges

### ✅ **Performance Caching**
- Reduces redundant computation
- Faster execution
- **Impact:** Better efficiency

**📖 [Complete Integration Guide →](docs/INTEGRATION_COMPLETE.md)** | **[User Guide →](docs/USER_GUIDE.md)**

**Tool Utilization: ~95% (up from ~60%)**

---

## 📍 Project Status & Roadmap

**🚀 New to the project? Contributing? Want to know what's next?**

**Quick Links:**
- **[🎯 MISSION.md](MISSION.md)** - Bot mission: Phase 1 (stocks buy/short) → Phase 2 (options)
- **[🖥️ DEV_DEPLOY_WORKFLOW.md](DEV_DEPLOY_WORKFLOW.md)** - Build on Windows → run on Linux Mint (python3, venv)
- **[📋 ROADMAP.md](ROADMAP.md)** - Active development, TODO list, and quarterly plans
- **[📊 PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current state, completed features, and priorities
- **[📚 docs/](docs/)** - Organized documentation and guides
- **[🤝 CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute

**See these docs for:**
- 🎯 **Mission:** Stocks (buy + short) first, then options; production readiness tied to Phase 1
- 🖥️ **Dev/deploy:** Edit on Windows, push to GitHub, pull and run on Linux Mint (`python3` in venv); `.gitattributes` for LF
- ✅ What's completed (spoiler: a lot!)
- 🔧 What needs work and development priorities
- 📋 How to contribute and where to start
- 🗺️ Project roadmap and future vision

## ⚡ Performance Benchmarks

**Want to know how fast the bot is? Running 500+ symbols? Optimizing for Pi 5?**

**[👉 See PERFORMANCE_BENCHMARKS.md](PERFORMANCE_BENCHMARKS.md)** for:
- 📊 Complete benchmark results (10 to 1,000 symbols)
- 🎯 TRADING_FREQUENCY tuning guide
- 🔧 Resource throttling configuration
- 🚀 Raspberry Pi 5 optimization tips
- 🐛 Performance troubleshooting guide

**Quick Stats:**
- ⚡ 500 symbols: ~6ms per iteration (~105,000 symbols/sec)
- 🎯 Well optimized for Raspberry Pi 5
- 📈 Linear scaling up to 1,000+ symbols

---

## 📚 Documentation Navigation

**📖 [Complete Documentation Index](DOCUMENTATION_INDEX.md)** - Central hub for all documentation
**🐛 [Known Issues & Limitations](KNOWN_ISSUES.md)** - Current bugs and workarounds

### 🎯 Getting Started
- **[docs/INSTRUCTIONS_FOR_USERS.md](docs/INSTRUCTIONS_FOR_USERS.md)** - **What to do now** — start API + frontend, run the bot, where to look, performance check, troubleshooting
- **[README.md](README.md)** (this file) - Project overview and quick start
- **[USER_GUIDE.md](USER_GUIDE.md)** - Complete user guide for all features
- **[WEB_GUI_QUICKSTART.md](WEB_GUI_QUICKSTART.md)** - Quick start for web interface (legacy Dash; current UI: start_api.sh + React frontend — see [docs/INSTRUCTIONS_FOR_USERS.md](docs/INSTRUCTIONS_FOR_USERS.md))
- **[MANUAL_START_GUIDE.md](MANUAL_START_GUIDE.md)** - Safe trading start procedures

### 🔧 Setup & Configuration
- **[DESKTOP_ICONS_GUIDE.md](DESKTOP_ICONS_GUIDE.md)** - Desktop integration for Raspberry Pi
- **[TOKEN_ENCRYPTION_GUIDE.md](TOKEN_ENCRYPTION_GUIDE.md)** - Secure token storage
- **[ENV_CONFLICT_CHECKER_GUIDE.md](ENV_CONFLICT_CHECKER_GUIDE.md)** - Environment variable troubleshooting
- **[SANDBOX_LIVE_DISTINCTION.md](SANDBOX_LIVE_DISTINCTION.md)** - Understanding trading modes
- **[EMAIL_ALERTS_GUIDE.md](EMAIL_ALERTS_GUIDE.md)** - Email notification setup (NEW! ✅)
- **[BRANCH_PROTECTION_GUIDE.md](BRANCH_PROTECTION_GUIDE.md)** - Prevent premature PR merges (NEW! ✅)

### 📈 Trading Features
- **[TRADING_ENHANCEMENTS_GUIDE.md](TRADING_ENHANCEMENTS_GUIDE.md)** - Advanced trading strategies and order types
- **[BACKTESTING_GUIDE.md](BACKTESTING_GUIDE.md)** - Strategy testing and validation
- **[LIVE_MODE_GUIDE.md](LIVE_MODE_GUIDE.md)** - Live trading setup and safety
- **[STOCK_SCREENER_GUIDE.md](STOCK_SCREENER_GUIDE.md)** - Stock selection and filtering
- **[YFINANCE_SIM_MODE.md](YFINANCE_SIM_MODE.md)** - Simulation mode documentation

### 🤖 AI & Machine Learning
- **✅ [ML_AND_AI_ARCHITECTURE.md](docs/ML_AND_AI_ARCHITECTURE.md)** - **Canonical** ML vs ALFa AI layers, 2026 changes and why
- **✅ [ALFA_AI_HOW_TO_USE.md](docs/ALFA_AI_HOW_TO_USE.md)** - LiteLLM, Ask AI, AI Monitor, agentic jobs
- **✅ [ENV_VARS.md](docs/ENV_VARS.md)** - ALFa AI / brain-gate environment variables
- **✅ [INTEGRATION_COMPLETE.md](docs/INTEGRATION_COMPLETE.md)** - All ML tools integrated in the trading loop
- **✅ [USER_GUIDE.md](docs/USER_GUIDE.md)** - Complete guide covering all integrations
- **✅ [EMAIL_ALERT_SETUP.md](docs/EMAIL_ALERT_SETUP.md)** - Email alert system setup
- **[ADAPTIVE_LEARNING_GUIDE.md](ADAPTIVE_LEARNING_GUIDE.md)** - Reinforcement learning & adaptive models
- **[ADAPTIVE_MODELS_ANALYSIS.md](ADAPTIVE_MODELS_ANALYSIS.md)** - Analysis of adaptive learning approach
- **[ML_GUIDE.md](ML_GUIDE.md)** - Local ML signal filtering (scikit-learn, VADER, Q-learning)
- **[AI_IMPROVEMENTS_GUIDE.md](AI_IMPROVEMENTS_GUIDE.md)** - Parameter tuning (heuristic optimizer; historical LLM notes)
- **[SENTIMENT_PORTFOLIO_GUIDE.md](SENTIMENT_PORTFOLIO_GUIDE.md)** - Sentiment analysis

### 🖥️ User Interface
- **[WEB_GUI_GUIDE.md](WEB_GUI_GUIDE.md)** - Complete web GUI documentation
- **[GUI_SETTINGS_GUIDE.md](GUI_SETTINGS_GUIDE.md)** - Settings panel guide
- **[SHUTDOWN_BUTTON_GUIDE.md](SHUTDOWN_BUTTON_GUIDE.md)** - Safe shutdown procedures
- **[BETTER_SIM_MIMIC_GUIDE.md](BETTER_SIM_MIMIC_GUIDE.md)** - Simulation improvements

### 👨‍💻 Development
- **[ROADMAP.md](ROADMAP.md)** - 📋 **TODO list, active tasks, and quarterly plans**
- **[docs/PRODUCTION_READINESS_AND_REACT_NATIVE.md](docs/PRODUCTION_READINESS_AND_REACT_NATIVE.md)** - 🚀 **NEW!** Server production gaps, mobile API setup, and React Native (Expo) conversion guide
- **[docs/API_RELIABILITY.md](docs/API_RELIABILITY.md)** - 🔄 **NEW!** Phase 1.1 Startup Recovery & Phase 1.2 API Retry Logic (automatic data initialization, exponential backoff, cache fallback)
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current state and priorities
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- **[VERIFICATION_GUIDE.md](VERIFICATION_GUIDE.md)** - Testing and validation
- **[CHANGELOG.md](CHANGELOG.md)** - Version history
- **[COPILOT_DEBUG_LOGGING.md](COPILOT_DEBUG_LOGGING.md)** - Debug logging for bot analysis (NEW! ✅)

### 📂 Additional Resources
- **[docs/](docs/)** - Organized documentation directory
- **[docs/ARCHIVE.md](docs/ARCHIVE.md)** - Historical implementation notes and fix summaries
- **[ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)** - Feature overview
- **[COMPETITIVE_ANALYSIS.md](COMPETITIVE_ANALYSIS.md)** - Comparison with other bots
- **[SECURITY.md](SECURITY.md)** - 🔒 **Security policy, vulnerability reporting, and best practices**
- **[DATA_PRIVACY.md](DATA_PRIVACY.md)** - Privacy and security information
- **[WHATS_NEW.md](WHATS_NEW.md)** - Recent updates

**💡 Tip:** All 87 historical summary and fix documents have been moved to [docs/archive/](docs/archive/) to keep the root directory clean. See [docs/ARCHIVE.md](docs/ARCHIVE.md) for the complete index.

---

## 🔍 Key Features & Topics

### 🌐 **NEW: Browser-Based Trading Dashboard**
The bot now includes a **modern web GUI** accessible from any device! [Quick Start →](#web-based-gui-mode-new--recommended)

**✨ Core Features:**
- 📊 **Real-time interactive charts** (Plotly-powered)
- 📱 **Access from any device** (PC, tablet, phone)
- 💻 **Integrated terminal** with live log output
- 🎯 **Point-and-click controls** (no command-line needed)
- 📈 **Live statistics dashboard** with performance metrics
- ⚙️ **Settings panel** for easy configuration

**🎨 NEW: Node.js-Powered Visual Enhancements:**
- ✨ **Modern CSS Animations** - Smooth fade-in, slide-in, pulse, and scale effects
- 🎭 **Interactive Elements** - Ripple effects on clicks, card hover states
- 📊 **Enhanced Charts** - Chart.js integration with date adapters
- 🎨 **Icon Library** - Font Awesome icons for professional look
- 💫 **Loading Animations** - Shimmer and skeleton loading states
- 🌊 **Glassmorphism Effects** - Modern translucent card styling
- 🎯 **Tooltips & Badges** - Enhanced visual feedback
- 📱 **Responsive Grid** - Optimized layouts for all screens
- ♿ **Accessibility** - Reduced motion support, focus states

**Quick Start:**
```bash
./start_api.sh   # then: cd frontend && npm run dev → open http://localhost:5173
```
**📖 [Complete Web GUI Guide →](WEB_GUI_QUICKSTART.md)** | **[Visual Enhancements →](assets/README.md)**

---

**GitHub Topics/Tags:** `trading-bot` `algorithmic-trading` `raspberry-pi` `python` `ai` `machine-learning` `stock-trading` `fintech` `automated-trading` `paper-trading` `schwab-api` `huggingface` `technical-analysis` `quantitative-trading` `raspberry-pi-5` `investment-automation` `day-trading` `swing-trading` `trading-algorithms` `financial-analysis` `api-trading` `risk-management` `backtesting` `portfolio-management` `web-dashboard` `plotly-dash`

**Keywords:** Trading Bot, Algorithmic Trading, Quantitative Trading, Automated Stock Trading, Raspberry Pi Trading Bot, AI Trading, Pattern Day Trading (PDT), Paper Trading Simulator, Self-Scaling Algorithm, Trailing Stop Loss, Risk Management, Schwab API Integration, ALFa AI, LiteLLM, Technical Analysis, Financial Automation, Resource Monitoring, Real-time Trading, Trading Strategy Optimization, Market Analysis, Investment Bot, Web Dashboard, Browser GUI

---

## 🆕 New: Stock Trading Enhancements

**The bot now includes professional-grade trading tools and strategies!**

### **Trading Strategies** (5 Built-in Strategies)
- ✅ **SMA Crossover** - Momentum trading with moving average crossovers (Golden/Death Cross)
- ✅ **Bollinger Bands** - Mean reversion strategy for identifying overbought/oversold conditions
- ✅ **RSI Strategy** - Relative Strength Index for overbought/oversold signals
- ✅ **MACD Strategy** - Moving Average Convergence Divergence for trend following
- ✅ **Momentum Strategy** - Rate of change momentum trading
- ✅ **Strategy Manager** - Combine multiple strategies with weighted signals for robust trading

### **Technical Indicators** (with optional pandas-ta support)
- RSI, MACD, SMA/EMA, Bollinger Bands, ATR, ADX, Stochastic Oscillator
- Automatic signal interpretation (overbought/oversold detection)
- Built-in manual calculations with optional pandas-ta support (requires Python >=3.12)

### **Data Integration**
- ✅ **yfinance** - Real-time and historical price data
- ✅ **Alpha Vantage** - Fundamental data (P/E ratios, earnings, ROE, profit margins, etc.)
- Built-in caching to reduce API calls
- Comprehensive fundamental analysis with buy/sell recommendations

### **Advanced Risk Management**
- Position sizing: Fixed risk, percentage of capital, Kelly Criterion
- Risk/reward ratio calculations
- Portfolio risk assessment
- Value at Risk (VaR) and Sharpe Ratio
- Maximum drawdown analysis

### **Enhanced Backtesting**
- ✅ **Backtrader** integration for realistic backtesting
- Built-in backtesting with rolling metrics
- Baseline comparison (buy-and-hold)
- Comprehensive performance analytics

### **Advanced Order Types** (NEW!)
- ✅ **Market Orders** - Immediate execution at current price
- ✅ **Limit Orders** - Execute at specified price or better
- ✅ **Stop Orders** - Trigger market order at stop price
- ✅ **Stop-Limit Orders** - Trigger limit order at stop price
- ✅ **Trailing Stop Orders** - Dynamic stops that follow price
- ✅ **OCO Orders** - One-Cancels-Other for profit/loss pairs
- ✅ **Bracket Orders** - Entry with automatic profit target and stop loss

### **Sentiment Analysis & Portfolio Optimization** (NEW! 🚀)
- ✅ **Sentiment Analysis** - News-based sentiment filtering with NewsAPI and Finnhub
  - VADER and TextBlob sentiment scoring
  - Automatic filtering of stocks with negative sentiment
  - Sentiment-based trading signals (BULLISH/BEARISH/NEUTRAL)
  - Smart caching to reduce API calls
  - **Built-in rate limiting** to prevent 429 errors and stay within API quotas
- ✅ **Portfolio Optimization** - Modern Portfolio Theory (MPT) implementation
  - Maximum Sharpe Ratio optimization
  - Minimum Variance portfolios
  - Risk Parity allocation
  - Correlation analysis and diversification scoring
  - Efficient frontier calculation
  - Automated rebalancing suggestions

**📖 [Complete Guide & Tutorials →](TRADING_ENHANCEMENTS_GUIDE.md)** | **[Sentiment & Portfolio Guide →](SENTIMENT_PORTFOLIO_GUIDE.md)** | **[Rate Limiting Guide →](RATE_LIMITING_GUIDE.md)** | **[Competitive Analysis →](COMPETITIVE_ANALYSIS.md)**

---

## 🆕 New: Dynamic Stock Screener

**The bot now dynamically discovers tradeable stocks instead of using preloaded lists!**

### **Key Features**
- 🔍 **Dynamic Discovery** - Automatically fetches 500+ stocks from S&P 500, NASDAQ-100, and Dow Jones
- ⚡ **Fast Screening** - Checks up to 200 stocks in ~2 seconds (TOS-like performance)
- 🎯 **Smart Filtering** - Filters by price range, volume, and volatility from your `.env` settings
- 💾 **Intelligent Caching** - 24-hour universe cache, 5-minute screening cache
- 🔄 **No API Keys** - Uses free Wikipedia tables via pandas
- 📊 **Fallback Support** - 160+ stock fallback when Wikipedia unavailable

### **Configuration**
```bash
# Enable in .env
ENABLE_STOCK_SCREENER=true
MAX_DISCOVERED_STOCKS=10

# Customize filtering
MIN_STOCK_PRICE=5.0              # Minimum stock price
MAX_STOCK_PRICE=1000.0           # Maximum stock price
MIN_DAILY_VOLUME=500000          # Minimum daily volume
MAX_STOCK_VOLATILITY=0.15        # Maximum volatility (15%)
```

### **Before vs After**
| Before | After |
|--------|-------|
| ❌ Limited to 2 hardcoded stocks in scan_symbols.txt | ✅ 500+ stocks dynamically from S&P 500, NASDAQ-100, etc. |
| ❌ Manual updates required | ✅ TOS-like automatic discovery based on criteria |
| ❌ Static scan_symbols.txt file required | ✅ scan_symbols.txt optional (fallback only) |
| ❌ No filtering by criteria | ✅ Real-time filtering by price, volume, volatility |

**📖 [Complete Stock Screener Guide →](STOCK_SCREENER_GUIDE.md)**

---

## 🔐 Enhanced Security Features (NEW!)

**The bot now includes enterprise-grade security for protecting your OAuth tokens!**

### **Token Encryption**
- 🔒 **Fernet Encryption** - AES-128 symmetric encryption for token.json
- 🔐 **HMAC Integrity Checks** - SHA-256 HMAC to detect file corruption or tampering
- 🔑 **Multiple Key Sources** - Environment variables or secure key files
- 🔄 **Backward Compatible** - Works with both encrypted and plain tokens

### **Security Enhancements**
- 🛡️ **Log Masking** - Sensitive information (URLs, tokens) masked in logs
- 📝 **Tamper Detection** - HMAC verification prevents unauthorized modifications
- 🔐 **Secure Storage** - Tokens encrypted at rest on disk
- 🎯 **Key Rotation** - Support for periodic encryption key rotation

### **Quick Setup**
```bash
# Generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env file
SCHWAB_TOKEN_ENCRYPTION_KEY=your_generated_key_here
```

**📖 [Complete Security Guide →](TOKEN_ENCRYPTION_GUIDE.md)**

---

## Setup

### Schwab API Key Setup

To use this bot with Schwab's API, you need to obtain API credentials:

**Step-by-Step Schwab API Setup:**

1. **Go to developer.schwab.com** and sign in with your Schwab account
2. **Register your application:**
   - Navigate to the "My Apps" section
   - Click "Create New App"
   - Select application type: "Personal" (for individual trading)
   - Select required scopes: Enable "Trading" scopes for order placement
3. **Get your API credentials:**
   - **API Key**: Your application/consumer key (displayed after app creation)
   - **App Secret**: Your application secret (save this immediately, shown only once)
   - **Callback URL**: Set to `https://127.0.0.1:8182` (IMPORTANT: must be HTTPS with this exact port)
4. **Note your Schwab Account ID:**
   - Find this in your Schwab account dashboard
   - Usually an 8-digit account number
5. **First-time OAuth Login:**
   - When you first run the bot, a browser window will open automatically
   - Log in to your Schwab account and authorize the app
   - The bot will save your OAuth token to `token.json` for future use
   - Token is valid for 7 days and automatically refreshes while the bot is running
6. **Choose your testing environment:**
   - **Sandbox Mode (Recommended for Testing)**: Uses Schwab's sandbox environment with real-time API calls but simulated trading
   - **ThinkorSwim paperMoney**: Traditional paper trading platform with CSV export capability
   - **Pure Simulation**: Random price generation without API calls

**Important Notes About OAuth Authentication:**

- The bot now uses **OAuth 2.0** authentication via the `schwab-py` library
- On first run, you'll need to complete an interactive login via browser
- Your credentials are stored securely in `token.json` (never commit this file!)
- The token automatically refreshes, so you won't need to log in again for 7 days
- For headless/server deployments, complete the OAuth flow once on a desktop machine, then copy `token.json` to your server

#### Sandbox Mode Setup (Recommended)

Schwab's sandbox environment provides a production-like experience for testing:

- **Real-time market data** from Schwab's market data API
- **Simulated order execution** without using real money
- **Full API feature parity** with production environment
- **Rate limiting** similar to production (for realistic testing)
- **API connectivity required** - will not fall back to random prices

To enable sandbox mode:

1. Set `SCHWAB_SANDBOX_MODE=true` in your `.env` file
2. Keep `PAPER_TRADING_MODE=true` for testing
3. Configure your Schwab API credentials as usual
4. The bot will automatically use sandbox endpoints

**Important: Sandbox Mode Behavior**

When sandbox mode is enabled, the bot **requires** API connectivity:
- ✅ Bot will attempt to fetch prices from Schwab sandbox API
- ❌ If Schwab sandbox fails, bot will **STOP IMMEDIATELY** (NO fallback)
- ❌ Bot will **NOT** fall back to yfinance or random/simulated prices
- ❌ Bot will raise a **CRITICAL ERROR** if Schwab API fails
- ✅ Startup validation checks API connectivity before trading

This ensures sandbox testing uses realistic market data and behaves like production. Any API failure is treated as a critical error that must be fixed before continuing.

**Sandbox vs. Simulation Mode:**

| Feature | Sandbox Mode | Simulation Mode |
|---------|--------------|-----------------|
| Market Data | Real-time from Schwab API ONLY | Random or yfinance |
| Order Execution | Schwab sandbox API | Simulated locally |
| API Required | Yes (CRITICAL ERROR if unavailable) | No (can use random prices) |
| Fallback Behavior | STOPS IMMEDIATELY if API fails | Uses random prices |
| Rate Limits | Yes (realistic) | No |
| Latency Testing | Yes (realistic) | No |
| API Errors | Yes (realistic) | No |
| Best For | Pre-production testing | Quick algorithm testing |

**Why Sandbox Requires API:**

In sandbox mode, the bot is testing API integration and should behave like production.
If the API fails, the bot should **fail**, not silently continue with fake data.
This helps identify API issues early, before live trading.

#### ThinkorSwim paperMoney Integration

For traditional paper trading with ThinkorSwim:

- Open ThinkorSwim platform and switch to paperMoney mode
- Execute test trades in the paper trading environment
- Export position data: Go to Monitor > Account Statement > Export to CSV
- Save the CSV file (e.g., `positions.csv`) for simulation testing
- Import into bot using `bot.import_tos_csv('positions.csv')`

Once you have your credentials, copy `.env.example` to `.env` and fill in your actual values:

```bash
cp .env.example .env
```

Then edit `.env` with your credentials:
- `SCHWAB_API_KEY`: Your application key (from step 3)
- `SCHWAB_APP_SECRET`: Your application secret (from step 3)
- `SCHWAB_CALLBACK_URL`: Your redirect URI (MUST be `https://127.0.0.1:8182`)
- `SCHWAB_TOKEN_PATH`: Path to store OAuth token (default: `token.json`)
- `SCHWAB_ACCOUNT_ID`: Your account number (from step 4)
- `SCHWAB_API_ENABLED`: Set to `on`/`true` to enable Schwab API, `off`/`false` to disable (default: `on`)
- `SCHWAB_SANDBOX_MODE`: Set to `true` for sandbox testing, `false` for production
- `PAPER_TRADING_MODE`: Set to `true` for paper/sandbox trading, `false` for live trading
- `LITELLM_ENABLED`: Enable AI features via the ALFa AI brain (LiteLLM). See `docs/ENV_VARS.md`
- `LITELLM_BASE_URL`: ALFa AI LiteLLM proxy URL (default: `http://192.0.2.30`)
- `LITELLM_API_KEY`: This bot's LiteLLM key (env only). Required to start the bot while `BOT_REQUIRE_BRAIN=true`
- `JWT_SECRET`: Session-token signing secret. **Required in production** (see `docs/LOGIN_AUTH.md`)
- `BOT_RISK_THRESHOLD`: Risk threshold (default: 0.02)
- `BOT_MIN_ALLOCATION`: Minimum allocation amount (default: 100)
- `BOT_MAX_ALLOCATION`: Maximum allocation amount (default: 5000)
- `BOT_TRAILING_STOP_PERCENT`: Trailing stop percentage (default: 0.03 = 3%)
- `SCAN_SYMBOLS_FILE`: Path to static symbol file (default: scan_symbols.txt) - **RARELY USED** (only when ENABLE_STOCK_SCREENER=false)

**Stock Discovery Configuration (TOS-like - RECOMMENDED)**

The bot uses **ThinkOrSwim (TOS)-like dynamic stock discovery by default**:

```bash
# Enable stock discovery (default: true)
ENABLE_STOCK_SCREENER=true

# Maximum number of stocks to discover (default: 10)
MAX_DISCOVERED_STOCKS=10

# Screening criteria (filters stocks)
MIN_STOCK_PRICE=5.0          # Minimum stock price (avoid penny stocks)
MAX_STOCK_PRICE=1000.0       # Maximum stock price (avoid very expensive stocks)
MIN_DAILY_VOLUME=500000      # Minimum daily trading volume
MAX_STOCK_VOLATILITY=0.15    # Maximum volatility (15%)
```

**When ENABLE_STOCK_SCREENER=true:**
**When ENABLE_STOCK_SCREENER=true (DEFAULT - RECOMMENDED):**

- ✅ **TOS-like dynamic discovery** from S&P 500, NASDAQ-100, Dow Jones, etc.
- ✅ **Smart filtering** based on price, volume, and volatility
- ✅ **Real-time screening** using yfinance data
- ✅ **Quality ranking** (momentum, volume, liquidity, sentiment)
- ✅ **Automatic daily refresh** (24-hour cache)
- ⚠️ **Note**: Falls back to popular stocks or scan_symbols.txt if screening unavailable

**When ENABLE_STOCK_SCREENER=false:**
- ✅ Uses symbols from `scan_symbols.txt` file only (static list)
- ✅ Full manual control over traded symbols
- ✅ Lower API usage (no yfinance calls for discovery)
- ⚠️ **Note**: Requires manual symbol management

**Benefits:**
1. **Dynamic Trading**: Find new opportunities automatically
2. **Risk Management**: Filter out unsuitable stocks
3. **Diversification**: Trade multiple stocks from different sectors
4. **Automation**: No manual symbol list maintenance

**NEW: SCHWAB_API_ENABLED Toggle**

You can now easily enable/disable Schwab API connectivity without changing credentials:

```bash
# Disable Schwab API (use yfinance for data)
SCHWAB_API_ENABLED=off

# Enable Schwab API (default)
SCHWAB_API_ENABLED=on
```

**When SCHWAB_API_ENABLED=off:**
- ✅ **No Schwab API connection attempts** (reduces log entries)
- ✅ **Uses yfinance for market data** (real prices)
- ✅ **Runs simulation trades** to learn patterns and improve predictions
- ✅ **Perfect for troubleshooting** without API credentials
- ✅ **Great for development** and testing strategies
- ✅ **Useful for learning mode** from historical data
- ⚠️ **Cannot be used in live trading mode** (PAPER_TRADING_MODE=false)

**Benefits:**
1. **Troubleshooting**: Test without credentials, no need to remove API keys
2. **Reduced Logs**: No connection errors when API is intentionally off
3. **Learning Mode**: Train strategies using yfinance historical data
4. **Development**: Faster iteration without API setup

## Installation

### Quick Install from Release (Recommended)

Download the latest stable release from the [Releases page](https://github.com/operator/market-pie5-bot/releases):

```bash
# Download the latest release
wget https://github.com/

# Extract the archive
tar -xzf market-pie5-bot-v1.0.0.tar.gz
cd market-pie5-bot

# Create virtual environment and install dependencies
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# You're ready to go!
./start_api.sh
# In another terminal: cd frontend && npm install && npm run dev → open http://localhost:5173
```

**Benefits of installing from releases:**
- ✅ Stable, tested versions
- ✅ Semantic versioning (v1.x.x)
- ✅ Release notes with changelog
- ✅ No development files or clutter

### Installation on Raspberry Pi 5

#### Prerequisites: GitHub Authentication (Private Repositories Only)

**Note:** If this repository is public, you can skip this section entirely - GitHub authentication is not required for public repositories. You can proceed directly to the [Step-by-Step Install](#step-by-step-install) section below.

**For private repositories only:** You'll need to authenticate with GitHub to download files and clone the repository. Follow these steps to create a GitHub Personal Access Token (PAT):

1. **Create a GitHub Personal Access Token:**
   - Go to [GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)](https://github.com/settings/tokens)
   - Click "Generate new token" → "Generate new token (classic)"
   - Give your token a descriptive name (e.g., "market-pie5-bot-install")
   - Set an expiration date (recommended: 90 days or custom)
   - Select the following permissions:
     - ✓ `repo` (Full control of private repositories)
   - Click "Generate token" at the bottom
   - **IMPORTANT:** Copy the token immediately - you won't be able to see it again!
   - Save the token securely (e.g., in a password manager)

2. **Set up your token for command-line access:**

```bash
# Store your token in a variable for easy use (replace YOUR_TOKEN with your actual token)
export GITHUB_TOKEN=YOUR_TOKEN
```

**Security Note:** This stores the token in your current shell session only. The token will be lost when you close the terminal. Never commit tokens to code or store them in shell history files.

#### Step-by-Step Install

1. **Download and run the installation script:**

**For public repositories:**
```bash
# Download using curl (for public repos)
curl -o install.sh \
     https://raw.githubusercontent.com/operator/market-pie5-bot/main/install.sh

# Or using wget (alternative for public repos)
wget -O install.sh \
     https://raw.githubusercontent.com/operator/market-pie5-bot/main/install.sh
```

**For private repositories only:**
```bash
# Method 1: Download using curl with authentication (for private repos only)
curl -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -o install.sh \
     -L https://api.github.com/repos/operator/market-pie5-bot/contents/install.sh

# Method 2: Download using wget with authentication (alternative for private repos)
wget --header="Authorization: token $GITHUB_TOKEN" \
     --header="Accept: application/vnd.github.v3.raw" \
     -O install.sh \
     https://api.github.com/repos/operator/market-pie5-bot/contents/install.sh
```

**For all repositories (public and private):**
```bash
# Review the script content before executing (recommended)
cat install.sh

# Make it executable
chmod +x install.sh

# Run the installation
./install.sh
```

**Note for private repositories:** When the install script runs `git clone`, you'll be prompted for your GitHub username and password. Use your GitHub username and the Personal Access Token (not your GitHub password) when prompted. Public repositories do not require authentication.

#### 🆕 Enhanced Installation Features

The install script now includes optional interactive features:

**1. Desktop Icons Installation**
- Automatically installs application menu shortcuts
- Adds "Market Pie5 Web Dashboard" and "Market Pie5 Bot (Desktop GUI)" to your application menu
- Icons appear in Finance/Office categories
- Paths automatically configured for your installation directory
- Prompted during installation (optional)

**2. ClamAV Security Scanning with Unattended Updates**
- Installs ClamAV antivirus and malware detection
- Configures automatic virus definition updates via freshclam
- Updates run hourly in the background
- Provides system-wide protection against threats
- Prompted during installation (optional)

**Example Installation Flow:**
```bash
./install.sh
# ... (standard installation steps)

# Desktop Icons prompt:
Install desktop icons? (y/n): y
✓ Web GUI desktop icon installed
✓ Desktop GUI icon installed
✓ Desktop database updated

# ClamAV Security prompt:
Install ClamAV with automatic updates? (y/n): y
✓ ClamAV installed successfully
✓ Automatic virus definition updates enabled
✓ freshclam service is running
```

**Manual Installation Options:**
```bash
# Install desktop icons separately
./install_desktop_icons.sh

# Install ClamAV manually
sudo apt install clamav clamav-daemon clamav-freshclam -y
sudo systemctl enable clamav-freshclam
sudo systemctl start clamav-freshclam

# Check ClamAV status
sudo systemctl status clamav-freshclam

# Scan a directory
clamscan -r /path/to/directory
```

📖 **See also:** [DESKTOP_ICONS_GUIDE.md](DESKTOP_ICONS_GUIDE.md) for detailed desktop integration information.

Alternatively, you can manually run all installation steps:

```bash
#!/bin/bash
# Update system packages
sudo apt update -y
sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git -y

# Clone the repository (you'll be prompted for username and token)
git clone https://github.com/operator/market-pie5-bot.git

# Enter the repository directory
cd market-pie5-bot

# Create virtual environment
python3 -m venv venv

# Install Python dependencies in virtual environment
./venv/bin/pip install -r requirements.txt

echo "Setup complete. Edit .env with keys."
```

**Alternative: Configure Git to Cache Your Credentials**

To avoid entering your token repeatedly, you can configure Git to cache your credentials:

```bash
# Cache credentials for 1 hour (3600 seconds) - RECOMMENDED
git config --global credential.helper 'cache --timeout=3600'

# Or store credentials permanently - NOT RECOMMENDED
# WARNING: This stores your token in plain text in ~/.git-credentials
# git config --global credential.helper store
```

**Security Warning:** The `cache` option stores credentials in memory temporarily and is relatively safe. The `store` option saves your token unencrypted to `~/.git-credentials` on disk, which is a security risk. Only use `store` if you understand the implications.

2. **Configure environment variables:**

After installation, create a `.env` file in the repository root:

```bash
cd market-pie5-bot
cp .env.example .env
```

Edit the `.env` file with your API keys and configuration settings.

3. **You're ready to go!**

The setup is now complete and you can start using the bot.

### Manual Installation

If not using the Raspberry Pi install script, install the required dependencies:

```bash
# Create a virtual environment
python3 -m venv venv

# Install Python dependencies in the virtual environment
./venv/bin/pip install -r requirements.txt

# Install Node.js dependencies for enhanced web GUI visuals
npm install
```

**Note:** Node.js dependencies are optional but highly recommended for the best visual experience with the web GUI. They include:
- `animate.css` - Modern CSS animations
- `chart.js` - Enhanced charting capabilities
- `@fortawesome/fontawesome-free` - Professional icon library

If you don't have Node.js installed:
```bash
# On Raspberry Pi or Debian/Ubuntu
sudo apt update
sudo apt install nodejs npm

# Verify installation
node --version
npm --version
```

## Usage

### 🌐 Web-Based GUI Mode (⭐ RECOMMENDED)

**The easiest way to use the bot!** Access a modern React + FastAPI trading dashboard from any browser.

#### Quick Start (2 Steps)

**1. Start the API and frontend:**
```bash
cd market-pie5-bot
./start_api.sh
# In another terminal:
cd frontend && npm install && npm run dev
```

**2. Open the dashboard:**
- Open your browser to **http://localhost:5173**
- Splash screen appears with "Enter Dashboard" button
- Click to enter the trading dashboard 🎉

> **Note:** API runs at `http://localhost:8002` (default; do not use 8000 — reserved for Yacht); frontend at `http://localhost:5173`. See [Migration Guide (React default)](docs/MIGRATION_REACT_GUI.md).

#### 🛡️ Manual Start Confirmation (NEW!)

**The bot now requires explicit user confirmation before starting trades!**

- **CLI Mode**: Type `START` when prompted to begin trading
- **Web GUI**: Click the **Start** button to begin (with current settings)
- **No Auto-Trading**: Bot never trades until you explicitly confirm

**Benefits:**
- ✅ Review configuration before trading starts
- ✅ Apply and test settings without restart
- ✅ Cancel at any time before trading begins
- ✅ Complete control over when trading starts

**📖 [Complete Manual Start Guide →](MANUAL_START_GUIDE.md)**

---

#### 📱 Access from Mobile/Tablet

Find your Pi's IP address:
```bash
hostname -I
```

Then open on any device (use frontend port for UI):
```
http://<your-pi-ip>:5173
```
Example: `http://192.0.2.21:5173` (API: `http://192.0.2.21:8002` — do not use 8000, reserved for Yacht)

#### What You Get

The **Web GUI** (React + FastAPI) provides:
- 🎯 **Point-and-Click Interface**: No command-line required
- 📈 **Dashboard**: Stats, recent activity, bot status
- 🎚️ **Bot Controls**: Start, Stop, Shutdown; mode (yfinance, Sandbox, Live, Dry-run)
- 📋 **Trades & Pending Trades**: Trade list and approval flow
- 📄 **Logs**: Log viewer (trading_bot.log) with filters
- 📊 **Decision Report**: Live candidate symbols and per-symbol decisions
- ⚙️ **Settings, System, AI, Tax Reports**: Full configuration and tools
- 📱 **Mobile Access**: Monitor from phone/tablet on local network

**📖 [Migration Guide (React default) →](docs/MIGRATION_REACT_GUI.md)** | **[Phase 8 Test Plan →](docs/PHASE8_TEST_PLAN.md)**

---

### 🖥️ Desktop Icons for Raspberry Pi 5

**Quick and easy access from your application menu!**

Install desktop icons for both Web and Desktop GUIs:

```bash
cd market-pie5-bot
./install_desktop_icons.sh
```

This will add two icons to your application menu:
- **Market Pie5 Web Dashboard** - Browser-based interface (Recommended)
- **Market Pie5 Bot (Desktop GUI)** - Desktop Tkinter interface

Find them under Finance or Office categories, or search for "Market Pie5" in your launcher.

**📖 [Desktop Icons Installation Guide →](DESKTOP_ICONS_GUIDE.md)**

---

### Alternative: Quick Start (Raspberry Pi 5 - Desktop GUI)

The easiest way to start the bot on Pi5 with the desktop GUI is using the launcher script:

```bash
cd market-pie5-bot
./start_bot.sh
```

The launcher will:
1. Check and create virtual environment if needed
2. Install dependencies if needed
3. Prompt you to configure .env if missing
4. Let you choose GUI or command-line mode

---

### Web GUI Advanced Options

Run the API and frontend manually:

```bash
# API (required)
./start_api.sh
# Or: python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8002 --reload  # Do not use 8000 (Yacht)

# Frontend (in another terminal)
cd frontend && npm run dev
```

Then open your browser to: **http://localhost:5173** (API: **http://localhost:8002** — do not use 8000, reserved for Yacht).

Or access from any device on your network: **http://<your-ip>:5173** (ensure frontend is configured to call API at that host if needed).

#### Subdomain / CORS

When using the bot on a **subdomain** (e.g. **https://market-bot.example.com**), CORS allows subdomains by default. To add specific origins, set:

```bash
export CORS_ORIGINS=https://market-bot.example.com
```

Then restart the API. The regex also allows `192.0.2.21`, `localhost`, and common subdomains.

**📖 See [docs/MIGRATION_REACT_GUI.md](docs/MIGRATION_REACT_GUI.md) for migration and setup.**

---

### Desktop GUI Mode (Alternative)

Run the bot with the Tkinter desktop interface:

```bash
# If using virtual environment (recommended)
./venv/bin/python3 gui.py

# Or activate the virtual environment first
source venv/bin/activate
python gui.py
```

The **Desktop GUI** provides:
- **Control Panel**: Start/stop bot with PDT compliance checks
- **Settings**: Configure bot parameters without editing code
- **Logs**: Real-time log viewer with filtering
- **Resources**: Monitor CPU, RAM, Disk, and Network usage
- **Statistics**: Detailed performance metrics and trade history

### Pattern Day Trading (PDT) Compliance

**IMPORTANT**: PDT rules are **ONLY enforced in full production mode** (PAPER_TRADING_MODE=false).

**PDT Rules Summary**:
- A "day trade" is buying and selling the same security on the same trading day
- Accounts under $25,000 are limited to **3 day trades per 5 business days**
- Exceeding this limit can result in account restrictions (90-day freeze)
- **PDT rules apply ONLY in production/live trading mode**

**PDT Enforcement by Mode**:
- **Production/Live Mode** (PAPER_TRADING_MODE=false): PDT rules are **always enforced** for regulatory compliance
- **Paper Trading Mode** (PAPER_TRADING_MODE=true): PDT rules are **NOT enforced** - unlimited day trades allowed
- **Sandbox Mode** (SCHWAB_SANDBOX_MODE=true): PDT rules are **NOT enforced** - unlimited day trades allowed

**Note**: The `ENABLE_PDT_RULES` environment variable is no longer used. PDT enforcement is determined solely by the trading mode (PAPER_TRADING_MODE).

**Capital Management**:
- Starting capital: $500 (as specified in requirements)
- Capital floor: 10% of starting capital ($50)
- Bot automatically pauses trading if capital drops below floor
- This protects against catastrophic losses

**Trading Strategy for Small Accounts (Production Mode)**:
- Focus on **swing trades** (hold overnight) to avoid day trade classification
- Use the bot's allocation management to scale positions appropriately
- Goal: Make consistent small profits without violating PDT rules
- Daily profit target should cover: fees (~$0.50-5 per trade) + small profit margin

**How the Bot Handles PDT (Production Mode Only)**:
1. Tracks all day trades (same-day buy/sell) automatically
2. Warns when approaching 3-trade limit
3. Blocks trades that would violate PDT rules
4. Resets counter after 5 business days
5. Monitors capital floor and pauses if needed

**Recommended Settings for $500 Account**:
- Min Allocation: $50 (10% of capital)
- Max Allocation: $100 (20% of capital)
- Max Positions: 3-4 (to allow diversification)
- Trailing Stop: 3-5% (balance protection vs. premature exits)

### Paper Trading Mode (Default)

The bot starts in paper trading mode by default, which simulates trades without executing real orders:

**Command-line mode:**

```bash
# If using virtual environment (recommended)
./venv/bin/python3 main.py

# Or activate the virtual environment first
source venv/bin/activate
python main.py
```

### Live Trading Mode

⚠️ **WARNING: Live trading uses real money. Test thoroughly in paper mode first!**

To enable live trading:

1. **Configure credentials in `.env`**:
   ```bash
   cp .env.example .env
   # Edit .env and set:
   PAPER_TRADING_MODE=false
   SCHWAB_API_KEY=your_actual_api_key
   SCHWAB_APP_SECRET=your_actual_secret
   SCHWAB_CALLBACK_URL=your_actual_callback
   SCHWAB_ACCOUNT_ID=your_actual_account
   ```

2. **Validate configuration**:
   ```bash
   python3 -c "import main; valid, issues = main.validate_configuration(); print('Valid' if valid else issues)"
   ```

3. **Start the bot** (will prompt for confirmation):
   ```bash
   python3 main.py
   # Type 'CONFIRM' when prompted
   ```

**📖 See [LIVE_MODE_GUIDE.md](LIVE_MODE_GUIDE.md) for complete setup instructions, safety features, and troubleshooting.**

Key safety features:
- ✅ Credential validation before any trade
- ✅ Risk threshold checks (max 2% per trade by default)
- ✅ Capital floor protection (stops at 10% loss)
- ✅ Comprehensive error handling (timeouts, auth, rate limits)
- ✅ Detailed logging (trading_bot.log + alerts.log)
- ✅ User confirmation required for live mode

### Sandbox Testing Mode

For realistic testing without risking real money:

1. **Enable sandbox mode in `.env`**:
   ```bash
   PAPER_TRADING_MODE=true
   SCHWAB_SANDBOX_MODE=true
   # Add your Schwab API credentials (sandbox endpoints will be used)
   ```

2. **Start the bot**:
   ```bash
   python3 main.py
   ```

The bot will:
- Fetch real-time market data from Schwab sandbox API
- Execute trades against Schwab sandbox environment
- Use realistic rate limits and latency
- Log all API interactions for debugging

**Sandbox Benefits:**
- Test with production-like environment
- Validate API integration before going live
- Experience realistic API behavior (rate limits, timeouts, etc.)
- No risk to real capital

## Troubleshooting

### Collecting Error Logs for Analysis

If you're experiencing issues, you can collect all logs, self-test results, and debug information into a single file for analysis:

```bash
# Collect all logs into errorlogs.txt
./collect_logs.sh

# Or use the Python script directly
python3 collect_errorlogs.py
```

This script collects:
- ✅ Application logs (*.log files)
- ✅ API logs (/tmp/market-bot-api.log)
- ✅ Debug logs (debug_logs/ directory)
- ✅ Trade logs and debug traces (logs/ directory)
- ✅ Test results and self-test outputs
- ✅ Error files and known issues
- ✅ Backtest and ML optimization reports
- ✅ Git status and environment information

The output file `errorlogs.txt` can be committed to the repository for GitHub Copilot analysis or shared with maintainers for debugging.

### Debugging and Test Failures

If you're experiencing test failures or need help debugging issues:

- **[docs/TEST_FAILURES_ANALYSIS.md](docs/TEST_FAILURES_ANALYSIS.md)** - Comprehensive analysis of common test failures, their causes, and recommended fixes
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Detailed testing documentation and best practices
- **[KNOWN_ISSUES.md](KNOWN_ISSUES.md)** - Current known bugs, limitations, and workarounds

### Common Issues and Solutions

#### OAuth Authentication Issues

**Problem: "Browser window doesn't open for OAuth login"**
- **Solution**:
  - Check that you're running the bot in an environment with GUI/display support
  - For headless servers, complete OAuth on a desktop machine first, then copy `token.json`
  - Verify your `SCHWAB_CALLBACK_URL` is exactly `https://127.0.0.1:8182`

**Problem: "OAuth authentication failed"**
- **Solution**:
  - Verify `SCHWAB_API_KEY` and `SCHWAB_APP_SECRET` are correct (not placeholder values)
  - Ensure your app is approved in the Schwab Developer Portal
  - Check that `SCHWAB_CALLBACK_URL` in `.env` matches exactly what you set in Schwab Developer Portal
  - Try deleting `token.json` and re-authenticating

**Problem: "Token expired" or "Need to re-authenticate frequently"**
- **Solution**:
  - OAuth tokens last 7 days - you'll need to re-authenticate after that
  - Ensure the bot runs regularly (at least once every 7 days) to keep token refreshed
  - Check that `token.json` file permissions allow the bot to write to it

**Problem: "Running on a server without browser access"**
- **Solution**:
  1. Run the bot once on your local desktop machine with GUI
  2. Complete the OAuth login in the browser
  3. Copy the generated `token.json` file to your server
  4. Set `NON_INTERACTIVE=true` in your server's `.env` file

#### Schwab Sandbox API Issues

**Problem: "Authentication failed - invalid or expired API key"**
- **Solution**: Check that `SCHWAB_API_KEY` in `.env` is correct and not a placeholder
- Verify your API key is active at developer.schwab.com
- Ensure you're using the correct key for sandbox vs. production

**Problem: "API rate limit exceeded - too many requests"**
- **Solution**: This is normal in sandbox mode with frequent API calls
- The bot will automatically log the error and skip the trade
- Consider increasing `TRADING_FREQUENCY` in `.env` to reduce API call rate
- Wait a few minutes before retrying

**Problem: "Connection error" or "Request timeout"**
- **Solution**: Check your internet connection
- Verify Schwab API status at developer.schwab.com
- In **sandbox mode**, the bot will **STOP with a CRITICAL ERROR** (no fallback)
- In **simulation mode**, the bot will fall back to yfinance or random prices
- Review logs in `trading_bot.log` for details

**Problem: Sandbox mode not using Schwab API**
- **Solution**: Verify configuration in `.env`:
  - `PAPER_TRADING_MODE=true`
  - `SCHWAB_SANDBOX_MODE=true`
  - All Schwab credentials are configured
- Check startup logs for "Mode: PAPER TRADING (Schwab Sandbox)"
- Review `trading_bot.log` for API call attempts

#### Price Fetching Issues

**Problem: "CRITICAL ERROR: Schwab sandbox API failed"**

- This occurs when sandbox mode is enabled but Schwab API is unavailable
- The bot **STOPS IMMEDIATELY** - no fallback to yfinance or random prices
- This is by design - sandbox mode requires real API connectivity
- **Solution**: Fix the Schwab API connection issue:
  - Check SCHWAB_API_KEY is correct
  - Check SCHWAB_APP_SECRET is correct
  - Check SCHWAB_CALLBACK_URL is set to https://127.0.0.1 (or your redirect URI)
  - Verify network connectivity
  - Verify Schwab API service is available
- **Alternative**: Switch to pure simulation mode: Set SCHWAB_SANDBOX_MODE=false

**Problem: "Using simulated price (all API fetches failed)"**

- This only happens in **simulation mode** (SCHWAB_SANDBOX_MODE=false)
- yfinance API failed → using random prices as fallback
- **Does NOT occur in sandbox mode** - sandbox mode stops with CRITICAL ERROR instead
- For testing without APIs: Ensure SCHWAB_SANDBOX_MODE=false

**Problem: "API connectivity check failed" at startup**

This means the bot cannot connect to required APIs in sandbox/live mode:

**Causes:**
1. **Missing or invalid API credentials**
   - Check SCHWAB_API_KEY, SCHWAB_APP_SECRET, SCHWAB_ACCOUNT_ID in .env
   - Verify credentials are correct (not placeholder values)
   - Check SCHWAB_CALLBACK_URL is set to https://127.0.0.1 (or your configured redirect URI)

2. **Network connectivity issues**
   - Check internet connection
   - Verify firewall/proxy settings
   - Test connection: `curl https://api.schwabapi.com`

3. **Schwab API service down**
   - Check Schwab API status page
   - Try again later

**Note**: In sandbox mode, yfinance is NOT used as a fallback. The bot stops immediately if Schwab API fails.

**Solutions:**
- **To continue with sandbox mode**: Fix API credentials or network issues
  - Verify SCHWAB_API_KEY is correct
  - Verify SCHWAB_APP_SECRET is correct
  - Verify SCHWAB_CALLBACK_URL is set to https://127.0.0.1 (or your redirect URI)
  - Check network connectivity
- **To use pure simulation**: Set `SCHWAB_SANDBOX_MODE=false` in .env

**Problem: "Bot completed trades but sandbox API failed"**

This **NO LONGER HAPPENS**. The bot now:
- ✅ Stops immediately with CRITICAL ERROR when Schwab sandbox API fails
- ✅ No fallback to yfinance or random prices in sandbox mode
- ✅ Checks API connectivity at startup
- ✅ Ensures sandbox mode always uses real Schwab API data

Previously, the bot would silently fall back to yfinance or random prices when sandbox API failed. This has been eliminated - any API failure in sandbox mode now causes immediate termination.
- ✅ Show clear error messages
- ✅ Never complete trades with fake data in sandbox mode

If you still see this behavior, ensure you have the latest version of the code.

**Problem: Prices seem unrealistic or too volatile**
- **Solution**: If using simulation mode (no Schwab credentials), prices are randomly generated
- Enable sandbox mode for realistic market data
- Configure `SCHWAB_SANDBOX_MODE=true` and add API credentials

**Problem: "Error Getting AI Suggestions" or AI features unavailable**
- **Solution:** AI narratives use the ALFa AI brain (LiteLLM) on ``:
  1. Ensure `LITELLM_ENABLED=true` in `.env` (see `docs/ENV_VARS.md`)
  2. Verify the brain: `curl http://192.0.2.30/health/liveliness`
  3. Confirm `LITELLM_API_KEY` matches the brain's master key
  4. Recreate the API container to apply `.env` changes
  5. Check `/api/health/detailed` → `litellm.status` should be `healthy`
- **Parameter suggestions** (`GET /api/ai/optimization-suggestions`) do **not** require the LLM — they use backtest heuristics.
- **Trading gate:** With default `BOT_REQUIRE_BRAIN=true`, the bot **will not start** if the brain is down. Set `BOT_REQUIRE_BRAIN=false` to trade without the brain (AI narratives still need `LITELLM_ENABLED`).

**Problem: Bot refuses to start (HTTP 503 — brain unavailable)**
- **Cause:** `BOT_REQUIRE_BRAIN=true` and LiteLLM is down or `LITELLM_ENABLED=false`.
- **Fix:** Restore brain health, or set `BOT_REQUIRE_BRAIN=false` in `.env` and recreate the container.

**Problem: AI narrative fails after env changes**
- **Solution:** Recreate the API container (`docker compose ... --force-recreate market-bot-api`). See `docs/ENV_VARS.md`.

#### Mode Configuration Issues

**Problem: Not sure which mode is active**
- **Solution**: Check the summary at startup or end of trading:
  - "PAPER TRADING (Schwab Sandbox)" = Using Schwab sandbox API
  - "PAPER TRADING (Simulation)" = Using random/yfinance prices
  - "LIVE TRADING (Production)" = Using real money!
- Review `trading_bot.log` for detailed mode information

**Problem: Want to switch from simulation to sandbox**
- **Solution**:
  1. Set `SCHWAB_SANDBOX_MODE=true` in `.env`
  2. Configure all Schwab API credentials
  3. Keep `PAPER_TRADING_MODE=true`
  4. Restart the bot
  5. Verify startup logs show "Schwab Sandbox"

#### Debugging API Issues

**Enable detailed logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check API logs:**
- Review `trading_bot.log` for API request/response details
- Look for `[SANDBOX]` or `[PRODUCTION]` prefixes in logs
- Check `alerts.log` for trading errors and alerts

**Test API connectivity:**
```python
from main import TradingBot
bot = TradingBot()
result = bot.fetch_schwab_stock_price('AAPL')
print(f"Result: {result}")
```

**Run tests:**
```bash
# Test sandbox integration
python3 -m unittest test_schwab_sandbox_integration -v

# Test live mode features
python3 -m unittest test_live_mode_features -v
```

### Getting Help

If you encounter issues not covered here:
1. Check logs in `trading_bot.log` and `alerts.log`
2. Review the error message and stack trace
3. Search for similar issues in the GitHub repository
4. Create a new issue with:
   - Error message and full stack trace
   - Relevant configuration (sanitize credentials!)
   - Steps to reproduce
   - Bot logs (last 50 lines)

## Features

- **📉 Short Selling Support (Phase 1 Complete)**:
  - **Full short position support**: SHORT (open), COVER (close)
  - **Automatic signal conversion**: SELL signals → SHORT when flat
  - **Inverse P&L tracking**: Profit when prices fall
  - **Mixed portfolio**: Hold longs and shorts simultaneously
  - **Smart risk management**: Position limits, exposure caps
  - **Trailing stops**: Inverted logic for short protection
  - **Schwab API ready**: SELL_SHORT and BUY_TO_COVER instructions
  - Configure via `ALLOW_SHORTS_IN_PAPER`, `MAX_SHORT_POSITIONS`, `MAX_SHORT_EXPOSURE_PCT`
  - 📖 **[Short Selling Guide →](SHORT_SELLING_GUIDE.md)**
- **⚡ Asynchronous API Requests (NEW)**:
  - **Concurrent data fetching** from multiple APIs for faster I/O
  - **80% faster stock screening** compared to sequential fetching
  - **Schwab API prioritized** for buy/sell/account operations
  - **Connection pooling** optimized for Raspberry Pi 5
  - Fetches yfinance, Alpha Vantage, and sentiment data simultaneously
  - **Smart caching** to reduce API overhead (1-hour default)
  - **Graceful fallback** to synchronous mode if async unavailable
  - Configurable concurrency limits and timeouts
  - Enable via `ENABLE_ASYNC_FETCHING=true` (default)
  - 📖 **[Async API Guide →](ASYNC_API_GUIDE.md)**
- **🏆 Top Performers Watchlist (NEW)**:
  - **Intelligent stock ranking** by win probability using ML predictions
  - Displays top 50 stocks with highest success probability
  - **Real-time updates** with auto-refresh (every 60 seconds)
  - **Bot prioritization**: Automatically trades best stocks first
  - Combines ML predictions, sentiment analysis, and technical indicators
  - Sortable table with price, volume, and win probability
  - Manual refresh button for on-demand updates
  - Configurable watchlist size and refresh interval
  - Enable via `ENABLE_TOP_PERFORMERS_WATCHLIST=true`
  - 📖 **[Top Performers Watchlist Guide →](TOP_PERFORMERS_WATCHLIST_GUIDE.md)**
- **🔍 Intelligent Stock Discovery**:
  - **TOS-like prioritization**: Scans 100+ stocks, trades best first
  - **Multi-factor scoring**: momentum, volume, volatility, liquidity, sentiment
  - **Smart ranking**: Automatically prioritizes stocks by quality (#1, #2, #3...)
  - Discovers tradeable stocks from S&P 500 and major indices
  - Filters by price range (MIN_STOCK_PRICE to MAX_STOCK_PRICE)
  - Filters by volume (MIN_DAILY_VOLUME requirement)
  - Filters by volatility (MAX_STOCK_VOLATILITY limit)
  - Configurable scoring weights for custom strategies
  - Smart caching to reduce API calls
  - Graceful fallback to popular stocks when APIs unavailable
  - Enable/disable via `ENABLE_STOCK_SCREENER` setting
  - Configure max discovered stocks with `MAX_DISCOVERED_STOCKS`
  - 📖 **[Stock Prioritization Guide →](STOCK_PRIORITIZATION_GUIDE.md)** | **[Stock Screener Guide →](STOCK_SCREENER_GUIDE.md)**
- **🌐 Browser-Based Web Dashboard (RECOMMENDED)**:
  - Modern web interface: **React + FastAPI** (port 5173 + 8002; do not use 8000 — reserved for Yacht)
  - **Access from any device**: PC, Mac, tablet, or smartphone
  - **Dashboard**: Stats, recent activity, bot status; **Decision Report** for live symbol decisions
  - **Point-and-click controls**: Start/stop bot, mode selection (yfinance, Sandbox, Live, Dry-run)
  - **Logs, Trades, Pending Trades, Settings, System, AI, Tax Reports**
  - **Mobile-responsive**: Monitor trades from anywhere on your network
  - **No command-line knowledge required**: Perfect for beginners
  - 📖 **[Migration Guide (React default)](docs/MIGRATION_REACT_GUI.md)** | **[Phase 8 Test Plan](docs/PHASE8_TEST_PLAN.md)**
- **Schwab API Sandbox Integration**:
  - Real-time market data from Schwab sandbox API
  - Production-like testing environment without risk
  - **CRITICAL ERROR on API failure** - NO fallback in sandbox mode
  - Ensures sandbox mode uses only real API data
  - Comprehensive error handling (rate limits, timeouts, auth failures)
  - Detailed logging with mode differentiation
  - Smart caching to reduce API calls
- **Desktop GUI (Alternative)**: Tkinter-based GUI optimized for Raspberry Pi 5
  - Real-time log viewer
  - Settings configuration panel
  - Resource monitoring (CPU, RAM, Disk, Network)
  - Statistics dashboard
  - TOS CSV import dialog
- **Pattern Day Trading (PDT) Compliance**:
  - Automatically tracks day trades (buy and sell same day)
  - Prevents PDT violations for accounts under $25,000
  - Limits to 3 day trades per 5 business days
  - Capital floor protection (pauses bot if capital drops below 10% of starting)
  - **IMPORTANT**: Starting with $500 capital requires careful trade management
- **T+1 Settlement Tracking (Cash Account)**:
  - Enforces T+1 (1 business day) settlement rules for all trading modes
  - Capital used to buy stocks is locked until T+1 settlement date
  - Proceeds from selling stocks are locked until T+1 settlement date
  - Prevents use of unsettled funds for trading (Good Faith Violations)
  - Automatically skips weekends when calculating settlement dates
  - Essential for non-margin cash accounts to comply with settlement rules
- **Multiple Trading Modes**:
  - **Sandbox Mode**: Schwab API with simulated trading (recommended for testing)
  - **Paper Trading**: Local simulation with random or yfinance prices
  - **Live Trading**: Real money trading via Schwab production API
- **Self-Scaling**: Automatically adjusts allocation based on win rate
  - Win rate > 60%: Increase allocation by 20%
  - Win rate ≤ 60%: Decrease allocation by 10%
- **Trailing Stop Loss**: Protect profits with configurable trailing stops
  - Tracks high water mark for each position
  - Automatically exits when price falls below trailing stop threshold
  - Configurable stop percentage (default: 3%)
- **Realistic Paper Trading Simulation**:
  - Sequential trades with random delays (1-5 seconds)
  - Configurable symbol scan list from file
  - Random price and volume generation for realistic market conditions
- **TOS paperMoney CSV Import**:
  - Import trades from ThinkorSwim paperMoney CSV exports
  - Parse Symbol, Quantity, Price, Action, and Date columns
  - Automatic P&L calculation and track record updates
  - Compatible with standard TOS export format
- **AI Integration**: Sends track record to the ALFa AI brain (LiteLLM) for strategy analysis
  - Uses the OpenAI-compatible chat completions endpoint (`/v1/chat/completions`)
  - Routes via the `app-chat` model alias on the brain (`192.0.2.30`)
  - Provides intelligent trading suggestions based on performance data
  - Degrades gracefully: if the brain is unreachable, the bot keeps trading
  - **Auto-Tweak**: Can automatically adjust bot settings based on AI recommendations (requires user verification)
  - **Win Rate Auto-Tuning**: ML-powered parameter optimization when win rate drops below 70% target
    - Automatically triggers when win rate < 70% and ≥10 trades executed
    - Uses the ML parameter optimizer via the ALFa AI brain (LiteLLM)
    - Optimizes risk threshold, stops, take profit, and allocation sizes
    - Configurable target via WIN_RATE_TARGET environment variable
- **Risk Management**: Configurable risk thresholds and allocation limits
- **Resource Throttling (NEW)**: Intelligent resource management for Raspberry Pi 5
  - Automatic CPU and memory usage monitoring
  - Configurable throttling thresholds (default: 75% for both)
  - Automatic slowdown when resources exceed limits
  - Prevents system instability and ensures smooth operation
  - Maintains bot efficiency without overwhelming Pi5 hardware
  - Zero-configuration default settings optimized for Pi5
- **Resource Monitoring**: Real-time system resource tracking
  - CPU, RAM, Disk, and Network monitoring
  - Bottleneck detection and alerts
  - Optimized for Raspberry Pi 5
- **Alert System**: Get notified of important events
  - Logs all alerts to alerts.log file
  - Capital floor breaches
  - Significant P&L changes (>10% of capital)
  - Bot status changes
  - **NEW: Email notifications** via SMTP (fully implemented!)
    - Professional HTML and plain-text email templates
    - Retry logic with exponential backoff
    - Works with Gmail, Outlook, Office 365, Yahoo, and custom SMTP
    - SSL/TLS encryption support
    - Comprehensive configuration guide ([EMAIL_ALERTS_GUIDE.md](EMAIL_ALERTS_GUIDE.md))
- **📊 Tax Reporting (NEW)**:
  - **IRS Form 8949 CSV Export**: Generate IRS-compliant capital gains/losses reports
  - **Wash Sale Detection**: Automatic detection of wash sales per IRS 30-day rule
  - **Short-Term vs Long-Term**: Automatic classification based on holding period
  - **CPA-Ready Reports**: Comprehensive text reports for professional review
  - **Tax Summary JSON**: Machine-readable format with all trade details
  - **Cost Basis Tracking**: Accurate proceeds and cost basis calculations
  - **Multi-Year Support**: Generate reports for any tax year
  - 📖 **[Tax Reporting Guide →](TAX_REPORTING_GUIDE.md)**
- **Dynamic Symbol Scanning**:
  - Load symbols from API endpoint (if configured)
  - Falls back to file-based scanning
  - Hot-reloading without bot restart

## New Features Detailed Guide

### Capital Floor Protection

The bot automatically pauses trading if your capital drops below 10% of starting capital:

- **Starting capital**: $500
- **Capital floor**: $50 (10% of $500)
- **Auto-pause**: Bot stops trading if capital < $50
- **Auto-resume**: Bot resumes when capital recovers to >$60 (120% of floor)

This prevents catastrophic losses and gives you time to reassess strategy.

### Pattern Day Trading (PDT) Compliance

The GUI and bot automatically track and prevent PDT violations:

- **Automatic tracking**: Counts day trades (same-day buy/sell)
- **Warning system**: Shows current count (X/3)
- **Block trades**: Prevents 4th day trade within 5 business days
- **Smart detection**: Only applies to accounts under $25,000

### T+1 Settlement Rules (Cash Accounts)

The bot enforces T+1 settlement rules to comply with cash account regulations and prevent Good Faith Violations:

**What is T+1 Settlement?**
- **T** = Trade date (the day you execute the trade)
- **+1** = Settlement date is 1 business day after the trade
- Weekends are automatically skipped in the calculation

**How It Works:**
1. **When you BUY a stock**: The capital used is locked until T+1
   - Example: Buy $1,000 of AAPL on Monday → Capital settles Tuesday
   - That $1,000 cannot be used for another trade until Tuesday

2. **When you SELL a stock**: The proceeds are locked until T+1
   - Example: Sell stock for $1,500 on Wednesday → Proceeds settle Thursday
   - That $1,500 cannot be used for another trade until Thursday

**Why This Matters:**
- **Cash Accounts** (non-margin) cannot use unsettled funds
- Using unsettled funds would be a **Good Faith Violation**
- Multiple violations can lead to account restrictions (90-day freeze)

**How the Bot Handles It:**
- Automatically tracks all unsettled funds with settlement dates
- Checks available (settled) capital before each trade
- Blocks trades if insufficient settled capital
- Displays clear messages when trades are blocked by settlement
- Works in all modes: Paper Trading, Sandbox, and Live Trading

**Example Scenario:**
```
Starting Capital: $10,000

Monday 9:00 AM:  Buy $3,000 of AAPL
                 Available Capital: $7,000 (locked $3,000 until Tuesday)

Monday 2:00 PM:  Try to buy $8,000 of TSLA
                 ❌ BLOCKED - Only $7,000 settled capital available

Tuesday 9:00 AM: AAPL purchase settles
                 Available Capital: $10,000 (all funds settled)

Tuesday 10:00 AM: Can now buy $8,000 of TSLA ✓
```

**Technical Details:**
- Settlement tracking in `unsettled_funds` list
- Business day calculation with weekend skipping
- Automatic cleanup of settled funds
- Pre-trade validation with `check_settled_capital_available()`

### Resource Monitoring

The GUI displays real-time Pi5 resource usage:

- **CPU**: Current CPU utilization percentage
- **Memory**: RAM usage percentage
- **Disk**: Storage usage percentage
- **Network**: Upload/download speed in KB/s
- **Bottleneck alerts**: Automatic warnings when resources >80% (CPU/RAM) or >90% (Disk)

This helps identify performance issues that might affect trading.

### Resource Throttling (NEW)

**Intelligent resource management for Raspberry Pi 5 stability and efficiency.**

The bot automatically monitors and throttles resource usage to maintain system stability:

**How It Works:**
- Monitors CPU and memory usage before each trade
- When usage exceeds configured thresholds, automatically pauses trading
- Waits for a configurable delay before continuing
- Resumes normal operation when resources return to acceptable levels
- Tracks throttling events for performance analysis

**Default Configuration (Optimized for Pi5):**
- CPU Limit: 75% maximum
- Memory Limit: 75% maximum
- Throttle Delay: 5 seconds when limits exceeded
- Status: Enabled by default

**Why This Matters:**
- Prevents system freezes and crashes on resource-constrained hardware
- Maintains bot responsiveness and stability
- Ensures other Pi5 processes can run smoothly
- Extends hardware lifespan by preventing thermal stress
- Zero configuration required - works out of the box

**Customization:**

Add these variables to your `.env` file to customize throttling:

```bash
# Enable/disable resource throttling (default: true)
BOT_ENABLE_THROTTLING=true

# Maximum CPU usage before throttling (default: 75%)
BOT_MAX_CPU_PERCENT=75

# Maximum memory usage before throttling (default: 75%)
BOT_MAX_MEMORY_PERCENT=75

# Maximum disk usage before throttling (default: 90%) - NEW
BOT_MAX_DISK_PERCENT=90

# Maximum network throughput before throttling in MB/s (default: 100) - NEW
BOT_MAX_NETWORK_MBPS=100

# Delay in seconds when throttling (default: 5)
BOT_THROTTLE_DELAY=5
```

**Monitoring Throttling:**

The bot logs throttling events and displays statistics:

```
[RESOURCE THROTTLE] CPU usage 78.5% exceeds 75% - Waiting 5s before continuing
```

View throttling statistics in the bot summary:
```
Resource Throttling: Enabled
  CPU Limit: 75%
  Memory Limit: 75%
  Disk Limit: 90%        # NEW
  Network Limit: 100MB/s # NEW
  Throttle Events: 12
```

**When to Adjust:**
- **Increase limits (80-85%)**: If bot is throttling too frequently and you have headroom
- **Decrease limits (60-70%)**: If running other services on the same Pi5
- **Increase delay (10-15s)**: For aggressive resource conservation
- **Disable completely**: Only if running on more powerful hardware (not recommended for Pi5)

### AI Auto-Tweak

**Status: 🧪 Beta Feature** - Requires explicit opt-in and includes multiple safeguards.

The bot can analyze its performance and suggest setting adjustments using AI:

**How It Works:**
1. Bot sends track record to the ALFa AI brain (LiteLLM)
2. AI analyzes win rate, allocation, trade count
3. AI suggests optimized parameters (risk, stops, allocation, etc.)
4. **User reviews suggestions** through confirmation modal
5. **User approves** changes before they are applied

**🔒 Safeguards (NEW):**
- **Disabled by default** - Must explicitly enable with `BOT_ENABLE_AI_AUTO_TWEAK=true`
- **Confirmation modal** - GUI requires user confirmation before applying
- **Beta warning banner** - Visible alert in AI Assistant tab
- **Settings toggle** - Clear control with warnings in Settings tab
- **Manual review** - Always review suggestions before applying
- **Revertible** - Changes can be undone in Settings tab

**Enable AI Auto-Tweak:**
```bash
# In .env file:
BOT_ENABLE_AI_AUTO_TWEAK=true      # Disabled by default - explicit opt-in
HUGGINGFACE_API_KEY=your_key       # Required for AI features
```

**Using AI Auto-Tweak:**
1. Enable the feature in `.env` (see above)
2. Go to AI Assistant tab in web GUI
3. Review beta warning banner
4. Click "Get AI Suggestions"
5. Review the suggested changes carefully
6. Click "Apply AI Suggestions to Settings"
7. **Confirm in the modal** that appears
8. Changes are saved to `.env`

**⚠️ Important**: This is a beta feature under active development. Always review AI suggestions carefully. The bot will not apply changes without your explicit confirmation.
3. AI suggests optimal settings (trailing stops, risk thresholds)
4. You review suggestions in GUI
5. Optionally enable auto-apply for automatic tuning

**Important**: Always review AI suggestions before applying them. Auto-apply mode should be used with caution and continuous monitoring.

### Dynamic Symbol Scanning

Instead of a static file, load symbols dynamically from an API:

1. Set `DYNAMIC_SCAN_API_URL` in .env (advanced use case)
2. API should return JSON with symbols list
3. Bot fetches fresh symbols before each trading session
4. Falls back to TOS-like screener or scan_symbols.txt if API fails

**Example API Response**:
```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL", "TSLA"]
}
```

Or simply:
```json
["AAPL", "MSFT", "GOOGL", "TSLA"]
```

### Tax Reporting

**Generate IRS-compliant tax reports for all your trades!**

The bot now includes comprehensive tax reporting functionality to help you document all trades for tax filing purposes. The system generates IRS Form 8949 compatible reports, detects wash sales, and provides detailed summaries suitable for CPA review.

#### Quick Start

Generate all tax reports for the current year:

```bash
python3 tax_report_generator.py
```

Or specify a tax year:

```bash
python3 tax_report_generator.py 2024
```

#### Generated Reports

Three reports are automatically generated:

1. **`form_8949_tax_year_YYYY.csv`** - IRS Form 8949 compatible CSV
   - Short-term capital gains/losses (≤365 days)
   - Long-term capital gains/losses (>365 days)
   - Columns match IRS form requirements
   - Ready for import to tax software

2. **`tax_summary_YYYY.json`** - Comprehensive JSON summary
   - All trade details with dates and amounts
   - Summary statistics by holding period
   - Wash sale tracking
   - Machine-readable format

3. **`cpa_report_YYYY.txt`** - Human-readable CPA report
   - Executive summary with totals
   - Trade-by-trade breakdown
   - Wash sale analysis
   - Professional format for CPA review

#### Features

- **IRS Form 8949 Export**: CSV format matching IRS requirements
- **Wash Sale Detection**: Automatic detection per IRS 30-day rule
- **Holding Period Classification**: Short-term vs long-term automatically determined
- **Cost Basis Tracking**: Accurate proceeds and cost basis calculations
- **Multi-Year Support**: Generate reports for any tax year
- **CPA-Ready Format**: Professional reports suitable for tax professionals

#### Example Output

```
================================================================================
TRADING TAX REPORT FOR CPA REVIEW
================================================================================
Tax Year: 2024
Generated: 2026-01-23 15:30:00

EXECUTIVE SUMMARY
--------------------------------------------------------------------------------
Total Completed Trades: 18
Short-Term Trades (≤365 days): 15
Long-Term Trades (>365 days): 3
Potential Wash Sales Detected: 2

Short-Term Capital Gain/(Loss): $1,800.00
Long-Term Capital Gain/(Loss): $650.00
Net Capital Gain/(Loss): $2,450.00
```

#### Important Notes

⚠️ **Disclaimer**: These reports are for informational purposes only. Always:
- Compare with official brokerage statements (Form 1099-B)
- Verify all trades are included
- Review wash sale detections with a CPA
- Consult a qualified tax professional for filing

📖 **[Complete Tax Reporting Guide →](TAX_REPORTING_GUIDE.md)**

## Testing

This project includes comprehensive test coverage for all features. Tests can be run using either `unittest` (Python's built-in testing framework) or `pytest` (more feature-rich alternative).

### Running Tests

#### Using unittest (Python Built-in)

```bash
# Activate virtual environment (recommended)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run all tests with unittest
python3 -m unittest discover -s . -p "test_*.py" -v

# Run specific test file
python3 -m unittest test_trading_bot -v

# Run specific test suite
python3 -m unittest test_trading_bot.TestTradingBot -v

# Run specific test method
python3 -m unittest test_trading_bot.TestTradingBot.test_execute_trade -v
```

#### Using pytest (Recommended)

```bash
# Activate virtual environment (recommended)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install pytest testing dependencies (not in requirements.txt)
pip install pytest-cov pytest-xdist pytest-timeout pytest-asyncio

# Set required environment variables for testing
export PAPER_TRADING_MODE='true'
export SCHWAB_SANDBOX_MODE='true'

# Create reports directory for JUnit XML output (required by pytest.ini)
mkdir -p reports

# Run all tests with pytest
pytest test_*.py -v

# Run tests in parallel (faster on multi-core systems)
pytest test_*.py -n auto

# Run tests with coverage report
pytest test_*.py --cov=. --cov-report=html
pytest test_*.py --cov=. --cov-report=term-missing

# Run specific test file
pytest test_trading_bot.py -v

# Run tests by marker (unit, integration, e2e, slow)
pytest -m unit -v
pytest -m "not slow" -v
```

**Test Organization:**
- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests for APIs and services
- `@pytest.mark.e2e` - End-to-end workflow tests
- `@pytest.mark.slow` - Long-running tests (backtests, etc.)

### Test Suites

The project includes the following main test suites:

- **`test_trading_bot.py`** - Core trading bot functionality
- **`test_new_features.py`** - New features and enhancements
- **`test_gui_features.py`** - GUI and desktop features
- **`test_web_gui_*.py`** - Web dashboard tests
- **`test_adaptive_learning.py`** - AI and machine learning tests
- **`test_backtest_*.py`** - Backtesting and strategy tests
- **`test_security_*.py`** - Security and encryption tests

### Test Requirements

**Environment Variables for Testing:**
```bash
export PAPER_TRADING_MODE='true'     # Use paper trading mode
export SCHWAB_SANDBOX_MODE='true'    # Use sandbox mode (optional)
```

**Note:** `ENABLE_PDT_RULES` is deprecated and no longer used. PDT enforcement is controlled solely by `PAPER_TRADING_MODE`.

**Test Types:**
- **Unit tests** (`@pytest.mark.unit`): Run with mocks, no external API credentials required
- **Integration tests** (`@pytest.mark.integration`): May require Schwab sandbox API credentials for full testing
  - If you don't have API credentials, integration tests will be skipped or use fallback mocks
  - Sandbox mode requires valid API keys (see [Sandbox Testing Mode](#sandbox-testing-mode) in README)
- **E2E tests** (`@pytest.mark.e2e`): Full workflow tests, may require API connectivity

Most tests use mocks and will run without any API credentials. Set `PAPER_TRADING_MODE='true'` to ensure safe testing.

### Troubleshooting Test Failures

If you encounter test failures:

1. **Check environment variables** - Ensure testing env vars are set correctly
2. **Review test logs** - Look for specific error messages in test output
3. **Check API credentials** - Some tests require valid (sandbox) API keys
4. **Verify dependencies** - Ensure all packages in `requirements.txt` are installed
5. **See detailed analysis** - Check **[docs/TEST_FAILURES_ANALYSIS.md](docs/TEST_FAILURES_ANALYSIS.md)** for known issues and fixes

### Contributing and Testing Standards

For detailed information about:
- Writing new tests
- Testing best practices
- Code coverage requirements
- CI/CD integration
- Mocking external APIs

**See [CONTRIBUTING.md](CONTRIBUTING.md)** for complete testing guidelines and contribution standards.

### Automated Testing & CI/CD

The project uses GitHub Actions for automated testing and continuous integration.

#### GitHub Actions Workflows

| Workflow | Status | Purpose |
|----------|--------|---------|
| **Tests** | [![Tests](https://github.com/operator/market-pie5-bot/workflows/Tests/badge.svg)](https://github.com/operator/market-pie5-bot/actions/workflows/tests.yml) | Unit tests on Python 3.10-3.12 with parallel execution |
| **Code Quality** | [![Code Quality](https://github.com/operator/market-pie5-bot/workflows/Code%20Quality/badge.svg)](https://github.com/operator/market-pie5-bot/actions/workflows/lint.yml) | Linting (flake8, black, isort, pylint) |
| **Security** | [![Security](https://github.com/operator/market-pie5-bot/workflows/Security%20Scan/badge.svg)](https://github.com/operator/market-pie5-bot/actions/workflows/security.yml) | Security scanning (Safety, Bandit, CodeQL) |
| **E2E Tests** | [![E2E Tests](https://github.com/operator/market-pie5-bot/workflows/End-to-End%20Tests/badge.svg)](https://github.com/operator/market-pie5-bot/actions/workflows/e2e.yml) | Integration and end-to-end tests |

**Key Features:**
- ✅ **Parallel Test Execution** - Tests run faster with pytest-xdist
- ✅ **Code Coverage Reporting** - Enforced minimum 60% coverage threshold
- ✅ **Security Enforcement** - Blocks PRs with high-severity security issues
- ✅ **Multi-Python Version Testing** - Ensures compatibility with Python 3.10-3.12
- ✅ **Comprehensive Summaries** - Detailed test results and coverage reports in GitHub Actions

### Additional Test Documentation

- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing documentation and CI/CD workflows
- **[docs/TEST_FAILURES_ANALYSIS.md](docs/TEST_FAILURES_ANALYSIS.md)** - Analysis of common test failures and fixes
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Testing standards and contribution guidelines
- **[VERIFICATION_GUIDE.md](VERIFICATION_GUIDE.md)** - Manual testing and validation procedures


## New Features Usage

### Trailing Stop Loss

The bot automatically monitors positions with trailing stops:

```python
bot = TradingBot(total_capital=10000.0)
bot.trailing_stop_percent = 0.05  # 5% trailing stop

# Trailing stops are automatically applied to all BUY trades
bot.execute_trade('AAPL', 'BUY', 150.50)
```

### Symbol Scanning from File (Optional - RARELY USED)

**Note**: This method is **only used when ENABLE_STOCK_SCREENER=false**. The bot uses TOS-like dynamic discovery by default.

If you want to manually control the exact symbols to trade, create a `scan_symbols.txt` file with one symbol per line:

```
AUID
BNKK
CGTL
CJMB
SEGG
```

The bot will automatically load and trade these symbols sequentially with random delays:

```python
symbols = bot.load_scan_symbols()  # Loads from SCAN_SYMBOLS_FILE
for symbol in symbols:
    price = bot.generate_random_price()
    bot.execute_trade(symbol, 'BUY', price)
    time.sleep(random.uniform(1, 5))  # Random delay
```

### TOS paperMoney CSV Import

Export your ThinkorSwim paperMoney trades to CSV and import them:

```python
# Import trades from TOS CSV
trades = bot.import_tos_csv('tos_paper_trades.csv')

# Process and update track record
bot.process_tos_trades(trades)
```

Expected CSV format:
```csv
Symbol,Quantity,Price,Action,Date
AAPL,10,150.25,BUY,2026-01-15
MSFT,5,380.50,BUY,2026-01-15
GOOGL,-8,140.75,SELL,2026-01-15
```

The bot will:
- Parse the CSV (case-insensitive column names)
- Calculate P&L for each trade
- Update the bot's track record and statistics

## Centralized Logging and Analysis

The bot now includes a comprehensive logging and analysis system for tracking performance and generating insights.

### LogManager - Centralized Logging

The `LogManager` class consolidates all logging into a unified system with both JSON and SQLite storage:

```python
from log_manager import LogManager

# Initialize log manager
log_manager = LogManager(log_dir="logs", db_name="trading_logs.db")

# Log trades
trade = {
    'symbol': 'AAPL',
    'action': 'BUY',
    'quantity': 10.0,
    'price': 150.0,
    'is_win': True,
    'pnl': 50.0,
    'pnl_percent': 3.33,
    'exit_reason': 'trailing_stop',
    'strategy': 'momentum'
}
log_manager.log_trade(trade)

# Log system events
log_manager.log_system_event('INFO', 'Trading bot started', {'version': '1.0'})

# Log backtest results
backtest_result = {
    'initial_capital': 10000.0,
    'final_capital': 11000.0,
    'total_pnl': 1000.0,
    'roi': 0.10,
    'total_trades': 50,
    'winning_trades': 30,
    'losing_trades': 20,
    'win_rate': 0.60
}
log_manager.log_backtest_result(backtest_result)

# Merge existing trade history
log_manager.merge_trade_history(bot.trade_history)

# Retrieve trades with filters
trades = log_manager.get_trades(symbol='AAPL', start_date='2024-01-01')
```

### Report Generation and Analysis

Generate comprehensive reports with KPI analysis:

```python
from report_generator import LogParser, ReportGenerator

# Create parser and generator
parser = LogParser(db_path="logs/trading_logs.db")
generator = ReportGenerator(parser)

# Generate text report
text_report = generator.generate_text_report(output_file="report.txt")
print(text_report)

# Generate JSON report
json_report = generator.generate_json_report(output_file="report.json")

# Generate visualization script
generator.generate_visualization_script(output_file="visualize.py")
```

Run the standalone report generator:

```bash
# Generate reports from existing logs
python3 report_generator.py

# Generate visualizations (requires matplotlib)
python3 visualize.py
```

### Key Performance Indicators (KPIs)

The system automatically calculates comprehensive KPIs:

- **Win Rate**: Percentage of profitable trades
- **Total P&L**: Cumulative profit/loss
- **ROI**: Return on investment
- **Sharpe Ratio**: Risk-adjusted return metric
- **Max Drawdown**: Maximum peak-to-trough decline
- **Profit Factor**: Ratio of gross profit to gross loss
- **Average Win/Loss**: Mean profit per winning/losing trade
- **Rolling Averages**: Time-based performance trends

### Enhanced Backtesting Analytics

The backtesting module now includes advanced analytics:

```python
from backtesting import Backtester
from main import TradingBot

# Create backtester with initial capital
backtester = Backtester(initial_capital=10000.0)

# Generate or load historical data
historical_data = backtester.generate_historical_data(
    symbol='TEST',
    days=100,
    start_price=100.0,
    volatility=0.02
)

# Run backtest with bot
bot = TradingBot(total_capital=10000.0)
backtest_result = backtester.run_backtest(bot, historical_data)

# Run baseline comparison
baseline_result = backtester.run_baseline(historical_data)

# Generate enhanced report with analytics
report = backtester.generate_report('backtest_report.json')
```

The enhanced report includes:
- **Rolling Metrics**: 10-period rolling averages and win rates
- **Distribution Metrics**: Mean, std dev, percentiles, skewness, kurtosis
- **Sharpe Ratio**: Risk-adjusted performance measure
- **Max Drawdown**: Maximum capital decline percentage
- **Benchmark Comparison**: Performance vs. buy-and-hold strategy

### Enhanced Trade Filtering

The `filter_stock()` method now includes advanced pre-trade validation:

```python
# The filter checks multiple criteria:
# 1. Minimum price (avoid penny stocks)
# 2. Minimum volume (ensure liquidity)
# 3. Maximum volatility (risk control)
# 4. Trend gradient (detect strong downtrends)
# 5. Volatility pattern (detect increasing instability)

is_valid, reason = bot.filter_stock('AAPL', price=150.0, volume=1000000)

if is_valid:
    print(f"Stock passed all filters")
    # Access validation metadata
    last_validation = bot.stock_validation_log[-1]
    print(f"Checks passed: {last_validation['metadata']['checks_passed']}")
else:
    print(f"Stock rejected: {reason}")
```

### Exit Condition Logging

All position exits are now logged with comprehensive metadata:

```python
# When closing a position, detailed exit conditions are logged
exit_info = bot.close_position('AAPL', exit_price=155.0, exit_reason='trailing_stop')

# Exit info includes:
# - Entry/exit prices and P&L
# - Hold duration
# - Exit volatility
# - High price achieved
# - Trailing stop percentage
# - Partial exit status
```

### Log Storage Structure

Logs are stored in multiple formats for flexibility:

**SQLite Database** (`logs/trading_logs.db`):
- `trades` table: All trade data with metadata
- `system_logs` table: System events and errors
- `backtest_results` table: Backtest performance data
- `performance_metrics` table: Time-series metrics

**JSON Files** (in `logs/` directory):
- `trades_<session_id>.json`: Trade log (one per line)
- `system_<session_id>.json`: System events log
- `backtest_<session_id>.json`: Complete backtest results

### Visualization Features

The visualization script generates professional charts:

1. **Cumulative P&L Over Time**: Line chart with trend
2. **Win Rate Pie Chart**: Visual breakdown of wins vs. losses
3. **Performance Metrics Bar Chart**: Sharpe ratio, profit factor, max drawdown
4. **Summary Statistics Panel**: Key metrics in text format

Install matplotlib to use visualization features:

```bash
pip3 install matplotlib
```

Then generate and view charts:

```bash
python3 visualize.py
# Creates 'trading_performance.png' with all charts
```

### Testing Logging and Reporting

Run comprehensive tests for the new features:

```bash
# Run logging and reporting tests
python3 -m unittest test_logging_reporting -v

# Specific test classes
python3 -m unittest test_logging_reporting.TestLogManager -v
python3 -m unittest test_logging_reporting.TestLogParser -v
python3 -m unittest test_logging_reporting.TestReportGenerator -v
python3 -m unittest test_logging_reporting.TestEnhancedFilterStock -v
```

---

## **Copilot PR Label Gate**

- **Purpose:** Copilot PRs must include the `copilot-completed` label before merging.
- **Automation:** An auto-label workflow adds the label when all required checks succeed on branches starting with `copilot/`.
- **Gate Behavior:** The gate re-triggers on the label being added and passes automatically when present.
- **Manual Fallback:** If automation doesn’t trigger, add the label in the PR sidebar (Labels → copilot-completed). Optional CLI:
  - Install: winget install GitHub.cli
  - Login: gh auth login
  - Label: gh pr edit <number> --add-label copilot-completed
- **Branch Naming:** Use `copilot/<task-slug>` (e.g., `copilot/add-dryrun-live-mode-tests`).

See also: [CONTRIBUTING.md](CONTRIBUTING.md) and [.github/workflows/](.github/workflows/) for CI details.
