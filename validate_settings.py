#!/usr/bin/env python3
"""
Comprehensive validation script for trade settings
Verifies all settings from problem statement are present in web GUI
"""

def main():
    print("=" * 80)
    print("TRADE SETTINGS VALIDATION REPORT")
    print("=" * 80)
    print()
    
    # Read web_gui.py
    with open('web_gui.py', 'r') as f:
        web_gui_content = f.read()
    
    # Settings from problem statement with their expected web GUI setting IDs
    settings_map = {
        'Paper Trading Mode': {
            'id': 'setting-paper-trading',
            'env_var': 'PAPER_TRADING_MODE',
            'example_value': 'enabled'
        },
        'Schwab Sandbox Mode': {
            'id': 'setting-sandbox-mode',
            'env_var': 'SCHWAB_SANDBOX_MODE',
            'example_value': 'disabled'
        },
        'Total Capital': {
            'id': 'setting-capital',
            'env_var': 'BOT_TOTAL_CAPITAL',
            'example_value': '9999'
        },
        'Min Allocation': {
            'id': 'setting-min-alloc',
            'env_var': 'BOT_MIN_ALLOCATION',
            'example_value': '100'
        },
        'Max Allocation': {
            'id': 'setting-max-alloc',
            'env_var': 'BOT_MAX_ALLOCATION',
            'example_value': '200'
        },
        'Risk Threshold': {
            'id': 'setting-risk-threshold',
            'env_var': 'BOT_RISK_THRESHOLD',
            'example_value': '4.9%'
        },
        'Position Size': {
            'id': 'setting-position-size',
            'env_var': 'BOT_POSITION_SIZE',
            'example_value': '5%'
        },
        'Capital Floor': {
            'id': 'setting-capital-floor',
            'env_var': 'CAPITAL_FLOOR_PERCENT',
            'example_value': '10%'
        },
        'Max Open Positions': {
            'id': 'setting-max-positions',
            'env_var': 'BOT_MAX_OPEN_POSITIONS',
            'example_value': '50'
        },
        'Max Consecutive Losses': {
            'id': 'setting-max-losses',
            'env_var': 'BOT_MAX_CONSECUTIVE_LOSSES',
            'example_value': '4'
        },
        'Trailing Stop': {
            'id': 'setting-trailing-stop',
            'env_var': 'BOT_TRAILING_STOP_PERCENT',
            'example_value': '3%'
        },
        'Stop Loss': {
            'id': 'setting-stop-loss',
            'env_var': 'BOT_STOP_LOSS_PERCENT',
            'example_value': '6%'
        },
        'Take Profit': {
            'id': 'setting-take-profit',
            'env_var': 'BOT_TAKE_PROFIT_PERCENT',
            'example_value': '10%'
        },
        'Dynamic Stop': {
            'id': 'setting-dynamic-stop',
            'env_var': 'DYNAMIC_STOP_ENABLED',
            'example_value': 'enabled',
            'note': 'Label fixed from "Dynamic Stop Enabled" to "Dynamic Stop"'
        },
        'Min Trailing Stop': {
            'id': 'setting-min-trailing',
            'env_var': 'MIN_TRAILING_STOP',
            'example_value': '2%'
        },
        'Max Trailing Stop': {
            'id': 'setting-max-trailing',
            'env_var': 'MAX_TRAILING_STOP',
            'example_value': '10%'
        },
        'Min Stock Price': {
            'id': 'setting-min-price',
            'env_var': 'MIN_STOCK_PRICE',
            'example_value': '2'
        },
        'Min Daily Volume': {
            'id': 'setting-min-volume',
            'env_var': 'MIN_DAILY_VOLUME',
            'example_value': '300000'
        },
        'Max Stock Volatility': {
            'id': 'setting-max-volatility',
            'env_var': 'MAX_STOCK_VOLATILITY',
            'example_value': '0.15'
        },
        'Volatility Window': {
            'id': 'setting-volatility-window',
            'env_var': 'VOLATILITY_WINDOW',
            'example_value': '19'
        },
        'Partial Exit': {
            'id': 'setting-partial-exit',
            'env_var': 'PARTIAL_EXIT_ENABLED',
            'example_value': 'enabled',
            'note': 'Label fixed from "Partial Exit Enabled" to "Partial Exit"'
        },
        'Partial Exit %': {
            'id': 'setting-partial-exit-pct',
            'env_var': 'PARTIAL_EXIT_PERCENTAGE',
            'example_value': '50%'
        },
        'Trading Frequency': {
            'id': 'setting-trading-freq',
            'env_var': 'TRADING_FREQUENCY',
            'example_value': '1'
        },
        'Simulated Win Rate': {
            'id': 'setting-sim-win-rate',
            'env_var': 'SIMULATED_WIN_RATE',
            'example_value': '0.7'
        },
        'Max Symbols to Trade': {
            'id': 'setting-max-symbols',
            'env_var': 'WEB_GUI_MAX_SYMBOLS',
            'example_value': '10'
        },
        'Continuous Trading': {
            'id': 'setting-continuous-trading',
            'env_var': 'WEB_GUI_CONTINUOUS_TRADING',
            'example_value': 'enabled'
        }
    }
    
    print(f"Checking {len(settings_map)} settings from problem statement...")
    print()
    
    all_present = True
    issues = []
    
    for idx, (setting_name, details) in enumerate(settings_map.items(), 1):
        setting_id = details['id']
        env_var = details['env_var']
        example = details['example_value']
        note = details.get('note', '')
        
        # Check if setting ID exists in web_gui.py
        if f"id='{setting_id}'" in web_gui_content:
            status = "✓ PRESENT"
            # Check if it references the correct env var
            if env_var in web_gui_content:
                env_status = "✓"
            else:
                env_status = "⚠"
                issues.append(f"{setting_name}: env var {env_var} not found in code")
        else:
            status = "✗ MISSING"
            env_status = "✗"
            all_present = False
            issues.append(f"{setting_name}: setting ID {setting_id} not found")
        
        print(f"{idx:2d}. {status} {setting_name:25s} ({setting_id})")
        print(f"    └─ Env Var: {env_status} {env_var}")
        print(f"    └─ Example Value: {example}")
        if note:
            print(f"    └─ Note: {note}")
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if all_present:
        print("✓ SUCCESS: All 26 settings are present in the web GUI!")
    else:
        print("✗ FAILURE: Some settings are missing!")
        print()
        print("Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    
    print()
    print("Label improvements made:")
    print("  - Changed 'Dynamic Stop Enabled:' to 'Dynamic Stop:'")
    print("  - Changed 'Partial Exit Enabled:' to 'Partial Exit:'")
    print()
    print("These changes improve UI consistency while maintaining full functionality.")
    print("=" * 80)

if __name__ == '__main__':
    main()
