"""
Bot Manager - Handles bot lifecycle and integration with API
Manages bot instance, start/stop/shutdown operations
"""

import threading
import logging
import os
import sys
from datetime import datetime
from typing import Optional
from api.utils import set_bot_instance, get_bot_instance
from api.utils.timeutils import utcnow as _naive_utcnow

logger = logging.getLogger(__name__)

# Global bot thread and control
_bot_thread: Optional[threading.Thread] = None
_bot_instance = None
_bot_running = False
_bot_stop_event = threading.Event()

# Last reason the bot refused to start (surfaced by the /start endpoints).
_last_start_error: Optional[str] = None


class BrainUnavailableError(RuntimeError):
    """Raised when BOT_REQUIRE_BRAIN is set but the ALFa AI brain is unreachable.

    Policy: the trader must not run without the brain. The trade *decisions*
    themselves are made by deterministic strategies + local ML, but the operator
    has chosen to hard-gate the whole trading loop on brain availability.
    """


def _brain_required() -> bool:
    """True when the trader must not run unless the ALFa AI brain is reachable."""
    return os.getenv("BOT_REQUIRE_BRAIN", "true").lower() in ("true", "1", "yes")


def _brain_status() -> tuple:
    """Return (ok: bool, detail: str) for the ALFa AI brain liveliness probe."""
    try:
        from api.services.litellm_client import litellm_health_sync

        timeout = float(os.getenv("BOT_BRAIN_CHECK_TIMEOUT_SECONDS", "10"))
        h = litellm_health_sync(timeout=timeout)
        detail = f"{h.get('status', 'unknown')} @ {h.get('base_url', '?')}"
        if h.get("error"):
            detail += f" ({h['error']})"
        return bool(h.get("ok")), detail
    except Exception as e:  # noqa: BLE001 - never let the probe break lifecycle
        return False, f"probe_error: {type(e).__name__}: {e}"


def brain_config_error() -> Optional[str]:
    """Clear, variable-naming error when BOT_REQUIRE_BRAIN is on but LiteLLM is not configured.

    Returns None when the brain is not required or the config looks complete
    (reachability is still probed by _brain_status at start time).
    """
    if not _brain_required():
        return None
    try:
        from api.services.litellm_client import litellm_missing_config, get_litellm_base_url
        missing = litellm_missing_config()
        base_url = get_litellm_base_url()
    except Exception as e:  # noqa: BLE001
        return f"ALFa AI brain config could not be checked: {type(e).__name__}: {e}"
    if not missing:
        return None
    hints = []
    if "LITELLM_ENABLED" in missing:
        hints.append("LITELLM_ENABLED is not true (set LITELLM_ENABLED=true)")
    if "LITELLM_API_KEY" in missing:
        hints.append("LITELLM_API_KEY is not set (set it to this bot's LiteLLM key)")
    return (
        "Bot cannot start: BOT_REQUIRE_BRAIN=true but the ALFa AI brain (LiteLLM at "
        f"{base_url}) is not configured: " + "; ".join(hints) + ". "
        "Set these in the environment (see env.required.example / docs/ENV_VARS.md), "
        "or set BOT_REQUIRE_BRAIN=false to run without the brain."
    )


def get_last_start_error() -> Optional[str]:
    """Reason the most recent start attempt was refused (or None)."""
    return _last_start_error

