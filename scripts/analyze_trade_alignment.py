#!/usr/bin/env python3
"""
Analyze trade data alignment against bot parameters and surface issues.

Features:
- Reads settings via API (/api/settings) or .env fallback
- Reads trades from SQLite (logs/trading_logs.db) by default; optional API source
- Computes allocation per trade, checks min/max, risk threshold compliance
- Approximates max concurrent open positions from BUY/SELL/COVER sequence
- Fetches self-test summary from /api/system/health (if available)
- Scans trading_bot.log for common warnings (throttling, missing keys)

Usage examples:
  python scripts/analyze_trade_alignment.py --api-url http://127.0.0.1:8000
  python scripts/analyze_trade_alignment.py --target operator
  python scripts/analyze_trade_alignment.py --source api --api-url http://127.0.0.1:8000
"""

import argparse
import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


def load_targets_map() -> Dict[str, str]:
    """Load monitor target aliases from config/monitor_targets.json if present."""
    project_root = Path(__file__).parent.parent
    cfg_path = project_root / "config" / "monitor_targets.json"
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def resolve_api_url(args: argparse.Namespace) -> Optional[str]:
    """Resolve API URL from args or target alias; return None if not set."""
    if args.api_url:
        url = args.api_url.strip().rstrip('/')
        if not url.startswith('http'):
            url = f"http://{url}"
        return url
    if args.target:
        targets = load_targets_map()
        url_obj = targets.get(args.target)
        if url_obj:
            # Support both string and object forms
            if isinstance(url_obj, str):
                url = url_obj
            elif isinstance(url_obj, dict):
                url = url_obj.get('api_url') or url_obj.get('url') or ''
            else:
                url = ''
            if url:
                url = url.strip().rstrip('/')
                if not url.startswith('http'):
                    url = f"http://{url}"
                return url
    # Fallback to env API_URL if present
    env_url = os.getenv("API_URL")
    if env_url:
        env_url = env_url.strip().rstrip('/')
        if not env_url.startswith('http'):
            env_url = f"http://{env_url}"
        return env_url
    return None


def fetch_settings_via_api(api_url: str) -> Optional[Dict[str, Any]]:
    try:
        import requests
    except ImportError:
        return None
    try:
        r = requests.get(f"{api_url}/api/settings", timeout=5)
        if r.status_code == 200:
            return r.json()
        return None
    except requests.RequestException:
        return None


