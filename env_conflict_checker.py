#!/usr/bin/env python3
"""
Environment Variable Conflict Checker

This module checks for conflicting or redundant settings in the .env file
and provides clear warnings to users about potential configuration issues.
"""

import os
from typing import List, Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class EnvConflict:
    """Represents a configuration conflict"""
    
    def __init__(self, severity: str, title: str, description: str, 
                 affected_vars: List[str], suggestion: str):
        """
        Initialize a configuration conflict instance.
        
        Args:
            severity: Severity level ('ERROR', 'WARNING', or 'INFO')
            title: Brief title describing the conflict
            description: Detailed description of the issue
            affected_vars: List of environment variable names involved
            suggestion: Recommendation for resolving the conflict
        """
        self.severity = severity  # 'ERROR', 'WARNING', 'INFO'
        self.title = title
        self.description = description
        self.affected_vars = affected_vars
        self.suggestion = suggestion
    
    def __str__(self):
        """
        Return a formatted string representation of the conflict.
        
        Returns:
            Multi-line string with severity, title, variables, issue, and suggestion
        """
        vars_str = ', '.join(self.affected_vars)
        return f"[{self.severity}] {self.title}\n  Variables: {vars_str}\n  Issue: {self.description}\n  Suggestion: {self.suggestion}"