def initialize_bot_from_main():
    """
    Initialize bot instance from main.py TradingBot class
    This should be called when the bot needs to be started
    """
    global _bot_instance
    import time
    
    init_start = time.time()
    logger.info(f"[BOT_INIT] Bot initialization started at {datetime.now().isoformat()}")
    
    try:
        # Import TradingBot from main module
        import_start = time.time()
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from main import TradingBot
        import_elapsed = time.time() - import_start
        logger.debug(f"[BOT_INIT] TradingBot import: {import_elapsed:.3f}s")
        
        # Get capital from environment or use default
        capital = float(os.getenv('BOT_TOTAL_CAPITAL', '10000.0'))
        
        # Create bot instance
        create_start = time.time()
        bot = TradingBot(total_capital=capital)
        create_elapsed = time.time() - create_start
        logger.debug(f"[BOT_INIT] TradingBot creation: {create_elapsed:.3f}s")
        
        # Determine and set mode based on environment variables
        paper_mode = os.getenv('PAPER_TRADING_MODE', 'true').lower() == 'true'
        sandbox_mode = os.getenv('SCHWAB_SANDBOX_MODE', 'false').lower() == 'true'
        
        if not paper_mode:
            mode = 'live'
        elif sandbox_mode:
            mode = 'sandbox'
        else:
            mode = 'yfinance'  # Paper trading without sandbox = yfinance simulation
        
        # Set mode attribute on bot instance
        bot.mode = mode
        
        # Set bot instance for API
        set_bot_instance(bot)
        _bot_instance = bot
        
        init_elapsed = time.time() - init_start
        logger.info(f"[BOT_INIT] Bot instance initialized: capital=${capital:.2f}, mode={mode} in {init_elapsed:.3f}s")
        return bot
    except Exception as e:
        init_elapsed = time.time() - init_start
        logger.error(f"[BOT_INIT] Failed to initialize bot after {init_elapsed:.3f}s: {e}", exc_info=True)
        raise

def start_bot():
    """
    Start the bot in a background thread
    Bot must be initialized with the selected mode before starting
    """
    global _bot_thread, _bot_running, _bot_instance, _last_start_error
    import time
    
    if _bot_running:
        logger.warning("Bot is already running")
        return False
    
    # Hard gate: do not run the trader if the ALFa AI brain is down.
    if _brain_required():
        config_error = brain_config_error()
        if config_error:
            _last_start_error = config_error
            logger.error("[BOT_START] %s", _last_start_error)
            raise BrainUnavailableError(_last_start_error)
        ok, detail = _brain_status()
        if not ok:
            _last_start_error = (
                f"ALFa AI brain is not reachable — refusing to start "
                f"(BOT_REQUIRE_BRAIN=true): {detail}"
            )
            logger.error("[BOT_START] %s", _last_start_error)
            raise BrainUnavailableError(_last_start_error)
        logger.info("[BOT_START] Brain health OK (%s) — proceeding with start", detail)
    _last_start_error = None
    
    start_time = time.time()
    try:
        # Reload the runtime env file so GUI settings changes (Strategy, Trading, etc.) take
        # effect on Restart. Host installs: project .env (as before). Containers: only
        # BOT_RUNTIME_ENV_FILE, if set (see api/runtime_env.py).
        try:
            from dotenv import load_dotenv
            from api.runtime_env import runtime_env_file
            env_path = runtime_env_file()
            if env_path is not None and env_path.exists():
                load_dotenv(env_path, override=True)
                logger.info("Reloaded %s for bot start (Settings changes will apply)", env_path)
        except ImportError:
            pass

        # Always reinitialize bot to pick up mode changes
        # This ensures the bot uses the latest mode settings from .env
        logger.info("Initializing bot with current mode settings...")
        # Shutdown existing instance if it exists
        if _bot_instance is not None:
            logger.info("Reinitializing bot with updated mode settings...")
            shutdown_bot()
        
        _bot_instance = initialize_bot_from_main()
        
        bot = get_bot_instance()
        if not bot:
            logger.error("Failed to get bot instance")
            return False
        
        # Verify mode is set
        if not hasattr(bot, 'mode') or not bot.mode:
            # Get mode from environment as fallback
            paper_mode = os.getenv('PAPER_TRADING_MODE', 'true').lower() == 'true'
            sandbox_mode = os.getenv('SCHWAB_SANDBOX_MODE', 'false').lower() == 'true'
            
            if not paper_mode:
                bot.mode = 'live'
            elif sandbox_mode:
                bot.mode = 'sandbox'
            else:
                bot.mode = 'yfinance'
            
            logger.info(f"Bot mode set to: {bot.mode}")
        
        # Clear stop event
        _bot_stop_event.clear()
        
        # Set running flag on bot instance (add if not exists)
        if not hasattr(bot, 'running'):
            bot.running = False
        bot.running = True
        _bot_running = True
        
        # Start bot in background thread
        _bot_thread = threading.Thread(
            target=_run_bot_loop,
            args=(bot,),
            daemon=True,
            name="TradingBotThread"
        )
        _bot_thread.start()
        
        start_elapsed = time.time() - start_time
        logger.info(f"[BOT_START] Bot started successfully in {bot.mode} mode in {start_elapsed:.3f}s")
        return True
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        _bot_running = False
        return False

