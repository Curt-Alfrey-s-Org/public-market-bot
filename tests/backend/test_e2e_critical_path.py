"""
E2E Critical Path Tests (Phase 8.2)
Runs the API-side critical path in sequence: health → stats → reports/decisions → logs → messages → bot status.
Use with runner.py when API is up; frontend E2E (open 5173, click through) remains manual per PHASE8_TEST_PLAN.md.
"""

from tests.framework.base_test import BaseTestModule, TestResult, TestStatus


class E2ECriticalPathTest(BaseTestModule):
    """E2E critical path: core API flow in one sequence."""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        super().__init__("E2E Critical Path", api_base_url, timeout=15)

    def test_e2e_critical_path_api(self) -> TestResult:
        """Run critical path: health → stats → reports/decisions → logs → messages → bot status."""
        def _test():
            # 1. Health
            r = self.api_request("GET", "/api/health")
            self.assert_status(r, 200)
            d = self.assert_json(r)
            self.assert_field_exists(d, "status")
            assert d.get("status") == "healthy", "Health should be healthy"

            # 2. Stats
            r = self.api_request("GET", "/api/stats")
            self.assert_status(r, 200)
            d = self.assert_json(r)
            for f in ("capital", "total_trades", "win_rate", "total_pnl"):
                self.assert_field_exists(d, f)

            # 3. Reports/decisions (Decision Report)
            r = self.api_request("GET", "/api/reports/decisions")
            self.assert_status(r, 200)
            d = self.assert_json(r)
            for f in ("candidates", "decisions", "cycle_number", "total_candidates", "evaluated_count"):
                self.assert_field_exists(d, f)

            # 4. Logs
            r = self.api_request("GET", "/api/logs", params={"limit": 5})
            self.assert_status(r, 200)
            d = self.assert_json(r)
            self.assert_field_exists(d, "logs")
            self.assert_field_exists(d, "total")
            self.assert_field_exists(d, "exists")

            # 5. Messages
            r = self.api_request("GET", "/api/messages", params={"limit": 5})
            self.assert_status(r, 200)
            d = self.assert_json(r)
            self.assert_field_exists(d, "messages")
            self.assert_field_exists(d, "total")

            # 6. Bot status
            r = self.api_request("GET", "/api/bot/status")
            self.assert_status(r, 200)
            d = self.assert_json(r)
            self.assert_field_exists(d, "running")
            self.assert_field_exists(d, "mode")

            return True

        return self.run_test("E2E Critical Path (API)", _test)

    def run(self):
        """Run E2E critical path tests."""
        self.start_time = self.end_time = None
        self.log("Starting E2E critical path tests...")

        if not self.api_available():
            self.results.append(
                TestResult(
                    "E2E Critical Path (API)",
                    TestStatus.SKIP,
                    "API not running. Start with: ./start_api.sh",
                )
            )
            self.log("Completed 1 test (skipped - API not available)")
            return self.results

        try:
            result = self.test_e2e_critical_path_api()
            if result:
                status = "✓" if result.status == TestStatus.PASS else "✗"
                self.log(f"{status} {result.name}: {result.message or result.status.value}")
        except Exception as e:
            self.log(f"E2E Critical Path failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()

        self.log(f"Completed {len(self.results)} test(s)")
        return self.results
