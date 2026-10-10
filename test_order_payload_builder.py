#!/usr/bin/env python3
"""Tests for order_payload_builder (Schwab payloads for MARKET, LIMIT, STOP, STOP_LIMIT, TRAILING_STOP)."""

import unittest

from order_payload_builder import (
    SUPPORTED_ORDER_TYPES,
    build_schwab_order_payload,
)


class TestBuildSchwabOrderPayload(unittest.TestCase):
    """Test build_schwab_order_payload for all supported order types and actions."""

    def _base(self, payload):
        self.assertIn('orderType', payload)
        self.assertIn('orderStrategyType', payload)
        self.assertEqual(payload['orderStrategyType'], 'SINGLE')
        self.assertIn('orderLegCollection', payload)
        self.assertEqual(len(payload['orderLegCollection']), 1)
        leg = payload['orderLegCollection'][0]
        self.assertIn('instruction', leg)
        self.assertIn('quantity', leg)
        self.assertIn('instrument', leg)
        self.assertEqual(leg['instrument'], {'symbol': 'AAPL', 'assetType': 'EQUITY'})

    def test_market_buy(self):
        p = build_schwab_order_payload(
            'BUY', 'MARKET', 150.0, 10.0, 'AAPL', 'BUY',
        )
        self._base(p)
        self.assertEqual(p['orderType'], 'MARKET')
        self.assertEqual(p['orderLegCollection'][0]['instruction'], 'BUY')
        self.assertEqual(p['orderLegCollection'][0]['quantity'], 10.0)
        self.assertNotIn('price', p)
        self.assertNotIn('stopPrice', p)

    def test_market_sell(self):
        p = build_schwab_order_payload(
            'SELL', 'MARKET', 150.0, 10.0, 'AAPL', 'SELL',
        )
        self._base(p)
        self.assertEqual(p['orderType'], 'MARKET')
        self.assertEqual(p['orderLegCollection'][0]['instruction'], 'SELL')

    def test_limit_buy_no_offset(self):
        p = build_schwab_order_payload(
            'BUY', 'LIMIT', 150.0, 10.0, 'AAPL', 'BUY',
            limit_offset_pct=0.0,
        )
        self.assertEqual(p['orderType'], 'LIMIT')
        self.assertIn('price', p)
        self.assertEqual(p['price'], 150.0)

    def test_limit_buy_with_offset(self):
        p = build_schwab_order_payload(
            'BUY', 'LIMIT', 100.0, 5.0, 'AAPL', 'BUY',
            limit_offset_pct=0.01,
        )
        self.assertEqual(p['orderType'], 'LIMIT')
        self.assertEqual(p['price'], 99.0)  # 100 * (1 - 0.01)

    def test_limit_sell_with_offset(self):
        p = build_schwab_order_payload(
            'SELL', 'LIMIT', 100.0, 5.0, 'AAPL', 'SELL',
            limit_offset_pct=0.01,
        )
        self.assertEqual(p['orderType'], 'LIMIT')
        self.assertEqual(p['price'], 101.0)  # 100 * (1 + 0.01)

    def test_stop_sell(self):
        p = build_schwab_order_payload(
            'SELL', 'STOP', 100.0, 5.0, 'AAPL', 'SELL',
            stop_offset_pct=0.02,
        )
        self.assertEqual(p['orderType'], 'STOP')
        self.assertIn('stopPrice', p)
        self.assertEqual(p['stopPrice'], 98.0)  # 100 * (1 - 0.02)
        self.assertNotIn('price', p)

    def test_stop_cover(self):
        p = build_schwab_order_payload(
            'COVER', 'STOP', 50.0, 10.0, 'AAPL', 'BUY_TO_COVER',
            stop_offset_pct=0.01,
        )
        self.assertEqual(p['orderType'], 'STOP')
        self.assertIn('stopPrice', p)
        self.assertEqual(p['stopPrice'], 50.5)  # 50 * (1 + 0.01)

    def test_stop_limit_sell(self):
        p = build_schwab_order_payload(
            'SELL', 'STOP_LIMIT', 100.0, 5.0, 'AAPL', 'SELL',
            stop_offset_pct=0.02,
            stop_limit_offset_pct=0.01,
        )
        self.assertEqual(p['orderType'], 'STOP_LIMIT')
        self.assertEqual(p['stopPrice'], 98.0)
        self.assertEqual(p['price'], round(98.0 * 0.99, 2))  # stop * (1 - 0.01)

    def test_trailing_stop_sell(self):
        p = build_schwab_order_payload(
            'SELL', 'TRAILING_STOP', 100.0, 5.0, 'AAPL', 'SELL',
            trailing_stop_pct=0.03,
        )
        self.assertEqual(p['orderType'], 'TRAILING_STOP')
        self.assertEqual(p['stopPriceLinkBasis'], 'LAST')
        self.assertEqual(p['stopPriceLinkType'], 'PERCENT')
        self.assertEqual(p['stopPriceOffset'], 3)
        self.assertNotIn('price', p)
        self.assertNotIn('stopPrice', p)

    def test_unsupported_order_type(self):
        with self.assertRaises(ValueError) as ctx:
            build_schwab_order_payload(
                'BUY', 'FILL_OR_KILL', 100.0, 5.0, 'AAPL', 'BUY',
            )
        self.assertIn('FILL_OR_KILL', str(ctx.exception))
        self.assertIn('Unsupported', str(ctx.exception))

    def test_supported_order_types(self):
        self.assertIn('MARKET', SUPPORTED_ORDER_TYPES)
        self.assertIn('LIMIT', SUPPORTED_ORDER_TYPES)
        self.assertIn('STOP', SUPPORTED_ORDER_TYPES)
        self.assertIn('STOP_LIMIT', SUPPORTED_ORDER_TYPES)
        self.assertIn('TRAILING_STOP', SUPPORTED_ORDER_TYPES)


if __name__ == '__main__':
    unittest.main()
