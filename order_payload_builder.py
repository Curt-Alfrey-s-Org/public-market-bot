#!/usr/bin/env python3
"""
Build Schwab API order payloads from action, order type, and price.

Wires order_types.py concepts (limit, stop, stop-limit, trailing stop) into
Schwab-equity payloads. Used by execute_trade_live_mode (main.py).

Supports: MARKET, LIMIT, STOP, STOP_LIMIT, TRAILING_STOP.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Order types we can build payloads for
SUPPORTED_ORDER_TYPES = frozenset({'MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT', 'TRAILING_STOP'})


def _round2(x: float) -> float:
    return round(float(x), 2)


def build_schwab_order_payload(
    action: str,
    order_type: str,
    price: float,
    quantity: float,
    symbol: str,
    instruction: str,
    *,
    limit_offset_pct: float = 0.0,
    stop_offset_pct: float = 0.01,
    stop_limit_offset_pct: float = 0.01,
    trailing_stop_pct: float = 0.03,
) -> Dict[str, Any]:
    """
    Build a Schwab API order payload (SINGLE equity order).

    Args:
        action: BUY | SELL | SHORT | COVER
        order_type: MARKET | LIMIT | STOP | STOP_LIMIT | TRAILING_STOP
        price: Reference price (e.g. last or current)
        quantity: Share quantity
        symbol: Equity symbol
        instruction: Schwab instruction (BUY, SELL, SELL_SHORT, BUY_TO_COVER)
        limit_offset_pct: For LIMIT: buy below / sell above (0 = none)
        stop_offset_pct: For STOP/STOP_LIMIT: stop distance from price
        stop_limit_offset_pct: For STOP_LIMIT: limit distance from stop
        trailing_stop_pct: For TRAILING_STOP: trail % (e.g. 0.03 = 3%)

    Returns:
        Dict suitable for schwab client place_order(account_id, payload).
    """
    order_type = order_type.upper()
    if order_type not in SUPPORTED_ORDER_TYPES:
        raise ValueError(f"Unsupported order_type '{order_type}'. Use {SUPPORTED_ORDER_TYPES}")

    opens = action.upper() in ('BUY', 'SHORT')
    is_sell_side = action.upper() in ('SELL', 'SHORT')

    base: Dict[str, Any] = {
        'orderType': order_type,
        'session': 'NORMAL',
        'duration': 'DAY',
        'orderStrategyType': 'SINGLE',
        'orderLegCollection': [{
            'instruction': instruction,
            'quantity': quantity,
            'instrument': {'symbol': symbol, 'assetType': 'EQUITY'},
        }],
    }

    if order_type == 'MARKET':
        return base

    if order_type == 'LIMIT':
        if opens:
            limit_price = price * (1.0 - limit_offset_pct)
        else:
            limit_price = price * (1.0 + limit_offset_pct)
        base['price'] = _round2(limit_price)
        return base

    if order_type == 'STOP':
        if is_sell_side:
            stop_price = price * (1.0 - stop_offset_pct)
        else:
            stop_price = price * (1.0 + stop_offset_pct)
        base['stopPrice'] = _round2(stop_price)
        return base

    if order_type == 'STOP_LIMIT':
        if is_sell_side:
            stop_price = price * (1.0 - stop_offset_pct)
            limit_price = stop_price * (1.0 - stop_limit_offset_pct)
        else:
            stop_price = price * (1.0 + stop_offset_pct)
            limit_price = stop_price * (1.0 + stop_limit_offset_pct)
        base['stopPrice'] = _round2(stop_price)
        base['price'] = _round2(limit_price)
        return base

    if order_type == 'TRAILING_STOP':
        base['stopPriceLinkBasis'] = 'LAST'
        base['stopPriceLinkType'] = 'PERCENT'
        base['stopPriceOffset'] = int(round(trailing_stop_pct * 100.0))
        return base

    return base
