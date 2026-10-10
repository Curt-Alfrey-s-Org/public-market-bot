# Server worktree commit — 2026-04-02

Snapshot generated on the server immediately before `git add` / commit / push.
Purpose: document everything that was pending in the working tree for this repository.

## Branch tracking
## main...origin/main
 M .env.example
 M .gitignore
 M CHANGELOG.md
 M api/main.py
 M api/middleware/error_handler.py
 M api/routes/health.py
 M docker-compose.yml
 M docs/INDEX.md
 D docs/archive/AI_ASSISTANT_IMPLEMENTATION.md
 D docs/archive/AI_ASSISTANT_VISUAL_MOCKUP.md
 D docs/archive/API_CONNECTIVITY_FIX.md
 D docs/archive/BACKGROUND_FIX_IMPLEMENTATION.md
 D docs/archive/BACKGROUND_FIX_SUMMARY.md
 D docs/archive/BETTER_SIM_MIMIC_SUMMARY.md
 D docs/archive/BUG_FIX_SUMMARY.md
 D docs/archive/CHART_FIX_BEFORE_AFTER.md
 D docs/archive/CHROMIUM_LAUNCH_IMPLEMENTATION.md
 D docs/archive/CI_CD_IMPLEMENTATION_SUMMARY.md
 D docs/archive/CLOSED_PR_FIXES_SUMMARY.md
 D docs/archive/CODE_ANALYSIS_REPORT.md
 D docs/archive/COMPLETE_SUMMARY.md
 D docs/archive/DASHBOARD_CHART_FIX_SUMMARY.md
 D docs/archive/DEBUG_LOGGING_IMPROVEMENTS.md
 D docs/archive/DRY_RUN_ANALYSIS_COMPLETE.md
 D docs/archive/ENCRYPTION_KEY_BEFORE_AFTER.md
 D docs/archive/ENCRYPTION_KEY_FIX_SUMMARY.md
 D docs/archive/ENVIRONMENT_VARIABLES_SUMMARY.md
 D docs/archive/ERROR_LOGS_FIX_SUMMARY.md
 D docs/archive/FALLBACK_IMPROVEMENTS_SUMMARY.md
 D docs/archive/FEATURE_COMPARISON.md
 D docs/archive/FINAL_SUMMARY.md
 D docs/archive/FIX_SUMMARY.md
 D docs/archive/FIX_SUMMARY_CAPITAL_SAVING.md
 D docs/archive/FIX_SUMMARY_NUMBER_FORMATTING.md
 D docs/archive/FORMATTING_CHANGES_SUMMARY.md
 D docs/archive/GUI_CONFIRMATION_MOCKUPS.md
 D docs/archive/GUI_JSON_ERROR_HANDLING_COMPLETE.md
 D docs/archive/ICON_FIX_COMPLETE.md
 D docs/archive/ICON_FIX_SUMMARY.md
 D docs/archive/IMAGE_LOADING_FIX_SUMMARY.md
 D docs/archive/IMAGE_PERSISTENCE.md
 D docs/archive/IMPLEMENTATION_COMPLETE.md
 D docs/archive/IMPLEMENTATION_COMPLETE_SUMMARY.md
 D docs/archive/IMPLEMENTATION_NOTES.md
 D docs/archive/IMPLEMENTATION_SUMMARY.md
 D docs/archive/IMPLEMENTATION_SUMMARY_CHARTS.md
 D docs/archive/IMPLEMENTATION_SUMMARY_DYNAMIC_SCREENER.md
 D docs/archive/IMPLEMENTATION_SUMMARY_OLD.md
 D docs/archive/INTEGRATION_SUMMARY.md
 D docs/archive/ISSUE_FIX_SUMMARY.md
 D docs/archive/ISSUE_FIX_VERIFICATION.md
 D docs/archive/LIVE_MODE_PREPARATION_SUMMARY.md
 D docs/archive/LUMIBOT_REMOVAL_SUMMARY.md
 D docs/archive/MANUAL_START_IMPLEMENTATION.md
 D docs/archive/MAX_STOCK_PRICE_FIX.md
 D docs/archive/MODE_FIX_SUMMARY.md
 D docs/archive/MODE_SELECTION_IMPLEMENTATION.md
 D docs/archive/MODE_SELECTION_SUMMARY.md
 D docs/archive/NODEJS_ENHANCEMENTS_SUMMARY.md
 D docs/archive/NON_INTERACTIVE_FIX.md
 D docs/archive/OAUTH_FIX_COMPARISON.md
 D docs/archive/OAUTH_IMPLEMENTATION_SUMMARY.md
 D docs/archive/PARAMETER_GATING.md
 D docs/archive/PDT_ENFORCEMENT_FIX_SUMMARY.md
 D docs/archive/PR120_RERUN_VALIDATION.md
 D docs/archive/PR86_VALIDATION_REVIEW.md
 D docs/archive/PR_REVIEW_SUMMARY.md
 D docs/archive/PR_SUMMARY.md
 D docs/archive/PR_SUMMARY_OLD.md
 D docs/archive/PR_SUMMARY_SANDBOX_LIVE.md
 D docs/archive/SCHWAB_API_TOGGLE_IMPLEMENTATION.md
 D docs/archive/SECURITY_IMPLEMENTATION_SUMMARY.md
 D docs/archive/SECURITY_SUMMARY.md
 D docs/archive/SETTINGS_LABEL_COMPARISON.md
 D docs/archive/SETTINGS_PERSISTENCE_FIX.md
 D docs/archive/SETTINGS_PERSISTENCE_IMPLEMENTATION.md
 D docs/archive/SETTINGS_VISUAL_EXAMPLES.md
 D docs/archive/SHUTDOWN_BUTTON_MOCKUP.md
 D docs/archive/SHUTDOWN_IMPLEMENTATION_SUMMARY.md
 D docs/archive/STARTUP_ORDER_AND_SANDBOX_FIX.md
 D docs/archive/STOCK_PRICE_FIX.md
 D docs/archive/STOCK_SEARCH_ENHANCEMENT_SUMMARY.md
 D docs/archive/STOCK_TRADING_SUMMARY.md
 D docs/archive/SUMMARY.md
 D docs/archive/SWING_HOLD_IMPLEMENTATION.md
 D docs/archive/SYSTEM_MONITOR_FIX_SUMMARY.md
 D docs/archive/SYSTEM_MONITOR_INTEGRATION.md
 D docs/archive/TRADE_HISTORY_FIX_SUMMARY.md
 D docs/archive/TRADE_SETTINGS_FIX_SUMMARY.md
 D docs/archive/VALIDATION_DEMO.md
 D docs/archive/VISUAL_COMPARISON.md
 D docs/archive/WEB_GUI_IMPLEMENTATION_SUMMARY.md
 D docs/archive/WEB_GUI_IMPROVEMENTS_SUMMARY.md
 D docs/archive/WEB_GUI_LAYOUT.md
 D docs/archive/YFINANCE_FALLBACK_ALERT_IMPLEMENTATION.md
 M frontend/src/api/client.ts
 M frontend/src/components/ErrorBoundary.tsx
 M frontend/src/context/AuthContext.tsx
 M requirements.txt
 M scripts/backup_postgres.sh