def check_env_conflicts() -> List[EnvConflict]:
    """
    Check for conflicts in environment variables
    
    Returns:
        List of EnvConflict objects describing any issues found
    """
    conflicts = []
    
    # Load environment variables
    paper_trading = os.getenv('PAPER_TRADING_MODE', 'true').lower() == 'true'
    sandbox_mode = os.getenv('SCHWAB_SANDBOX_MODE', 'false').lower() == 'true'
    api_enabled_str = os.getenv('SCHWAB_API_ENABLED', 'on').lower()
    api_enabled = api_enabled_str in ('on', 'true', '1', 'yes')
    enable_pdt = os.getenv('ENABLE_PDT_RULES', 'true').lower() == 'true'
    non_interactive = os.getenv('NON_INTERACTIVE', 'false').lower() == 'true'
    
    # Conflict 1: ENABLE_PDT_RULES is obsolete
    # Changed to INFO severity - this is informational, not a warning
    if enable_pdt and paper_trading:
        conflicts.append(EnvConflict(
            severity='INFO',  # Changed from WARNING to INFO - not critical
            title='Obsolete PDT Rules Setting',
            description='ENABLE_PDT_RULES=true is set but has no effect in paper trading mode. PDT rules are automatically determined by PAPER_TRADING_MODE (disabled in paper mode, enabled in live mode).',
            affected_vars=['ENABLE_PDT_RULES', 'PAPER_TRADING_MODE'],
            suggestion='Remove ENABLE_PDT_RULES from your .env file as it is no longer used. PDT enforcement is controlled solely by PAPER_TRADING_MODE.'
        ))
    
    # Conflict 2: Sandbox mode disabled + API disabled is redundant
    if not sandbox_mode and not api_enabled and paper_trading:
        conflicts.append(EnvConflict(
            severity='INFO',
            title='Redundant Configuration',
            description='Both SCHWAB_SANDBOX_MODE=false and SCHWAB_API_ENABLED=off are set. When API is disabled, sandbox mode setting is irrelevant.',
            affected_vars=['SCHWAB_SANDBOX_MODE', 'SCHWAB_API_ENABLED'],
            suggestion='When SCHWAB_API_ENABLED=off, you can remove SCHWAB_SANDBOX_MODE setting as it has no effect.'
        ))
    
    # Conflict 3: Live mode with API disabled
    if not paper_trading and not api_enabled:
        conflicts.append(EnvConflict(
            severity='ERROR',
            title='Invalid Live Trading Configuration',
            description='Cannot run in live mode (PAPER_TRADING_MODE=false) with Schwab API disabled (SCHWAB_API_ENABLED=off). Live trading requires API connectivity.',
            affected_vars=['PAPER_TRADING_MODE', 'SCHWAB_API_ENABLED'],
            suggestion='Set SCHWAB_API_ENABLED=on for live trading, or set PAPER_TRADING_MODE=true for simulation mode.'
        ))
    
    # Conflict 4: NON_INTERACTIVE without token.json and API enabled
    token_exists = os.path.exists(os.getenv('SCHWAB_TOKEN_PATH', 'token.json'))
    if non_interactive and api_enabled and not token_exists:
        conflicts.append(EnvConflict(
            severity='WARNING',
            title='Non-Interactive Mode Missing Token',
            description='NON_INTERACTIVE=true is set with SCHWAB_API_ENABLED=on, but token.json does not exist. The bot will fall back to yfinance simulation mode.',
            affected_vars=['NON_INTERACTIVE', 'SCHWAB_API_ENABLED'],
            suggestion='Either: (1) Run bot interactively first to generate token.json, (2) Set SCHWAB_API_ENABLED=off to explicitly use yfinance mode, or (3) Set NON_INTERACTIVE=false if you can run interactively.'
        ))
    
    # Conflict 5: Sandbox mode with API disabled
    if sandbox_mode and not api_enabled:
        conflicts.append(EnvConflict(
            severity='WARNING',
            title='Sandbox Mode with API Disabled',
            description='SCHWAB_SANDBOX_MODE=true is set, but SCHWAB_API_ENABLED=off disables all API connectivity. Sandbox mode requires API to be enabled.',
            affected_vars=['SCHWAB_SANDBOX_MODE', 'SCHWAB_API_ENABLED'],
            suggestion='Set SCHWAB_API_ENABLED=on to use sandbox mode, or set SCHWAB_SANDBOX_MODE=false if you want pure simulation without API.'
        ))
    
    # Risk parameter validation
    try:
        risk_threshold = float(os.getenv('BOT_RISK_THRESHOLD', '0.02'))
        stop_loss = float(os.getenv('BOT_STOP_LOSS_PERCENT', '0.06'))
        take_profit = float(os.getenv('BOT_TAKE_PROFIT_PERCENT', '0.10'))
        position_size = float(os.getenv('BOT_POSITION_SIZE', '0.01'))
        
        # Conflict 6: Stop loss too high (> 10%)
        if stop_loss > 0.10:
            conflicts.append(EnvConflict(
                severity='WARNING',
                title='High Stop Loss Percentage',
                description=f'BOT_STOP_LOSS_PERCENT={stop_loss:.0%} is unusually high. Most trading strategies use 5-10% stop losses.',
                affected_vars=['BOT_STOP_LOSS_PERCENT'],
                suggestion=f'Consider reducing BOT_STOP_LOSS_PERCENT to 0.06 (6%) or lower for better risk management.'
            ))
        
        # Conflict 7: Take profit too high (> 20%)
        if take_profit > 0.20:
            conflicts.append(EnvConflict(
                severity='WARNING',
                title='High Take Profit Percentage',
                description=f'BOT_TAKE_PROFIT_PERCENT={take_profit:.0%} is unusually high. This may cause you to miss profit-taking opportunities.',
                affected_vars=['BOT_TAKE_PROFIT_PERCENT'],
                suggestion=f'Consider reducing BOT_TAKE_PROFIT_PERCENT to 0.10 (10%) or lower for more frequent profit-taking.'
            ))
        
        # Conflict 8: Risk threshold misalignment with position size
        if position_size > risk_threshold * 2:
            conflicts.append(EnvConflict(
                severity='WARNING',
                title='Position Size vs Risk Threshold Mismatch',
                description=f'BOT_POSITION_SIZE ({position_size:.1%}) is much larger than BOT_RISK_THRESHOLD ({risk_threshold:.1%}). This may lead to oversized positions.',
                affected_vars=['BOT_POSITION_SIZE', 'BOT_RISK_THRESHOLD'],
                suggestion=f'Align these values: typically position_size should be close to risk_threshold. Consider setting BOT_POSITION_SIZE to {risk_threshold:.4f} ({risk_threshold:.1%}).'
            ))
        
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not validate risk parameters: {e}")
    
    return conflicts


