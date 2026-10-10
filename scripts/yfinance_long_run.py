import os
import sys
import time
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

# Auth: /api/* needs a JWT and POST /api/bot/start needs an ADMIN JWT. Set
# MARKET_BOT_ADMIN_TOKEN, or MARKET_BOT_ADMIN_USERNAME/MARKET_BOT_ADMIN_PASSWORD
# (see scripts/market_bot_auth.py).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from market_bot_auth import MISSING_TOKEN_HELP, auth_headers, resolve_admin_token  # noqa: E402

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
DURATION_SEC = int(os.getenv("DURATION_SEC", "600"))  # default 10 minutes
INTERVAL_SEC = int(os.getenv("INTERVAL_SEC", "10"))
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "50"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(os.getcwd(), "runs"))
TARGET_NAME = os.getenv("TARGET_NAME")
TARGETS_CONFIG = os.getenv(
    "TARGETS_CONFIG",
    os.path.join(os.getcwd(), "config", "monitor_targets.json")
)


def _resolve_api_url(api_url: str) -> str:
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
            pass
    return api_url

API_URL = _resolve_api_url(API_URL)
_AUTH_TOKEN: Optional[str] = None


def _fetch(url: str) -> Optional[Dict[str, Any]]:
    try:
        import requests  # type: ignore
        resp = requests.get(url, headers=auth_headers(_AUTH_TOKEN), timeout=5)
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def _post(url: str, body: Optional[Dict[str, Any]] = None) -> bool:
    try:
        import requests  # type: ignore
        resp = requests.post(url, json=body or {}, headers=auth_headers(_AUTH_TOKEN), timeout=5)
        return 200 <= resp.status_code < 300
    except Exception:
        return False


def ensure_bot_running() -> None:
    status = _fetch(f"{API_URL}/api/bot/status") or {}
    if not status.get("running"):
        _post(f"{API_URL}/api/bot/start", {"mode": "yfinance"})
        time.sleep(2)


def safe_list(resp: Any) -> List[Dict[str, Any]]:
    if isinstance(resp, list):
        return resp
    if isinstance(resp, dict):
        return resp.get("items") or resp.get("decisions") or []
    return []


def main() -> None:
    global _AUTH_TOKEN
    _AUTH_TOKEN = resolve_admin_token(API_URL)
    if not _AUTH_TOKEN:
        print(f"! {MISSING_TOKEN_HELP}", file=sys.stderr)
        sys.exit(2)
    ensure_bot_running()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    start = time.time()
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"yfinance_run_{run_id}.json")

    snapshot: Dict[str, Any] = {
        "api_url": API_URL,
        "target_name": TARGET_NAME,
        "started_at": run_id,
        "duration_sec": DURATION_SEC,
        "interval_sec": INTERVAL_SEC,
        "samples": [],
    }

    seen_trade_ids: set = set()
    try:
        while time.time() - start < DURATION_SEC:
            status = _fetch(f"{API_URL}/api/bot/status") or {}
            trades_resp = _fetch(f"{API_URL}/api/trades?limit={MAX_ITEMS}") or {}
            trades = safe_list(trades_resp)
            decisions = _fetch(f"{API_URL}/api/reports/decisions") or {}
            messages_resp = _fetch(f"{API_URL}/api/messages?limit={MAX_ITEMS}&level=INFO") or {}
            messages = safe_list(messages_resp)

            # track new trades only
            new_trades: List[Dict[str, Any]] = []
            for t in trades:
                tid = t.get("id") or f"{t.get('symbol')}-{t.get('timestamp')}-{t.get('side') or t.get('type')}"
                if tid not in seen_trade_ids:
                    seen_trade_ids.add(tid)
                    new_trades.append(t)

            snapshot["samples"].append({
                "ts": datetime.utcnow().isoformat() + "Z",
                "status": status,
                "new_trades": new_trades,
                "decisions": decisions,
                "messages": messages,
            })

            time.sleep(INTERVAL_SEC)
    finally:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2)
        print(f"Saved long-run sample to {out_path}")


if __name__ == "__main__":
    main()