A  scripts/cleanup_docker_disk.sh
 M scripts/docker_cleanup.sh
 M scripts/restore_postgres.sh
 M setup_dashboard.sh
 D tests/archived/demos/README.md
 D tests/archived/demos/demo_async_startup.py
 D tests/archived/demos/demo_backtest_instance_methods.py
 D tests/archived/demos/demo_backtest_mode.py
 D tests/archived/demos/demo_chart_visualization.py
 D tests/archived/demos/demo_debug_log_fixes.py
 D tests/archived/demos/demo_debug_log_fixes_sentiment.py
 D tests/archived/demos/demo_delisted_stocks_fix.py
 D tests/archived/demos/demo_email_alert.py
 D tests/archived/demos/demo_enhanced_stock_discovery_logging.py
 D tests/archived/demos/demo_fixed_bot.py
 D tests/archived/demos/demo_gui_error_handling_validation.py
 D tests/archived/demos/demo_gui_validation.py
 D tests/archived/demos/demo_hf_api_error_handling.py
 D tests/archived/demos/demo_json_error_handling.py
 D tests/archived/demos/demo_max_stock_price_fix.py
 D tests/archived/demos/demo_monte_carlo_integration.py
 D tests/archived/demos/demo_rate_limiting.py
 D tests/archived/demos/demo_schwab_api_toggle.py
 D tests/archived/demos/demo_search_stocks.py
 D tests/archived/demos/demo_sentiment_thread_fix.py
 D tests/archived/demos/demo_startup_fixes.py
 D tests/archived/demos/demo_stock_discovery.py
 D tests/archived/demos/demo_stock_filtering_optimization.py
 D tests/archived/demos/demo_stock_prioritization.py
 D tests/archived/demos/demo_stock_screener_enhancements.py
 D tests/archived/demos/demo_stock_screener_fix.py
 D tests/archived/demos/demo_swing_backtest.py
 D tests/archived/demos/demo_t1_settlement.py
 D tests/archived/demos/demo_tax_reporting.py
 D tests/archived/demos/demo_token_error_handling.py
 D tests/archived/demos/demo_tos_table_layout.py
 D tests/archived/demos/demo_watchlist_debug_logging.py
 D tests/archived/demos/demo_win_rate_auto_tuning.py
 D tests/archived/demos/demo_yfinance_fallback_alert.py