def print_conflict_report(conflicts: List[EnvConflict]) -> None:
    """
    Print a formatted report of configuration conflicts
    
    Args:
        conflicts: List of EnvConflict objects to report
    """
    if not conflicts:
        print("\n✓ No configuration conflicts detected")
        return
    
    # Group by severity
    errors = [c for c in conflicts if c.severity == 'ERROR']
    warnings = [c for c in conflicts if c.severity == 'WARNING']
    infos = [c for c in conflicts if c.severity == 'INFO']
    
    print("\n" + "=" * 70)
    print("ENVIRONMENT CONFIGURATION CONFLICT REPORT")
    print("=" * 70)
    
    if errors:
        print(f"\n🔴 ERRORS ({len(errors)}) - Must be fixed:")
        print("-" * 70)
        for i, conflict in enumerate(errors, 1):
            print(f"\n{i}. {conflict.title}")
            print(f"   Variables: {', '.join(conflict.affected_vars)}")
            print(f"   Issue: {conflict.description}")
            print(f"   ⚠️  Fix: {conflict.suggestion}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}) - Should be addressed:")
        print("-" * 70)
        for i, conflict in enumerate(warnings, 1):
            print(f"\n{i}. {conflict.title}")
            print(f"   Variables: {', '.join(conflict.affected_vars)}")
            print(f"   Issue: {conflict.description}")
            print(f"   💡 Suggestion: {conflict.suggestion}")
    
    if infos:
        print(f"\nℹ️  INFO ({len(infos)}) - Informational:")
        print("-" * 70)
        for i, conflict in enumerate(infos, 1):
            print(f"\n{i}. {conflict.title}")
            print(f"   Variables: {', '.join(conflict.affected_vars)}")
            print(f"   Note: {conflict.description}")
            print(f"   💡 Tip: {conflict.suggestion}")
    
    print("\n" + "=" * 70)
    print(f"Total issues: {len(errors)} errors, {len(warnings)} warnings, {len(infos)} info")
    print("=" * 70 + "\n")


