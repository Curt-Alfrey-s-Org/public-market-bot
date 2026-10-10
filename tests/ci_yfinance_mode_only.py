#!/usr/bin/env python3
"""
CI helper: run only backend yfinance-mode unit tests (no API required).
Writes a JSON report and exits non-zero if any test fails.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tests.framework.base_test import TestStatus
from tests.backend.test_yfinance_mode import YfinanceModeTest


def main():
    api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    output = os.getenv("OUTPUT", str(PROJECT_ROOT / "reports" / "selftest_yfinance_mode.json"))

    # Ensure reports directory exists
    Path(output).parent.mkdir(parents=True, exist_ok=True)

    module = YfinanceModeTest(api_base_url=api_url)
    start = datetime.now()
    results = module.run()
    end = datetime.now()

    summary = module.get_summary()
    report = {
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r.status == TestStatus.PASS),
            "failed": sum(1 for r in results if r.status == TestStatus.FAIL),
            "warnings": sum(1 for r in results if r.status == TestStatus.WARN),
            "skipped": sum(1 for r in results if r.status == TestStatus.SKIP),
            "success_rate": summary["success_rate"],
            "duration": (end - start).total_seconds(),
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
        "modules": [{"name": module.name, "summary": summary}],
        "results": [r.to_dict() for r in results],
    }

    with open(output, "w") as f:
        json.dump(report, f, indent=2)

    failed = report["summary"]["failed"]
    if failed > 0:
        print(f"\n✗ {failed} yfinance-mode backend test(s) failed")
        sys.exit(1)
    else:
        print("\n✓ All yfinance-mode backend tests passed")
        print(f"Report: {output}")
        sys.exit(0)


if __name__ == "__main__":
    main()