def read_env_settings() -> Dict[str, Any]:
    """Read settings from .env file (similar to api/routes/settings.py)."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'
    env_vars: Dict[str, str] = {}
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        env_vars[key] = value
        except OSError:
            pass

    def get_setting(key: str, default: str, type_func=float):
        value = env_vars.get(key, os.getenv(key, default))
        try:
            return type_func(value)
        except (ValueError, TypeError):
            return type_func(default)

    def get_setting_str(key: str, default: str):
        return env_vars.get(key, os.getenv(key, default))

    return {
        "BOT_TOTAL_CAPITAL": get_setting("BOT_TOTAL_CAPITAL", "10000", float),
        "BOT_MIN_ALLOCATION": get_setting("BOT_MIN_ALLOCATION", "50", float),
        "BOT_MAX_ALLOCATION": get_setting("BOT_MAX_ALLOCATION", "500", float),
        "BOT_RISK_THRESHOLD": get_setting("BOT_RISK_THRESHOLD", "0.02", float),
        "BOT_POSITION_SIZE": get_setting("BOT_POSITION_SIZE", "0.01", float),
        "BOT_MAX_OPEN_POSITIONS": get_setting("BOT_MAX_OPEN_POSITIONS", "5", int),
        "BOT_STOP_LOSS_PERCENT": get_setting("BOT_STOP_LOSS_PERCENT", "0.05", float),
        "BOT_TAKE_PROFIT_PERCENT": get_setting("BOT_TAKE_PROFIT_PERCENT", "0.10", float),
        "ENABLE_ML_SIGNAL_FILTER": get_setting_str("ENABLE_ML_SIGNAL_FILTER", "true"),
        "ML_SIGNAL_FILTER_MIN_CONFIDENCE": get_setting("ML_SIGNAL_FILTER_MIN_CONFIDENCE", "0.6", float),
        "ML_SIGNAL_FILTER_MIN_WIN_PROB": get_setting("ML_SIGNAL_FILTER_MIN_WIN_PROB", "0.55", float),
    }


def load_trades_from_sqlite(db_path: Path) -> List[Dict[str, Any]]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, symbol, action, quantity, price, is_win, pnl, pnl_percent, entry_price, exit_price, exit_reason, strategy, metadata FROM trades ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    conn.close()
    trades: List[Dict[str, Any]] = []
    for row in rows:
        trades.append({
            'timestamp': row[0],
            'symbol': row[1],
            'action': row[2],
            'quantity': float(row[3]) if row[3] is not None else None,
            'price': float(row[4]) if row[4] is not None else None,
            'is_win': bool(row[5]) if row[5] is not None else None,
            'pnl': float(row[6]) if row[6] is not None else None,
            'pnl_percent': float(row[7]) if row[7] is not None else None,
            'entry_price': float(row[8]) if row[8] is not None else None,
            'exit_price': float(row[9]) if row[9] is not None else None,
            'exit_reason': row[10],
            'strategy': row[11],
            'metadata': json.loads(row[12]) if row[12] else {},
        })
    return trades


def load_trades_via_api(api_url: str) -> List[Dict[str, Any]]:
    try:
        import requests
    except ImportError:
        return []
    try:
        r = requests.get(f"{api_url}/api/trades?limit=500", timeout=5)
        if r.status_code != 200:
            return []
        data = r.json() or {}
        trades = data.get('trades', [])
        # Normalize structure closer to record_trade shape
        norm: List[Dict[str, Any]] = []
        for t in trades:
            norm.append({
                'timestamp': t.get('entry_timestamp') or t.get('exit_timestamp'),
                'symbol': t.get('symbol'),
                'action': 'BUY' if t.get('status') == 'open' else 'SELL',
                'quantity': t.get('quantity'),
                'price': t.get('entry_price') or t.get('exit_price'),
                'entry_price': t.get('entry_price'),
                'exit_price': t.get('exit_price'),
                'pnl': t.get('pnl'),
                'pnl_percent': None,
            })
        return norm
    except requests.RequestException:
        return []


def compute_alignment(trades: List[Dict[str, Any]], settings: Dict[str, Any]) -> Dict[str, Any]:
    min_alloc = float(settings.get('BOT_MIN_ALLOCATION', 0))
    max_alloc = float(settings.get('BOT_MAX_ALLOCATION', 0))
    risk_threshold = float(settings.get('BOT_RISK_THRESHOLD', 0))
    stop_loss_pct = float(settings.get('BOT_STOP_LOSS_PERCENT', 0))
    total_capital = float(settings.get('BOT_TOTAL_CAPITAL', 0))
    max_open_positions = int(settings.get('BOT_MAX_OPEN_POSITIONS', 0))

    violations: List[Dict[str, Any]] = []
    alloc_ok = 0
    alloc_total = 0
    risk_ok = 0
    risk_total = 0

    # Track open positions counts by symbol
    open_counts: Dict[str, int] = {}
    max_concurrent_open = 0

    for t in trades:
        symbol = t.get('symbol')
        action = (t.get('action') or '').upper()
        qty = t.get('quantity') or 0
        entry_price = t.get('entry_price') if t.get('entry_price') not in (None, '') else t.get('price')
        if not qty or not entry_price:
            continue

        allocation_used = float(qty) * float(entry_price)
        alloc_total += 1
        if allocation_used < min_alloc or allocation_used > max_alloc:
            violations.append({
                'type': 'allocation_bounds',
                'symbol': symbol,
                'action': action,
                'allocation': round(allocation_used, 2),
                'min_alloc': min_alloc,
                'max_alloc': max_alloc,
                'timestamp': t.get('timestamp'),
            })
        else:
            alloc_ok += 1

        # Risk vs threshold
        risk_total += 1
        potential_loss = allocation_used * stop_loss_pct
        risk_limit = risk_threshold * total_capital
        if potential_loss > risk_limit:
            violations.append({
                'type': 'risk_limit_exceeded',
                'symbol': symbol,
                'action': action,
                'potential_loss': round(potential_loss, 2),
                'risk_limit': round(risk_limit, 2),
                'allocation': round(allocation_used, 2),
                'timestamp': t.get('timestamp'),
            })
        else:
            risk_ok += 1

        # Approximate open position tracking
        if action in ('BUY', 'SHORT'):
            open_counts[symbol] = open_counts.get(symbol, 0) + 1
        elif action in ('SELL', 'COVER') and open_counts.get(symbol, 0) > 0:
            open_counts[symbol] = max(0, open_counts.get(symbol, 0) - 1)
        # Compute current concurrent total
        concurrent = sum(open_counts.values())
        max_concurrent_open = max(max_concurrent_open, concurrent)

    max_pos_violation = max_concurrent_open > max_open_positions if max_open_positions > 0 else False

    return {
        'allocation_compliance': {
            'ok': alloc_ok,
            'total': alloc_total,
            'rate': round((alloc_ok / alloc_total * 100), 1) if alloc_total else 0.0,
        },
        'risk_compliance': {
            'ok': risk_ok,
            'total': risk_total,
            'rate': round((risk_ok / risk_total * 100), 1) if risk_total else 0.0,
        },
        'max_concurrent_open_positions': max_concurrent_open,
        'max_open_positions_limit': max_open_positions,
        'max_positions_violation': max_pos_violation,
        'violations': violations,
    }


def fetch_selftest_summary(api_url: Optional[str]) -> Optional[Dict[str, Any]]:
    if not api_url:
        return None
    try:
        import requests
    except ImportError:
        return None
    try:
        r = requests.get(f"{api_url}/api/system/health", timeout=8)
        if r.status_code != 200:
            return None
        data = r.json()
        st = data.get('self_test', {})
        return {
            'status': data.get('status'),
            'passed': st.get('passed'),
            'total': st.get('total'),
            'passed_count': st.get('passed_count'),
            'failed_count': st.get('failed_count'),
            'success_rate': st.get('success_rate'),
            'failed_tests': [r['name'] for r in st.get('results', []) if not r.get('passed')],
        }
    except requests.RequestException:
        return None


def scan_log_warnings(log_path: Path) -> Dict[str, Any]:
    stats = {
        'missing_keys': 0,
        'throttling_events': 0,
        'sandbox_fallbacks': 0,
        'ml_filter_rejections': 0,
    }
    if not log_path.exists():
        return stats
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                ls = line.lower()
                if 'missing api key' in ls or 'api key missing' in ls:
                    stats['missing_keys'] += 1
                if 'throttl' in ls and ('delay' in ls or 'wait' in ls):
                    stats['throttling_events'] += 1
                if 'sandbox mode' in ls and 'yfinance fallback' in ls:
                    stats['sandbox_fallbacks'] += 1
                if 'ml signal filter' in ls and ('reject' in ls or 'skipping' in ls):
                    stats['ml_filter_rejections'] += 1
    except OSError:
        pass
    return stats


def main():
    parser = argparse.ArgumentParser(description="Analyze trade alignment vs settings")
    parser.add_argument('--api-url', help='API base URL (e.g., http://127.0.0.1:8000)')
    parser.add_argument('--target', help='Target alias from config/monitor_targets.json (e.g., operator)')
    parser.add_argument('--source', choices=['sqlite', 'api'], default='sqlite', help='Trade data source')
    parser.add_argument('--output-json', action='store_true', help='Write JSON report under logs/')
    args = parser.parse_args()

    api_url = resolve_api_url(args)
    settings = fetch_settings_via_api(api_url) if api_url else None
    if not settings:
        settings = read_env_settings()

    project_root = Path(__file__).parent.parent
    db_path = project_root / 'logs' / 'trading_logs.db'
    trades: List[Dict[str, Any]] = []
    if args.source == 'sqlite':
        trades = load_trades_from_sqlite(db_path)
    elif api_url:
        trades = load_trades_via_api(api_url)

    if not trades:
        print("No trades found. Ensure trading is running or trade logging is enabled (logs/trading_logs.db).")
        # Still print self-test summary and exit
        st = fetch_selftest_summary(api_url)
        if st:
            print(f"Self-test: status={st['status']}, passed={st['passed']} ({st['passed_count']}/{st['total']}, fail={st['failed_count']})")
            if st.get('failed_tests'):
                print("Failed tests:", ", ".join(st['failed_tests'][:5]))
        return

    report = compute_alignment(trades, settings)
    st = fetch_selftest_summary(api_url)
    log_stats = scan_log_warnings(project_root / 'trading_bot.log')

    # Print concise summary
    print("Alignment Summary:")
    print(f"- Allocation compliance: {report['allocation_compliance']['ok']}/{report['allocation_compliance']['total']} ({report['allocation_compliance']['rate']}%)")
    print(f"- Risk compliance: {report['risk_compliance']['ok']}/{report['risk_compliance']['total']} ({report['risk_compliance']['rate']}%)")
    print(f"- Max concurrent open positions: {report['max_concurrent_open_positions']} (limit {report['max_open_positions_limit']})")
    if report['max_positions_violation']:
        print("- Violation: concurrent open positions exceeded configured limit")

    # Show top 5 violations
    if report['violations']:
        print("Top Violations:")
        for v in report['violations'][:5]:
            if v['type'] == 'allocation_bounds':
                print(f"  • {v['symbol']} {v['action']} allocation ${v['allocation']} out of bounds [{v['min_alloc']}, {v['max_alloc']}] @ {v.get('timestamp')}")
            elif v['type'] == 'risk_limit_exceeded':
                print(f"  • {v['symbol']} {v['action']} potential loss ${v['potential_loss']} > risk limit ${v['risk_limit']} (alloc ${v['allocation']}) @ {v.get('timestamp')}")

    # Self-test summary
    if st:
        print(f"Self-test: status={st['status']}, passed={st['passed']} ({st['passed_count']}/{st['total']}, fail={st['failed_count']})")
        if st.get('failed_tests'):
            print("Failed tests:", ", ".join(st['failed_tests'][:5]))

    # Log warnings summary
    print("Log Warnings:")
    print(f"- Missing API keys: {log_stats['missing_keys']}")
    print(f"- Throttling events: {log_stats['throttling_events']}")
    print(f"- Sandbox→yfinance fallbacks: {log_stats['sandbox_fallbacks']}")
    print(f"- ML filter rejections: {log_stats['ml_filter_rejections']}")

    if args.output_json:
        out_dir = project_root / 'logs'
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / f"trade_alignment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        payload = {
            'settings': settings,
            'alignment': report,
            'selftest': st,
            'log_warnings': log_stats,
        }
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2)
            print(f"Saved JSON report to {out_path}")
        except OSError as e:
            print(f"Failed to write JSON report: {e}")


if __name__ == '__main__':
    main()