def create_sanitized_env(source_env_path: str = None) -> Dict[str, str]:
    """
    Create a sanitized environment configuration based on current settings,
    resolving conflicts automatically.
    
    Args:
        source_env_path: Path to source .env file (optional)
    
    Returns:
        Dictionary of sanitized environment variables
    """
    # Load current values
    sanitized = {}
    
    # Core trading mode settings
    paper_trading = os.getenv('PAPER_TRADING_MODE', 'true').lower() == 'true'
    api_enabled_str = os.getenv('SCHWAB_API_ENABLED', 'on').lower()
    api_enabled = api_enabled_str in ('on', 'true', '1', 'yes')
    
    sanitized['PAPER_TRADING_MODE'] = 'true' if paper_trading else 'false'
    
    # If API is disabled, force sandbox off and paper trading on
    if not api_enabled:
        sanitized['SCHWAB_API_ENABLED'] = 'off'
        sanitized['SCHWAB_SANDBOX_MODE'] = 'false'
        sanitized['PAPER_TRADING_MODE'] = 'true'  # Force paper mode
    else:
        sanitized['SCHWAB_API_ENABLED'] = 'on'
        # Sandbox mode only matters if API is enabled
        if paper_trading:
            sanitized['SCHWAB_SANDBOX_MODE'] = os.getenv('SCHWAB_SANDBOX_MODE', 'false')
        else:
            sanitized['SCHWAB_SANDBOX_MODE'] = 'false'  # Always false in live mode
    
    # Remove obsolete ENABLE_PDT_RULES (it's determined by PAPER_TRADING_MODE)
    # Don't include it in sanitized config
    
    # NON_INTERACTIVE - keep if set, otherwise default to false
    non_interactive = os.getenv('NON_INTERACTIVE', 'false')
    if non_interactive.lower() == 'true':
        sanitized['NON_INTERACTIVE'] = 'true'
    
    # Copy other safe configuration values
    safe_vars = [
        'BOT_TOTAL_CAPITAL', 'SCAN_SYMBOLS_FILE',
        'BOT_MAX_OPEN_POSITIONS', 'BOT_MAX_CONSECUTIVE_LOSSES',
        'TRADING_FREQUENCY', 'DYNAMIC_STOP_ENABLED', 'VOLATILITY_WINDOW',
        'MIN_STOCK_PRICE', 'MAX_STOCK_PRICE', 'MIN_DAILY_VOLUME', 'MAX_STOCK_VOLATILITY',
        'PARTIAL_EXIT_ENABLED', 'PARTIAL_EXIT_PERCENTAGE',
        'SIMULATED_WIN_RATE', 'VOLATILITY_NORMALIZATION_MIN', 'VOLATILITY_NORMALIZATION_RANGE',
        'CAPITAL_FLOOR_PERCENT', 'ENABLE_ALERTS', 'ALERT_EMAIL',
        'WEB_GUI_MAX_SYMBOLS', 'WEB_GUI_CONTINUOUS_TRADING', 'WEB_GUI_CYCLE_DELAY',
        'WEB_GUI_DEBUG', 'USER_PROFILE_NAME', 'USER_PROFILE_USERNAME',
        'BOT_MAX_CPU_PERCENT', 'BOT_MAX_MEMORY_PERCENT', 'BOT_THROTTLE_DELAY',
        'BOT_ENABLE_THROTTLING', 'SENTIMENT_METHOD'
    ]
    
    for var in safe_vars:
        value = os.getenv(var)
        if value:
            sanitized[var] = value
    
    # Risk parameters - use safer defaults
    sanitized['BOT_RISK_THRESHOLD'] = os.getenv('BOT_RISK_THRESHOLD', '0.02')
    sanitized['BOT_MIN_ALLOCATION'] = os.getenv('BOT_MIN_ALLOCATION', '100')
    sanitized['BOT_MAX_ALLOCATION'] = os.getenv('BOT_MAX_ALLOCATION', '300')
    
    # Adjust risky parameters to safer values
    stop_loss = float(os.getenv('BOT_STOP_LOSS_PERCENT', '0.06'))
    if stop_loss > 0.10:
        sanitized['BOT_STOP_LOSS_PERCENT'] = '0.06'  # Cap at 6%
        logger.info(f"Adjusted BOT_STOP_LOSS_PERCENT from {stop_loss:.0%} to 6% for safety")
    else:
        sanitized['BOT_STOP_LOSS_PERCENT'] = str(stop_loss)
    
    take_profit = float(os.getenv('BOT_TAKE_PROFIT_PERCENT', '0.10'))
    if take_profit > 0.20:
        sanitized['BOT_TAKE_PROFIT_PERCENT'] = '0.10'  # Cap at 10%
        logger.info(f"Adjusted BOT_TAKE_PROFIT_PERCENT from {take_profit:.0%} to 10% for better profit-taking")
    else:
        sanitized['BOT_TAKE_PROFIT_PERCENT'] = str(take_profit)
    
    # Align position size with risk threshold
    risk_threshold = float(sanitized['BOT_RISK_THRESHOLD'])
    sanitized['BOT_POSITION_SIZE'] = str(risk_threshold)
    
    # Trailing stop
    sanitized['BOT_TRAILING_STOP_PERCENT'] = os.getenv('BOT_TRAILING_STOP_PERCENT', '0.03')
    sanitized['MIN_TRAILING_STOP'] = os.getenv('MIN_TRAILING_STOP', '0.02')
    sanitized['MAX_TRAILING_STOP'] = os.getenv('MAX_TRAILING_STOP', '0.10')
    
    sanitized['BOT_RISK_FREE_RATE'] = os.getenv('BOT_RISK_FREE_RATE', '0.01')
    
    return sanitized


