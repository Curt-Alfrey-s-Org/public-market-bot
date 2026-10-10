"""
Poll the Market Bot API and print status, trades, decisions and messages.

Authentication (required): every /api/* call needs a JWT, and starting the bot
(POST /api/bot/start) needs an ADMIN JWT. Provide one of:
  MARKET_BOT_ADMIN_TOKEN=<admin JWT>                         (preferred), or
  MARKET_BOT_ADMIN_USERNAME / MARKET_BOT_ADMIN_PASSWORD      (logs in once at startup).
The token is only sent as an Authorization header and is never printed
(see scripts/market_bot_auth.py).
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from market_bot_auth import MISSING_TOKEN_HELP, auth_headers, resolve_admin_token  # noqa: E402

API_URL = os.getenv("API_URL", "http://localhost:8000")
INTERVAL_SEC = int(os.getenv("MONITOR_INTERVAL", "15"))
DURATION_SEC = int(os.getenv("MONITOR_DURATION", "0"))  # 0 = run indefinitely
MAX_ITEMS = int(os.getenv("MONITOR_MAX_ITEMS", "5"))
TARGET_NAME = os.getenv("TARGET_NAME")
TARGETS_CONFIG = os.getenv(
    "TARGETS_CONFIG",
    os.path.join(os.getcwd(), "config", "monitor_targets.json")
)


def _resolve_api_url(api_url: str) -> str:
    """Resolve API URL from TARGET_NAME using config if provided."""
    if TARGET_NAME:
        try:
            if os.path.exists(TARGETS_CONFIG):
                with open(TARGETS_CONFIG, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                target = cfg.get(TARGET_NAME) or {}
                mapped = target.get("api_url")
                if isinstance(mapped, str) and mapped:
                    return mapped
        except Exception:
            # Fallback silently to provided api_url
            pass
    return api_url

API_URL = _resolve_api_url(API_URL)

_AUTH_TOKEN: Optional[str] = None


def _auth_headers() -> Dict[str, str]:
    return auth_headers(_AUTH_TOKEN)


def _fetch(url: str) -> Optional[Dict[str, Any]]:
    """HTTP GET with requests if available, else urllib.
    Returns parsed JSON dict or None on error.
    """
    try:
        import requests  # type: ignore

        resp = requests.get(url, headers=_auth_headers(), timeout=5)
        if resp.status_code != 200:
            print(f"! GET {url} -> {resp.status_code}")
            return None
        return resp.json()
    except ImportError:
        # Fallback to urllib
        try:
            from urllib.request import Request, urlopen
            from urllib.error import URLError, HTTPError

            with urlopen(Request(url, headers=_auth_headers()), timeout=5) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data)
        except (URLError, HTTPError) as e:
            print(f"! GET {url} failed: {e}")
            return None
        except Exception as e:
            print(f"! GET {url} unexpected error: {e}")
            return None


def _post(url: str, body: Optional[Dict[str, Any]] = None) -> bool:
    try:
        import requests  # type: ignore

        resp = requests.post(url, json=body or {}, headers=_auth_headers(), timeout=5)
        if resp.status_code >= 200 and resp.status_code < 300:
            return True
        print(f"! POST {url} -> {resp.status_code} {resp.text}")
        return False
    except ImportError:
        print("! requests not available; POST skipped")
        return False


def _fmt_ts(ts: Optional[str]) -> str:
    if not ts:
        return "-"
    try:
        # try ISO parse
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except Exception:
        return ts


def print_status(status: Dict[str, Any]) -> None:
    mode = status.get("mode", "unknown")
    running = status.get("running", False)
    continuous = status.get("continuous", False)
    open_positions = status.get("open_positions", 0)
    total_trades = status.get("total_trades", 0)
    print(f"[STATUS] mode={mode} running={running} continuous={continuous} open_positions={open_positions} total_trades={total_trades}")


def print_trades(trades: List[Dict[str, Any]]) -> None:
    if not trades:
        print("[TRADES] none")
        return
    print("[TRADES]")
    for t in trades[:MAX_ITEMS]:
        symbol = t.get("symbol")
        side = t.get("side") or t.get("type")
        qty = t.get("quantity") or t.get("qty")
        price = t.get("price") or t.get("entry_price")
        pnl = t.get("pnl") or t.get("pnl_amount")
        reason = t.get("reason") or t.get("entry_reason") or t.get("exit_reason")
        ts = _fmt_ts(t.get("timestamp") or t.get("time"))
        print(f"  {ts} {symbol} {side} {qty}@{price} pnl={pnl} reason={reason}")


def print_decisions(decisions: Dict[str, Any]) -> None:
    ev = decisions.get("evaluated_count")
    items = decisions.get("decisions") or decisions.get("items") or []
    print(f"[DECISIONS] evaluated={ev} showing up to {MAX_ITEMS}")
    for d in items[:MAX_ITEMS]:
        symbol = d.get("symbol")
        strategy = d.get("strategy") or d.get("source")
        signal = d.get("signal")
        conf = d.get("confidence") or d.get("score")
        reason = d.get("reason") or d.get("explanation")
        print(f"  {symbol} {strategy} -> {signal} conf={conf} reason={reason}")


def main() -> None:
    global _AUTH_TOKEN
    _AUTH_TOKEN = resolve_admin_token(API_URL)
    if not _AUTH_TOKEN:
        print(f"! {MISSING_TOKEN_HELP}", file=sys.stderr)
        sys.exit(2)
    target_info = f" (target={TARGET_NAME})" if TARGET_NAME else ""
    print(f"Monitoring {API_URL}{target_info} every {INTERVAL_SEC}s (Ctrl+C to stop)")
    # Ensure bot is running
    status = _fetch(f"{API_URL}/api/bot/status") or {}
    if not status.get("running"):
        started = _post(f"{API_URL}/api/bot/start", {"mode": "yfinance"})
        print(f"[INIT] bot start requested -> {'OK' if started else 'FAIL'}")
        time.sleep(2)

    start_ts = time.time()
    try:
        while True:
            status = _fetch(f"{API_URL}/api/bot/status") or {}
            print_status(status)

            trades_resp = _fetch(f"{API_URL}/api/trades?limit={MAX_ITEMS}") or {}
            trades = trades_resp if isinstance(trades_resp, list) else trades_resp.get("items") or []
            print_trades(trades)

            decisions = _fetch(f"{API_URL}/api/reports/decisions") or {}
            print_decisions(decisions)

            msgs = _fetch(f"{API_URL}/api/messages?limit={MAX_ITEMS}&level=INFO") or {}
            msg_items = msgs if isinstance(msgs, list) else msgs.get("items") or []
            if msg_items:
                print("[MESSAGES]")
                for m in msg_items[:MAX_ITEMS]:
                    print(f"  {_fmt_ts(m.get('timestamp'))} {m.get('level')} {m.get('message')}")

            print("-")
            time.sleep(INTERVAL_SEC)
            if DURATION_SEC > 0 and (time.time() - start_ts) >= DURATION_SEC:
                print("\nMonitor duration reached; exiting.")
                break
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        # Keep bot running; to stop: POST /api/bot/stop


if __name__ == "__main__":
    main()