def _load_symbols_todays_best(bot, max_symbols: int, use_screener: bool):
    """
    Load symbols using roadmap priority: Feed (today's best) → screener/file.
    Used for both startup and periodic refresh so a hot stock can enter the pool.
    """
    try:
        from top_performers_feed import get_feed_symbols
        feed_symbols = get_feed_symbols()
        if feed_symbols:
            symbols = feed_symbols[:max_symbols]
            logger.info(f"Using Top Performers Feed (today's best): {len(symbols)} symbols")
            return symbols
    except Exception as e:
        logger.debug(f"Feed not available, using screener/file: {e}")
    if use_screener:
        logger.info("Stock screener - discovering tradeable stocks (today's best)...")
        return bot.load_scan_symbols(use_screener=True, max_symbols=max_symbols)
    logger.info("Using symbols from file...")
    return bot.load_scan_symbols(use_screener=False)


def _run_bot_loop(bot):
    """
    Main bot loop - runs in background thread
    Runs continuous trading cycles until stopped
    """
    global _bot_running
    
    logger.info("Bot loop started")
    
    try:
        import time
        from main import (
            ENABLE_STOCK_SCREENER, MAX_DISCOVERED_STOCKS,
            TRADING_FREQUENCY, PAPER_TRADING_MODE, SCHWAB_SANDBOX_MODE,
            EXIT_REFRESH_PRICE
        )
        from api.bot_state import load_bot_state, save_bot_state, should_resume
        
        # Set running flag (ensure it exists)
        if not hasattr(bot, 'running'):
            bot.running = False
        bot.running = True
        _bot_running = True
        
        # YFinance mode: trade continuously (minimal delays). Other modes: use TRADING_FREQUENCY and WEB_GUI_CYCLE_DELAY.
        yfinance_mode = (
            getattr(bot, 'mode', None) == 'yfinance'
            or (PAPER_TRADING_MODE and not SCHWAB_SANDBOX_MODE and os.getenv('SCHWAB_API_ENABLED', 'on').lower() in ('off', 'false'))
        )
        if yfinance_mode:
            trade_delay = 0
            cycle_delay = max(0.5, int(os.getenv('WEB_GUI_CYCLE_DELAY', '1')))
            logger.info("Bot loop running in continuous mode (yfinance) — minimal delays between trades")
        else:
            trade_delay = max(0, int(os.getenv('TRADING_FREQUENCY', str(TRADING_FREQUENCY))))
            cycle_delay = max(0.5, int(os.getenv('WEB_GUI_CYCLE_DELAY', '5')))
            logger.info("Bot loop running in continuous mode...")
        
        recovery_minutes = max(0, int(os.getenv('BOT_RECOVERY_WINDOW_MINUTES', '30')))
        saved_state = load_bot_state()
        if saved_state and should_resume(saved_state, recovery_minutes):
            # Resume: restore symbols and no_trade_streak from last run
            scan_symbols = saved_state.get('current_symbols') or []
            cycle_count = max(0, int(saved_state.get('cycle_number', 0)))
            bot.no_trade_streak = dict(saved_state.get('no_trade_streak') or {})
            if scan_symbols:
                logger.info(f"Resuming from saved state: {len(scan_symbols)} symbols, cycle #{cycle_count + 1} (within {recovery_minutes} min window)")
                bot.current_symbols = scan_symbols
                if hasattr(bot, 'stored_messages'):
                    bot.stored_messages.add_message("Bot resumed from saved state", category='info')
            else:
                scan_symbols = []
        else:
            cycle_count = 0
            scan_symbols = []
            if saved_state:
                logger.info(f"Saved state is older than {recovery_minutes} min — starting fresh")
        
        if not scan_symbols:
            # Fresh start or resumed with empty list: load symbols from feed/screener
            logger.info("Loading symbols to trade...")
            scan_symbols = _load_symbols_todays_best(
                bot, MAX_DISCOVERED_STOCKS, ENABLE_STOCK_SCREENER
            )
            if not scan_symbols:
                logger.warning("No symbols available for trading")
                _bot_running = False
                bot.running = False
                return
            logger.info(f"Loaded {len(scan_symbols)} symbols for trading")
            bot.current_symbols = scan_symbols
            if not hasattr(bot, 'no_trade_streak') or bot.no_trade_streak is None:
                bot.no_trade_streak = {}
            if hasattr(bot, 'stored_messages'):
                bot.stored_messages.add_message("Bot started", category='info')
        else:
            if not hasattr(bot, 'no_trade_streak') or bot.no_trade_streak is None:
                bot.no_trade_streak = {}
        
        # How often to refresh symbol list for "today's best" (0 = only at startup)
        symbol_refresh_interval = int(os.getenv('SYMBOL_REFRESH_INTERVAL_CYCLES', '0'))
        if symbol_refresh_interval > 0:
            logger.info(f"Symbol list will refresh every {symbol_refresh_interval} cycle(s) (today's best)")
        
        # Ensure Decision Report (GET /decisions) has a valid structure: candidate_decisions and current_cycle_number
        # are updated each cycle in Phase 2 below; current_symbols is already set above.
        if not hasattr(bot, 'candidate_decisions') or bot.candidate_decisions is None:
            bot.candidate_decisions = {}
        if not hasattr(bot, 'current_cycle_number'):
            bot.current_cycle_number = 0
        
        # Brain-availability re-check cadence (start_bot already verified once).
        require_brain = _brain_required()
        brain_check_interval = max(0, int(os.getenv('BOT_BRAIN_CHECK_INTERVAL_SECONDS', '60')))
        last_brain_check = time.time()
        
        # Continuous trading loop
        while not _bot_stop_event.is_set() and _bot_running:
            # Hard gate: halt trading if the ALFa AI brain goes down mid-run.
            if require_brain and brain_check_interval > 0 and (time.time() - last_brain_check) >= brain_check_interval:
                last_brain_check = time.time()
                ok, detail = _brain_status()
                if not ok:
                    logger.error(
                        "[BOT_LOOP] Halting trading — ALFa AI brain unreachable mid-run "
                        "(BOT_REQUIRE_BRAIN=true): %s", detail
                    )
                    if hasattr(bot, 'stored_messages'):
                        bot.stored_messages.add_message(
                            f"Trading halted: AI brain down ({detail})", category='error'
                        )
                    _bot_running = False
                    if hasattr(bot, 'running'):
                        bot.running = False
                    break
            
            cycle_count += 1
            if hasattr(bot, 'current_cycle_number'):
                bot.current_cycle_number = cycle_count
            logger.info(f"\n=== Trading Cycle #{cycle_count} ===")
            if hasattr(bot, 'stored_messages'):
                bot.stored_messages.add_message(f"Cycle #{cycle_count} started", category='info')
            
            # Refresh symbol list periodically so we get "today's best" and can find hot stocks later
            if symbol_refresh_interval > 0 and (cycle_count % symbol_refresh_interval == 0):
                try:
                    scan_symbols = _load_symbols_todays_best(
                        bot, MAX_DISCOVERED_STOCKS, ENABLE_STOCK_SCREENER
                    )
                    if scan_symbols:
                        bot.current_symbols = scan_symbols
                        logger.info(f"Refreshed symbol list (today's best): {len(scan_symbols)} symbols")
                    # else keep previous scan_symbols
                except Exception as e:
                    logger.warning(f"Symbol refresh failed, keeping current list: {e}")
            
            # Process each symbol (respect ALLOW_RANDOM_FALLBACK for real-data-only tests)
            allow_fallback = (
                PAPER_TRADING_MODE and not SCHWAB_SANDBOX_MODE
                and os.getenv('ALLOW_RANDOM_FALLBACK', 'true').lower() == 'true'
            )
            
            hold_count = 0
            signal_count = 0
            executed_count = 0
            timing_enabled = os.getenv('BOT_TIMING', 'false').lower() == 'true'
            signal_timeout_sec = max(0, int(os.getenv('GET_STRATEGY_SIGNAL_TIMEOUT_SECONDS', '0')))
            batch_size = max(1, min(64, int(os.getenv('BOT_SIGNAL_BATCH_SIZE', '16'))))  # parallel get_strategy_signal workers
            if timing_enabled:
                import time as _time
                bot._cycle_signal_breakdown = []
                signal_elapsed = 0.0
                execute_elapsed = 0.0
                cycle_start = _time.perf_counter()
            
            # Phase 1: get strategy signal for all symbols in parallel (batch_size workers)
            from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
            def _get_signal(sym):
                return bot.get_strategy_signal(sym, use_random_fallback=allow_fallback)
            
            signal_results = {}
            result_timeout = signal_timeout_sec if signal_timeout_sec > 0 else 120
            logger.info(f"Evaluating {len(scan_symbols)} symbols in parallel (batch size {batch_size})")
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                future_to_symbol = {executor.submit(_get_signal, sym): sym for sym in scan_symbols}
                for future in as_completed(future_to_symbol, timeout=result_timeout * len(scan_symbols) // max(1, batch_size) + 60):
                    if _bot_stop_event.is_set() or not _bot_running:
                        break
                    symbol = future_to_symbol[future]
                    try:
                        res = future.result(timeout=result_timeout)
                        signal_results[symbol] = res if isinstance(res, (list, tuple)) and len(res) >= 3 else (None, None, None)
                    except FuturesTimeoutError:
                        logger.warning(f"{symbol}: get_strategy_signal timed out ({result_timeout}s)")
                        signal_results[symbol] = (None, None, None)
                    except Exception as e:
                        logger.error(f"Strategy signal failed for {symbol}: {e}", exc_info=True)
                        signal_results[symbol] = (None, None, None)
            
            # Phase 2: process results in order (update candidate_decisions, execute trades)
            for index, symbol in enumerate(scan_symbols, 1):
                # Check if we should stop
                if _bot_stop_event.is_set() or not _bot_running:
                    logger.info("Stop signal received - exiting trading loop")
                    break
                
                res = signal_results.get(symbol, (None, None, None))
                signal, price, volume = (res[0], res[1], res[2]) if len(res) >= 3 else (None, None, None)
                
                # Timeout or missing result
                if signal is None and price is None and volume is None:
                    hold_count += 1
                    if hasattr(bot, 'candidate_decisions'):
                        bot.candidate_decisions[symbol] = {
                            'symbol': symbol, 'signal': '—', 'action': '—', 'price': None, 'volume': None,
                            'reason': 'Data timeout', 'cycle_number': cycle_count, 'updated_at': _naive_utcnow().isoformat() + 'Z'
                        }
                    continue
                
                if os.getenv('DEBUG', 'false').lower() == 'true':
                    logger.debug(f"[{index}/{len(scan_symbols)}] {symbol}: {signal}, price: {'${:.2f}'.format(price) if price is not None else 'N/A'}, vol: {f'{volume:,}' if volume is not None else 'N/A'}")
                
                if signal == 'HOLD':
                    hold_count += 1
                    # Hold = we own the stock, keep position (don't sell). No trade = we don't own it, no entry.
                    has_position = symbol in getattr(bot, 'positions', {})
                    if has_position:
                        logger.info(f"{symbol}: signal=HOLD (hold — keep position)")
                        reason_hold = 'Hold'
                    else:
                        logger.info(f"{symbol}: signal=HOLD (no trade — no entry)")
                        reason_hold = 'No trade'
                    if hasattr(bot, 'candidate_decisions'):
                        bot.candidate_decisions[symbol] = {
                            'symbol': symbol, 'signal': 'HOLD', 'action': '—', 'price': price, 'volume': volume,
                            'reason': reason_hold, 'cycle_number': cycle_count, 'updated_at': _naive_utcnow().isoformat() + 'Z'
                        }
                    continue
                
                if price is None or volume is None:
                    logger.warning(f"{symbol}: no market data (signal={signal}) — skip")
                    hold_count += 1
                    if hasattr(bot, 'candidate_decisions'):
                        bot.candidate_decisions[symbol] = {
                            'symbol': symbol, 'signal': signal, 'action': '—', 'price': None, 'volume': None,
                            'reason': 'No market data', 'cycle_number': cycle_count, 'updated_at': _naive_utcnow().isoformat() + 'Z'
                        }
                    continue
                
                action = bot._signal_to_action(symbol, signal)
                if action is None:
                    hold_count += 1
                    logger.info(f"{symbol}: signal={signal} but no action (position held)")
                    if hasattr(bot, 'candidate_decisions'):
                        bot.candidate_decisions[symbol] = {
                            'symbol': symbol, 'signal': signal, 'action': '—', 'price': price, 'volume': volume,
                            'reason': 'Position held', 'cycle_number': cycle_count, 'updated_at': _naive_utcnow().isoformat() + 'Z'
                        }
                    continue
                
                signal_count += 1
                logger.info(f"{symbol}: signal={signal} → order {action} @ ${price:.2f}, vol={volume:,}")
                if hasattr(bot, 'candidate_decisions'):
                    bot.candidate_decisions[symbol] = {
                        'symbol': symbol, 'signal': signal, 'action': action, 'price': price, 'volume': volume,
                        'reason': 'Order submitted', 'cycle_number': cycle_count, 'updated_at': _naive_utcnow().isoformat() + 'Z'
                    }
                
                # Exit-price refresh: re-fetch price immediately before SELL/COVER
                if EXIT_REFRESH_PRICE and action in ('SELL', 'COVER'):
                    try:
                        exit_price, _ = bot.get_stock_price(symbol, use_random_fallback=False)
                        if exit_price is not None:
                            price = exit_price
                            if os.getenv('DEBUG', 'false').lower() == 'true':
                                logger.debug(f"Exit price refresh for {symbol}: ${price:.2f}")
                    except (ValueError, TypeError):
                        pass
                
                # Execute trade (BUY, SELL, SHORT, or COVER)
                logger.info(f"Processing trade for {symbol} ({action}) at ${price:.2f}, volume: {volume:,}")
                try:
                    if timing_enabled:
                        _t0e = _time.perf_counter()
                    result = bot.execute_trade(symbol, action, price, volume=volume)
                    if timing_enabled:
                        execute_elapsed += _time.perf_counter() - _t0e
                    
                    if result and result.get('status') == 'error':
                        logger.error(f"Order failed for {symbol}: {result.get('message', 'Unknown error')}")
                        if hasattr(bot, 'candidate_decisions') and symbol in bot.candidate_decisions:
                            bot.candidate_decisions[symbol]['reason'] = 'Order failed'
                            bot.candidate_decisions[symbol]['updated_at'] = _naive_utcnow().isoformat() + 'Z'
                    elif result and result.get('status') in ('success', 'simulated'):
                        executed_count += 1
                        logger.info(f"Order filled for {symbol}: {result.get('message', result.get('status', 'Filled'))}")
                        if hasattr(bot, 'candidate_decisions') and symbol in bot.candidate_decisions:
                            bot.candidate_decisions[symbol]['reason'] = 'Filled'
                            bot.candidate_decisions[symbol]['updated_at'] = _naive_utcnow().isoformat() + 'Z'
                except Exception as e:
                    logger.error(f"Execution error for {symbol}: {e}", exc_info=True)
                    if hasattr(bot, 'candidate_decisions') and symbol in bot.candidate_decisions:
                        bot.candidate_decisions[symbol]['reason'] = 'Execution error'
                        bot.candidate_decisions[symbol]['updated_at'] = _naive_utcnow().isoformat() + 'Z'
                
                # Add delay between trades (0 in yfinance for continuous trading)
                if trade_delay > 0:
                    if _bot_stop_event.wait(timeout=trade_delay):
                        break
                else:
                    # Yield briefly (0.1s) so we don't spin at 100% CPU; still check stop
                    if _bot_stop_event.wait(timeout=0.1):
                        break
            
            # One line per cycle so logs show why no trades (HOLD vs executed)
            logger.info(f"Cycle #{cycle_count} complete: {len(scan_symbols)} symbols, HOLD/skip: {hold_count}, BUY/SELL signals: {signal_count}, filled: {executed_count}")
            
            # Cull "No trade" symbols so list becomes prospects only (stocks we trade or hold)
            cull_after = max(0, int(os.getenv('BOT_CULL_NO_TRADE_CYCLES', '3')))
            min_prospects = max(1, int(os.getenv('BOT_PROSPECTS_MIN_SIZE', '5')))
            positions = getattr(bot, 'positions', {})
            if cull_after > 0 and hasattr(bot, 'candidate_decisions'):
                for sym in list(scan_symbols):
                    if sym in positions:
                        bot.no_trade_streak[sym] = 0
                        continue
                    reason = (bot.candidate_decisions.get(sym) or {}).get('reason', '')
                    if reason == 'No trade':
                        bot.no_trade_streak[sym] = bot.no_trade_streak.get(sym, 0) + 1
                    else:
                        bot.no_trade_streak[sym] = 0
                to_cull = [
                    s for s in scan_symbols
                    if s not in positions and bot.no_trade_streak.get(s, 0) >= cull_after
                ]
                if to_cull:
                    scan_symbols = [s for s in scan_symbols if s not in to_cull]
                    for s in to_cull:
                        bot.no_trade_streak.pop(s, None)
                    bot.current_symbols = scan_symbols
                    logger.info(f"Culled {len(to_cull)} No-trade symbol(s): {to_cull[:10]}{'...' if len(to_cull) > 10 else ''} — prospects: {len(scan_symbols)}")
                # Replenish from feed if prospects list fell below minimum
                if len(scan_symbols) < min_prospects:
                    try:
                        replenish_max = max(min_prospects, min(MAX_DISCOVERED_STOCKS, int(os.getenv('BOT_PROSPECTS_REPLENISH_MAX', str(MAX_DISCOVERED_STOCKS)))))
                        fresh = _load_symbols_todays_best(bot, replenish_max, ENABLE_STOCK_SCREENER)
                        if fresh:
                            existing = set(scan_symbols)
                            added = [s for s in fresh if s not in existing][:replenish_max - len(scan_symbols)]
                            if added:
                                scan_symbols = list(scan_symbols) + added
                                bot.current_symbols = scan_symbols
                                logger.info(f"Replenished prospects: +{len(added)} symbol(s), total: {len(scan_symbols)}")
                    except Exception as e:
                        logger.warning(f"Replenish failed: {e}")
            
            # Optional timing summary (BOT_TIMING=true) to find next bottlenecks
            if timing_enabled:
                total_cycle = _time.perf_counter() - cycle_start
                breakdown_msg = ""
                if getattr(bot, '_cycle_signal_breakdown', None):
                    ohlcv_s = sum(p.get('ohlcv_s', 0) for p in bot._cycle_signal_breakdown)
                    strategy_s = sum(p.get('strategy_s', 0) for p in bot._cycle_signal_breakdown)
                    price_s = sum(p.get('price_s', 0) for p in bot._cycle_signal_breakdown)
                    breakdown_msg = f" | breakdown: ohlcv={ohlcv_s:.2f}s strategy={strategy_s:.2f}s price={price_s:.2f}s"
                logger.info(f"Cycle #{cycle_count} timing: get_strategy_signal={signal_elapsed:.2f}s ({len(scan_symbols)} sym), execute_trade={execute_elapsed:.2f}s ({executed_count} trades), total={total_cycle:.2f}s{breakdown_msg}")
                bot.last_cycle_timings = {
                    'get_strategy_signal_s': signal_elapsed,
                    'execute_trade_s': execute_elapsed,
                    'total_cycle_s': total_cycle,
                    'symbols': len(scan_symbols),
                    'trades': executed_count,
                }
                if getattr(bot, '_cycle_signal_breakdown', None):
                    bot.last_cycle_timings['ohlcv_s'] = sum(p.get('ohlcv_s', 0) for p in bot._cycle_signal_breakdown)
                    bot.last_cycle_timings['strategy_s'] = sum(p.get('strategy_s', 0) for p in bot._cycle_signal_breakdown)
                    bot.last_cycle_timings['price_s'] = sum(p.get('price_s', 0) for p in bot._cycle_signal_breakdown)
            
            if hasattr(bot, 'stored_messages'):
                bot.stored_messages.add_message(
                    f"Cycle #{cycle_count} complete: {hold_count} HOLD, {signal_count} signals, {executed_count} filled",
                    category='info'
                )
            
            # Persist state for restart recovery (resume if within BOT_RECOVERY_WINDOW_MINUTES)
            try:
                last_cycle_at = _naive_utcnow().isoformat() + 'Z'
                save_bot_state(
                    last_cycle_at=last_cycle_at,
                    current_symbols=list(scan_symbols),
                    no_trade_streak=dict(getattr(bot, 'no_trade_streak', {}) or {}),
                    cycle_number=cycle_count,
                )
            except Exception as save_err:
                logger.debug(f"Failed to save bot state: {save_err}")
            
            # Wait before next cycle (if not stopped). YFinance: 1s default; others: WEB_GUI_CYCLE_DELAY or 5s.
            if not _bot_stop_event.is_set() and _bot_running:
                logger.info(f"Continuous mode: completed cycle #{cycle_count}, starting next cycle")
                _bot_stop_event.wait(timeout=cycle_delay)
        
        logger.info("Bot loop stopped")
        
    except Exception as e:
        logger.error(f"Error in bot loop: {e}", exc_info=True)
    finally:
        _bot_running = False
        if bot:
            if hasattr(bot, 'running'):
                bot.running = False
        logger.info("Bot loop exited")

def stop_bot():
    """
    Stop the bot (pauses trading but keeps instance alive)
    """
    global _bot_running
    
    if not _bot_running:
        logger.warning("Bot is not running")
        return False
    
    try:
        logger.info("Stopping bot...")
        
        bot = get_bot_instance()
        if bot:
            if hasattr(bot, 'running'):
                bot.running = False
        
        _bot_running = False
        _bot_stop_event.set()
        
        logger.info("Bot stop signal sent - waiting for bot loop to exit")
        return True
    except Exception as e:
        logger.error(f"Failed to stop bot: {e}", exc_info=True)
        return False

def shutdown_bot():
    """
    Shutdown the bot completely (stops and cleans up)
    Works whether bot is running or already stopped
    """
    global _bot_running, _bot_instance
    
    try:
        # Stop the bot first (if running)
        # This is safe to call even if bot is already stopped
        if _bot_running:
            stop_bot()
        
        # Wait for thread to finish (with increased timeout for long operations)
        if _bot_thread and _bot_thread.is_alive():
            logger.info("Waiting for bot thread to finish...")
            _bot_thread.join(timeout=10.0)
            if _bot_thread.is_alive():
                logger.warning("Bot thread did not stop within 10 second timeout - forcing shutdown")
                # Thread is daemon, so it will be terminated when process exits during shutdown sequence
        
        # Clean up bot instance (always, even if already stopped)
        _bot_instance = None
        set_bot_instance(None)
        _bot_running = False
        
        # Clear the stop event for next start
        _bot_stop_event.clear()
        
        logger.info("Bot shutdown complete")
        return True
    except Exception as e:
        logger.error(f"Failed to shutdown bot: {e}", exc_info=True)
        return False

def is_bot_running() -> bool:
    """Check if bot is currently running"""
    return _bot_running

def get_bot_status() -> dict:
    """
    Get comprehensive bot status
    """
    bot = get_bot_instance()
    
    # Determine mode from environment if bot not available (use 'dryrun-live' to match frontend)
    paper_mode = os.getenv('PAPER_TRADING_MODE', 'true').lower() == 'true'
    sandbox_mode = os.getenv('SCHWAB_SANDBOX_MODE', 'false').lower() == 'true'
    dry_run = os.getenv('DRY_RUN_MODE', 'false').lower() == 'true'
    
    if not bot:
        if dry_run:
            mode = 'dryrun-live'
        elif not paper_mode:
            mode = 'live'
        elif sandbox_mode:
            mode = 'sandbox'
        else:
            mode = 'yfinance'
        
        return {
            "running": False,
            "mode": mode,
            "initialized": False
        }
    
    # Get mode from bot
    mode = 'unknown'
    if hasattr(bot, 'mode') and bot.mode:
        mode = bot.mode
    elif hasattr(bot, 'trading_mode') and bot.trading_mode:
        mode = bot.trading_mode
    else:
        # Fallback: determine from environment
        if dry_run:
            mode = 'dryrun-live'
        elif not paper_mode:
            mode = 'live'
        elif sandbox_mode:
            mode = 'sandbox'
        else:
            mode = 'yfinance'
    
    no_trade_reasons = getattr(bot, 'no_trade_reasons', None)
    if no_trade_reasons is None:
        no_trade_reasons = []

    return {
        "running": getattr(bot, 'running', False) and _bot_running,
        "mode": mode,
        "initialized": True,
        "capital": getattr(bot, 'total_capital', 0.0),
        "positions": len(getattr(bot, 'positions', {})),
        "total_trades": len(getattr(bot, 'trade_history', [])),
        "no_trade_reasons": no_trade_reasons,
    }