def write_sanitized_env(output_path: str = '.env.sanitized') -> None:
    """
    Write sanitized environment configuration to a file
    
    Args:
        output_path: Path to write sanitized config
    """
    sanitized = create_sanitized_env()
    
    with open(output_path, 'w') as f:
        f.write("# Sanitized Environment Configuration\n")
        f.write("# Generated automatically with conflict resolution\n")
        f.write("# Review and rename to .env if acceptable\n\n")
        
        # Write in logical groups
        f.write("# Core Trading Mode Configuration\n")
        mode_vars = ['PAPER_TRADING_MODE', 'SCHWAB_SANDBOX_MODE', 'SCHWAB_API_ENABLED', 'NON_INTERACTIVE']
        for var in mode_vars:
            if var in sanitized:
                f.write(f"{var}={sanitized[var]}\n")
        
        f.write("\n# Risk Management Configuration\n")
        risk_vars = ['BOT_RISK_THRESHOLD', 'BOT_MIN_ALLOCATION', 'BOT_MAX_ALLOCATION',
                     'BOT_TRAILING_STOP_PERCENT', 'BOT_STOP_LOSS_PERCENT', 'BOT_TAKE_PROFIT_PERCENT',
                     'BOT_POSITION_SIZE', 'BOT_RISK_FREE_RATE']
        for var in risk_vars:
            if var in sanitized:
                f.write(f"{var}={sanitized[var]}\n")
        
        f.write("\n# Trading Behavior Configuration\n")
        trading_vars = ['BOT_TOTAL_CAPITAL', 'BOT_MAX_OPEN_POSITIONS', 'BOT_MAX_CONSECUTIVE_LOSSES',
                       'TRADING_FREQUENCY', 'SCAN_SYMBOLS_FILE']
        for var in trading_vars:
            if var in sanitized:
                f.write(f"{var}={sanitized[var]}\n")
        
        f.write("\n# Dynamic Trailing Stop Configuration\n")
        stop_vars = ['DYNAMIC_STOP_ENABLED', 'VOLATILITY_WINDOW', 'MIN_TRAILING_STOP', 'MAX_TRAILING_STOP']
        for var in stop_vars:
            if var in sanitized:
                f.write(f"{var}={sanitized[var]}\n")
        
        f.write("\n# Stock Filtering Configuration\n")
        filter_vars = ['MIN_STOCK_PRICE', 'MAX_STOCK_PRICE', 'MIN_DAILY_VOLUME', 'MAX_STOCK_VOLATILITY']
        for var in filter_vars:
            if var in sanitized:
                f.write(f"{var}={sanitized[var]}\n")
        
        f.write("\n# Position Management Configuration\n")
        position_vars = ['PARTIAL_EXIT_ENABLED', 'PARTIAL_EXIT_PERCENTAGE']
        for var in position_vars:
            if var in sanitized:
                f.write(f"{var}={sanitized[var]}\n")
        
        f.write("\n# Simulation and Volatility Settings\n")
        sim_vars = ['SIMULATED_WIN_RATE', 'VOLATILITY_NORMALIZATION_MIN', 'VOLATILITY_NORMALIZATION_RANGE']
        for var in sim_vars:
            if var in sanitized:
                f.write(f"{var}={sanitized[var]}\n")
        
        f.write("\n# Capital Floor and Alerts\n")
        alert_vars = ['CAPITAL_FLOOR_PERCENT', 'ENABLE_ALERTS', 'ALERT_EMAIL', 'SENTIMENT_METHOD']
        for var in alert_vars:
            if var in sanitized:
                f.write(f"{var}={sanitized[var]}\n")
        
        f.write("\n# Web GUI Configuration\n")
        gui_vars = ['WEB_GUI_MAX_SYMBOLS', 'WEB_GUI_CONTINUOUS_TRADING', 'WEB_GUI_CYCLE_DELAY',
                   'WEB_GUI_DEBUG', 'USER_PROFILE_NAME', 'USER_PROFILE_USERNAME']
        for var in gui_vars:
            if var in sanitized:
                f.write(f"{var}={sanitized[var]}\n")
        
        f.write("\n# Resource Throttling Configuration\n")
        throttle_vars = ['BOT_MAX_CPU_PERCENT', 'BOT_MAX_MEMORY_PERCENT', 'BOT_THROTTLE_DELAY',
                        'BOT_ENABLE_THROTTLING']
        for var in throttle_vars:
            if var in sanitized:
                f.write(f"{var}={sanitized[var]}\n")
    
    print(f"\n✓ Sanitized configuration written to: {output_path}")
    print(f"  Review the file and rename to .env if acceptable")


if __name__ == '__main__':
    """Run conflict checker as standalone script"""
    # Try to load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Loaded environment from .env file")
    except ImportError:
        print("⚠️  python-dotenv not available, using system environment variables")
    
    # Check for conflicts
    conflicts = check_env_conflicts()
    print_conflict_report(conflicts)
    
    # Ask if user wants sanitized config
    if conflicts:
        print("\nWould you like to generate a sanitized .env file? (y/n): ", end='')
        try:
            response = input().strip().lower()
            if response == 'y':
                write_sanitized_env()
        except (EOFError, KeyboardInterrupt):
            print("\nSkipping sanitized file generation")