?? .github/CODING_STANDARDS.md
?? .github/PORT_ASSIGNMENTS.md
?? api/middleware/prometheus.py
?? api/middleware/request_id.py
?? api/routes/metrics.py
?? docs/DEPENDENCIES.md
?? docs/DOCKER_DISK_CLEANUP.md
?? docs/PRODUCTION_API_OWNERSHIP.md
?? docs/RANKINGS_BOT_IMPROVEMENT_ANALYSIS.md
?? docs/SERVER_COMMIT_2026-04-02.md
?? docs/START_STOP_RESTART.md
?? docs/WHAT_CONTROLS_THE_APP.md
?? scripts/export_compose_uid_gid.sh
?? scripts/start.sh
?? scripts/stop.sh

## Unstaged/staged diff stat (before `git add`)
 .env.example                                       |   5 +
 .gitignore                                         |   2 +
 CHANGELOG.md                                       |   9 +
 api/main.py                                        |  21 +-
 api/middleware/error_handler.py                    |  52 +--
 api/routes/health.py                               |  60 ++-
 docker-compose.yml                                 |   5 +
 docs/INDEX.md                                      |  35 +-
 docs/archive/AI_ASSISTANT_IMPLEMENTATION.md        | 285 ------------
 docs/archive/AI_ASSISTANT_VISUAL_MOCKUP.md         | 228 ---------
 docs/archive/API_CONNECTIVITY_FIX.md               | 376 ---------------
 docs/archive/BACKGROUND_FIX_IMPLEMENTATION.md      | 216 ---------
 docs/archive/BACKGROUND_FIX_SUMMARY.md             | 218 ---------
 docs/archive/BETTER_SIM_MIMIC_SUMMARY.md           | 324 -------------
 docs/archive/BUG_FIX_SUMMARY.md                    | 168 -------
 docs/archive/CHART_FIX_BEFORE_AFTER.md             | 274 -----------
 docs/archive/CHROMIUM_LAUNCH_IMPLEMENTATION.md     | 263 -----------
 docs/archive/CI_CD_IMPLEMENTATION_SUMMARY.md       | 166 -------
 docs/archive/CLOSED_PR_FIXES_SUMMARY.md            | 141 ------
 docs/archive/CODE_ANALYSIS_REPORT.md               | 412 ----------------
 docs/archive/COMPLETE_SUMMARY.md                   | 276 -----------
 docs/archive/DASHBOARD_CHART_FIX_SUMMARY.md        | 153 ------
 docs/archive/DEBUG_LOGGING_IMPROVEMENTS.md         | 272 -----------
 docs/archive/DRY_RUN_ANALYSIS_COMPLETE.md          | 197 --------
 docs/archive/ENCRYPTION_KEY_BEFORE_AFTER.md        | 164 -------
 docs/archive/ENCRYPTION_KEY_FIX_SUMMARY.md         | 165 -------
 docs/archive/ENVIRONMENT_VARIABLES_SUMMARY.md      | 124 -----
 docs/archive/ERROR_LOGS_FIX_SUMMARY.md             | 228 ---------
 docs/archive/FALLBACK_IMPROVEMENTS_SUMMARY.md      | 108 -----
 docs/archive/FEATURE_COMPARISON.md                 | 188 --------
 docs/archive/FINAL_SUMMARY.md                      | 517 ---------------------
 docs/archive/FIX_SUMMARY.md                        | 299 ------------
 docs/archive/FIX_SUMMARY_CAPITAL_SAVING.md         |  88 ----
 docs/archive/FIX_SUMMARY_NUMBER_FORMATTING.md      |  74 ---
 docs/archive/FORMATTING_CHANGES_SUMMARY.md         | 215 ---------
 docs/archive/GUI_CONFIRMATION_MOCKUPS.md           | 416 -----------------
 docs/archive/GUI_JSON_ERROR_HANDLING_COMPLETE.md   | 279 -----------
 docs/archive/ICON_FIX_COMPLETE.md                  | 240 ----------
 docs/archive/ICON_FIX_SUMMARY.md                   | 244 ----------
 docs/archive/IMAGE_LOADING_FIX_SUMMARY.md          | 142 ------
 docs/archive/IMAGE_PERSISTENCE.md                  | 233 ----------
 docs/archive/IMPLEMENTATION_COMPLETE.md            | 348 --------------
 docs/archive/IMPLEMENTATION_COMPLETE_SUMMARY.md    | 406 ----------------
 docs/archive/IMPLEMENTATION_NOTES.md               | 224 ---------
 docs/archive/IMPLEMENTATION_SUMMARY.md             | 328 -------------
 docs/archive/IMPLEMENTATION_SUMMARY_CHARTS.md      | 143 ------
 .../IMPLEMENTATION_SUMMARY_DYNAMIC_SCREENER.md     | 335 -------------
 docs/archive/IMPLEMENTATION_SUMMARY_OLD.md         | 222 ---------
 docs/archive/INTEGRATION_SUMMARY.md                | 401 ----------------
 docs/archive/ISSUE_FIX_SUMMARY.md                  | 206 --------
 docs/archive/ISSUE_FIX_VERIFICATION.md             | 186 --------
 docs/archive/LIVE_MODE_PREPARATION_SUMMARY.md      | 138 ------
 docs/archive/LUMIBOT_REMOVAL_SUMMARY.md            | 152 ------
 docs/archive/MANUAL_START_IMPLEMENTATION.md        |  68 ---
 docs/archive/MAX_STOCK_PRICE_FIX.md                | 150 ------
 docs/archive/MODE_FIX_SUMMARY.md                   | 163 -------
 docs/archive/MODE_SELECTION_IMPLEMENTATION.md      | 217 ---------
 docs/archive/MODE_SELECTION_SUMMARY.md             | 206 --------
 docs/archive/NODEJS_ENHANCEMENTS_SUMMARY.md        | 371 ---------------
 docs/archive/NON_INTERACTIVE_FIX.md                | 229 ---------
 docs/archive/OAUTH_FIX_COMPARISON.md               | 216 ---------
 docs/archive/OAUTH_IMPLEMENTATION_SUMMARY.md       | 182 --------
 docs/archive/PARAMETER_GATING.md                   | 190 --------
 docs/archive/PDT_ENFORCEMENT_FIX_SUMMARY.md        | 176 -------
 docs/archive/PR120_RERUN_VALIDATION.md             | 155 ------
 docs/archive/PR86_VALIDATION_REVIEW.md             | 251 ----------
 docs/archive/PR_REVIEW_SUMMARY.md                  |  91 ----
 docs/archive/PR_SUMMARY.md                         | 132 ------
 docs/archive/PR_SUMMARY_OLD.md                     | 286 ------------
 docs/archive/PR_SUMMARY_SANDBOX_LIVE.md            | 232 ---------
 docs/archive/SCHWAB_API_TOGGLE_IMPLEMENTATION.md   | 221 ---------
 docs/archive/SECURITY_IMPLEMENTATION_SUMMARY.md    | 302 ------------
 docs/archive/SECURITY_SUMMARY.md                   | 127 -----
 docs/archive/SETTINGS_LABEL_COMPARISON.md          |  94 ----
 docs/archive/SETTINGS_PERSISTENCE_FIX.md           | 275 -----------
 .../archive/SETTINGS_PERSISTENCE_IMPLEMENTATION.md | 276 -----------
 docs/archive/SETTINGS_VISUAL_EXAMPLES.md           | 375 ---------------
 docs/archive/SHUTDOWN_BUTTON_MOCKUP.md             | 330 -------------
 docs/archive/SHUTDOWN_IMPLEMENTATION_SUMMARY.md    | 432 -----------------
 docs/archive/STARTUP_ORDER_AND_SANDBOX_FIX.md      | 164 -------
 docs/archive/STOCK_PRICE_FIX.md                    | 185 --------
 docs/archive/STOCK_SEARCH_ENHANCEMENT_SUMMARY.md   | 278 -----------
 docs/archive/STOCK_TRADING_SUMMARY.md              | 177 -------
 docs/archive/SUMMARY.md                            | 144 ------
 docs/archive/SWING_HOLD_IMPLEMENTATION.md          | 209 ---------
 docs/archive/SYSTEM_MONITOR_FIX_SUMMARY.md         | 135 ------
 docs/archive/SYSTEM_MONITOR_INTEGRATION.md         | 187 --------
 docs/archive/TRADE_HISTORY_FIX_SUMMARY.md          | 103 ----
 docs/archive/TRADE_SETTINGS_FIX_SUMMARY.md         |  88 ----
 docs/archive/VALIDATION_DEMO.md                    | 176 -------
 docs/archive/VISUAL_COMPARISON.md                  | 212 ---------
 docs/archive/WEB_GUI_IMPLEMENTATION_SUMMARY.md     | 298 ------------
 docs/archive/WEB_GUI_IMPROVEMENTS_SUMMARY.md       | 247 ----------
 docs/archive/WEB_GUI_LAYOUT.md                     | 234 ----------
 .../YFINANCE_FALLBACK_ALERT_IMPLEMENTATION.md      | 169 -------
 frontend/src/api/client.ts                         | 254 ++++++----
 frontend/src/components/ErrorBoundary.tsx          | 121 +++--
 frontend/src/context/AuthContext.tsx               |  10 +
 requirements.txt                                   |   1 +
 scripts/backup_postgres.sh                         |   5 +-
 scripts/cleanup_docker_disk.sh                     | 113 +++++
 scripts/docker_cleanup.sh                          |   1 +
 scripts/restore_postgres.sh                        |   5 +-
 setup_dashboard.sh                                 |   4 +-
 tests/archived/demos/README.md                     |   9 -
 tests/archived/demos/demo_async_startup.py         | 123 -----
 .../demos/demo_backtest_instance_methods.py        | 147 ------
 tests/archived/demos/demo_backtest_mode.py         | 161 -------
 tests/archived/demos/demo_chart_visualization.py   | 229 ---------
 tests/archived/demos/demo_debug_log_fixes.py       | 137 ------
 .../demos/demo_debug_log_fixes_sentiment.py        |  59 ---
 tests/archived/demos/demo_delisted_stocks_fix.py   | 142 ------
 tests/archived/demos/demo_email_alert.py           | 208 ---------
 .../demos/demo_enhanced_stock_discovery_logging.py | 128 -----
 tests/archived/demos/demo_fixed_bot.py             | 163 -------
 .../demos/demo_gui_error_handling_validation.py    | 223 ---------
 tests/archived/demos/demo_gui_validation.py        | 284 -----------
 tests/archived/demos/demo_hf_api_error_handling.py |  95 ----
 tests/archived/demos/demo_json_error_handling.py   | 198 --------
 tests/archived/demos/demo_max_stock_price_fix.py   |  93 ----
 .../archived/demos/demo_monte_carlo_integration.py | 418 -----------------
 tests/archived/demos/demo_rate_limiting.py         | 138 ------
 tests/archived/demos/demo_schwab_api_toggle.py     | 151 ------
 tests/archived/demos/demo_search_stocks.py         |  62 ---
 tests/archived/demos/demo_sentiment_thread_fix.py  |  89 ----
 tests/archived/demos/demo_startup_fixes.py         | 138 ------
 tests/archived/demos/demo_stock_discovery.py       | 164 -------
 .../demos/demo_stock_filtering_optimization.py     | 134 ------
 tests/archived/demos/demo_stock_prioritization.py  | 226 ---------
 .../demos/demo_stock_screener_enhancements.py      | 211 ---------
 tests/archived/demos/demo_stock_screener_fix.py    | 124 -----
 tests/archived/demos/demo_swing_backtest.py        | 125 -----
 tests/archived/demos/demo_t1_settlement.py         | 159 -------
 tests/archived/demos/demo_tax_reporting.py         | 278 -----------
 tests/archived/demos/demo_token_error_handling.py  | 135 ------
 tests/archived/demos/demo_tos_table_layout.py      | 221 ---------
 .../archived/demos/demo_watchlist_debug_logging.py | 129 -----
 tests/archived/demos/demo_win_rate_auto_tuning.py  | 128 -----
 .../archived/demos/demo_yfinance_fallback_alert.py |  57 ---
 139 files changed, 505 insertions(+), 25219 deletions(-)
 scripts/cleanup_docker_disk.sh | 113 +++++++++++++++++++++++++++++++++++++++++
 1 file changed, 113 insertions(+)

## Untracked files (first 400 lines)
.github/CODING_STANDARDS.md
.github/PORT_ASSIGNMENTS.md
api/middleware/prometheus.py
api/middleware/request_id.py
api/routes/metrics.py
docs/DEPENDENCIES.md
docs/DOCKER_DISK_CLEANUP.md
docs/PRODUCTION_API_OWNERSHIP.md
docs/RANKINGS_BOT_IMPROVEMENT_ANALYSIS.md
docs/SERVER_COMMIT_2026-04-02.md
docs/START_STOP_RESTART.md
docs/WHAT_CONTROLS_THE_APP.md
scripts/export_compose_uid_gid.sh
scripts/start.sh
scripts/stop.sh

## Recent commits (last 5)
6a7dd96 feat: Add API v1 reliability improvements, mobile navigation, structured logging, and comprehensive test suite
7e8958b chore: cleanup and network/nginx updates
b168cdb Update project files
8e79137 ROADMAP: add Option B (mount frontend) for tomorrow; clean up for fresh start
a28c7d4 feat: Centralized authentication integration
