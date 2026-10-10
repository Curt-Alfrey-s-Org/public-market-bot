#!/usr/bin/env python3
"""
Verify parameter consistency and identify potential conflicts in trading bot configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_float_env(key, default):
    """Safely get float environment variable"""
    return float(os.getenv(key, default))

def get_int_env(key, default):
    """Safely get integer environment variable"""
    return int(os.getenv(key, default))

def check_parameter_consistency():
    """Check for parameter conflicts and inconsistencies"""
    
    print("=" * 70)
    print("Trading Bot Parameter Consistency Check")
    print("=" * 70)
    
    # Stock filtering parameters
    min_stock_price = get_float_env('MIN_STOCK_PRICE', 5.0)
    max_stock_price = get_float_env('MAX_STOCK_PRICE', 1000.0)
    min_daily_volume = get_int_env('MIN_DAILY_VOLUME', 500000)
    max_volatility = get_float_env('MAX_STOCK_VOLATILITY', 0.15)
    
    # Capital and allocation parameters
    total_capital = get_float_env('BOT_TOTAL_CAPITAL', 10000)
    min_allocation = get_float_env('BOT_MIN_ALLOCATION', 100)
    max_allocation = get_float_env('BOT_MAX_ALLOCATION', 5000)
    position_size = get_float_env('BOT_POSITION_SIZE', 0.01)
    
    # Risk management parameters
    risk_threshold = get_float_env('BOT_RISK_THRESHOLD', 0.02)
    stop_loss = get_float_env('BOT_STOP_LOSS_PERCENT', 0.06)
    take_profit = get_float_env('BOT_TAKE_PROFIT_PERCENT', 0.1)
    trailing_stop = get_float_env('BOT_TRAILING_STOP_PERCENT', 0.03)
    
    # Position limits
    max_positions = get_int_env('BOT_MAX_OPEN_POSITIONS', 50)
    max_consecutive_losses = get_int_env('BOT_MAX_CONSECUTIVE_LOSSES', 3)
    
    issues = []
    warnings = []
    
    print("\n📊 STOCK FILTERING PARAMETERS")
    print("-" * 70)
    print(f"  MIN_STOCK_PRICE:       ${min_stock_price:.2f}")
    print(f"  MAX_STOCK_PRICE:       ${max_stock_price:.2f}")
    print(f"  Price Range:           ${min_stock_price:.2f} - ${max_stock_price:.2f}")
    print(f"  MIN_DAILY_VOLUME:      {min_daily_volume:,}")
    print(f"  MAX_STOCK_VOLATILITY:  {max_volatility:.1%}")
    
    # Check 1: MIN_STOCK_PRICE < MAX_STOCK_PRICE
    if min_stock_price >= max_stock_price:
        issues.append(f"❌ MIN_STOCK_PRICE (${min_stock_price}) >= MAX_STOCK_PRICE (${max_stock_price})")
    else:
        print(f"  ✅ Price range is valid")
    
    # Check 2: Price range is reasonable
    price_range = max_stock_price - min_stock_price
    if price_range < 10:
        warnings.append(f"⚠️  Price range (${price_range:.2f}) is very narrow")
    
    # Check 3: Warn about excluding high-value stocks
    if max_stock_price <= 100:
        warnings.append(f"⚠️  MAX_STOCK_PRICE (${max_stock_price:.2f}) will exclude high-value stocks (many popular stocks trade above $100)")
    
    print("\n💰 CAPITAL AND ALLOCATION PARAMETERS")
    print("-" * 70)
    print(f"  BOT_TOTAL_CAPITAL:     ${total_capital:,.2f}")
    print(f"  BOT_MIN_ALLOCATION:    ${min_allocation:.2f}")
    print(f"  BOT_MAX_ALLOCATION:    ${max_allocation:.2f}")
    print(f"  BOT_POSITION_SIZE:     {position_size:.1%} of capital")
    print(f"  Calculated position:   ${total_capital * position_size:.2f}")
    
    # Check 4: MIN_ALLOCATION <= MAX_ALLOCATION
    if min_allocation > max_allocation:
        issues.append(f"❌ MIN_ALLOCATION (${min_allocation}) > MAX_ALLOCATION (${max_allocation})")
    else:
        print(f"  ✅ Allocation range is valid")
    
    # Check 5: MAX_ALLOCATION <= TOTAL_CAPITAL
    if max_allocation > total_capital:
        issues.append(f"❌ MAX_ALLOCATION (${max_allocation}) > TOTAL_CAPITAL (${total_capital})")
    
    # Check 6: Position size calculation consistency
    calculated_position = total_capital * position_size
    if calculated_position < min_allocation:
        warnings.append(f"⚠️  Calculated position (${calculated_position:.2f}) < MIN_ALLOCATION (${min_allocation:.2f})")
    
    if calculated_position > max_allocation:
        warnings.append(f"⚠️  Calculated position (${calculated_position:.2f}) > MAX_ALLOCATION (${max_allocation:.2f})")
    
    print("\n🛡️  RISK MANAGEMENT PARAMETERS")
    print("-" * 70)
    print(f"  BOT_RISK_THRESHOLD:         {risk_threshold:.1%}")
    print(f"  BOT_STOP_LOSS_PERCENT:      {stop_loss:.1%}")
    print(f"  BOT_TAKE_PROFIT_PERCENT:    {take_profit:.1%}")
    print(f"  BOT_TRAILING_STOP_PERCENT:  {trailing_stop:.1%}")
    
    # Check 7: Stop loss < Take profit (sensible for risk/reward)
    if stop_loss >= take_profit:
        warnings.append(f"⚠️  STOP_LOSS ({stop_loss:.1%}) >= TAKE_PROFIT ({take_profit:.1%}). Risk/reward ratio may be unfavorable.")
    
    # Check 8: Trailing stop is reasonable
    if trailing_stop > stop_loss:
        warnings.append(f"⚠️  TRAILING_STOP ({trailing_stop:.1%}) > STOP_LOSS ({stop_loss:.1%})")
    
    # Check 9: Risk threshold is reasonable
    if risk_threshold > 0.1:  # 10%
        warnings.append(f"⚠️  RISK_THRESHOLD ({risk_threshold:.1%}) is very high (>10%)")
    
    if risk_threshold < 0.001:  # 0.1%
        warnings.append(f"⚠️  RISK_THRESHOLD ({risk_threshold:.1%}) is very low (<0.1%)")
    
    print("\n📈 POSITION LIMITS")
    print("-" * 70)
    print(f"  BOT_MAX_OPEN_POSITIONS:      {max_positions}")
    print(f"  BOT_MAX_CONSECUTIVE_LOSSES:  {max_consecutive_losses}")
    
    # Check 10: Total capital can support max positions
    min_capital_needed = min_allocation * max_positions
    if min_capital_needed > total_capital:
        warnings.append(f"⚠️  MAX_OPEN_POSITIONS ({max_positions}) × MIN_ALLOCATION (${min_allocation}) = ${min_capital_needed:.2f} > TOTAL_CAPITAL (${total_capital})")
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    if not issues and not warnings:
        print("✅ All parameters are consistent and properly configured!")
    else:
        if issues:
            print("\n🚨 CRITICAL ISSUES FOUND:")
            for issue in issues:
                print(f"  {issue}")
        
        if warnings:
            print("\n⚠️  WARNINGS:")
            for warning in warnings:
                print(f"  {warning}")
    
    print("\n" + "=" * 70)
    
    return len(issues) == 0

if __name__ == '__main__':
    success = check_parameter_consistency()
    exit(0 if success else 1)
