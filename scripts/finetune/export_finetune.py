#!/usr/bin/env python3
"""
Export captured fine-tune samples to OpenAI-style JSONL and enforce retention.

Samples are captured opt-in (FINETUNE_CAPTURE_ENABLED) and already redacted at
write time. This tool also purges anything past its retention window.

Usage (from ):
    python3 scripts/finetune/export_finetune.py --out finetune.jsonl
    python3 scripts/finetune/export_finetune.py --purge-only
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Export/purge fine-tune samples")
    parser.add_argument("--out", default="finetune.jsonl", help="Output JSONL path")
    parser.add_argument("--limit", type=int, default=None, help="Max samples to export")
    parser.add_argument("--purge-only", action="store_true", help="Only purge expired; no export")
    args = parser.parse_args()

    from database import engine
    from api.services.ai_tables import ensure_ai_tables
    from api.services.finetune_capture import export_samples, purge_expired

    ensure_ai_tables(engine)

    purged = purge_expired()
    print(f"Purged {purged} expired sample(s).")
    if args.purge_only:
        return 0

    records = export_samples(limit=args.limit)
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    print(f"Wrote {len(records)} sample(s) to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
