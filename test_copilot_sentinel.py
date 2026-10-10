#!/usr/bin/env python3
"""
Test suite for Copilot Sentinel workflow detection logic.

This test validates the logic used in the Copilot Sentinel GitHub Actions workflow
to determine when GitHub Copilot is still working on a PR vs. when work is complete.
"""

import unittest
from datetime import datetime, timedelta


class TestCopilotSentinelLogic(unittest.TestCase):
    """Test cases for Copilot Sentinel workflow detection logic."""
    
    def test_copilot_pr_detection_by_author(self):
        """Test detection of Copilot PRs by author name."""
        test_cases = [
            ("copilot[bot]", True),
            ("github-copilot", True),
            ("copilot-user", True),
            ("user123", False),
            ("john-doe", False),
        ]
        
        for author, expected in test_cases:
            with self.subTest(author=author):
                is_copilot = "copilot" in author.lower()
                self.assertEqual(is_copilot, expected,
                               f"Author '{author}' detection failed")
    
    def test_copilot_pr_detection_by_branch(self):
        """Test detection of Copilot PRs by branch name."""
        test_cases = [
            ("copilot/fix-bug", True),
            ("copilot/add-feature", True),
            ("feature/copilot-integration", False),  # Only "copilot/" prefix counts
            ("feature/add-tests", False),
            ("main", False),
            ("develop", False),
        ]
        
        for branch, expected in test_cases:
            with self.subTest(branch=branch):
                # Match the actual workflow logic: checks for "copilot/" prefix
                is_copilot = "copilot/" in branch.lower()
                self.assertEqual(is_copilot, expected,
                               f"Branch '{branch}' detection failed")
    
    def test_copilot_pr_detection_by_title(self):
        """Test detection of Copilot PRs by PR title."""
        test_cases = [
            ("Copilot: Add new feature", True),
            ("[Copilot] Fix bug in module", True),
            ("Feature by copilot", True),
            ("Add new feature", False),
            ("Fix bug in module", False),
        ]
        
        for title, expected in test_cases:
            with self.subTest(title=title):
                is_copilot = "copilot" in title.lower()
                self.assertEqual(is_copilot, expected,
                               f"Title '{title}' detection failed")
    
    def test_completion_markers_positive(self):
        """Test detection of completion markers in commit messages."""
        completion_markers = [
            "final",
            "complete",
            "finished",
            "done",
            "ready for review",
            "ready to merge"
        ]
        
        commit_messages = [
            "Final implementation of feature",
            "Feature complete and tested",
            "Implementation finished",
            "Work done on module",
            "Ready for review",
            "Code ready to merge",
        ]
        
        for msg in commit_messages:
            with self.subTest(commit_msg=msg):
                has_completion = any(
                    marker in msg.lower()
                    for marker in completion_markers
                )
                self.assertTrue(has_completion,
                              f"Should detect completion in '{msg}'")
    
    def test_completion_markers_negative(self):
        """Test that completion markers are not falsely detected."""
        completion_markers = [
            "final",
            "complete",
            "finished",
            "done",
            "ready for review",
            "ready to merge"
        ]
        
        commit_messages = [
            "Initial plan",
            "Add feature implementation",
            "Work in progress",
            "Implementing module",
            "Update documentation",
        ]
        
        for msg in commit_messages:
            with self.subTest(commit_msg=msg):
                has_completion = any(
                    marker in msg.lower()
                    for marker in completion_markers
                )
                self.assertFalse(has_completion,
                               f"Should not detect completion in '{msg}'")
    
    def test_wip_markers_positive(self):
        """Test detection of work-in-progress markers."""
        wip_markers = [
            "wip",
            "work in progress",
            "initial plan",
            "progress:",
            "todo",
            "implementing"
        ]
        
        commit_messages = [
            "WIP: Add feature",
            "Work in progress on module",
            "Initial plan for feature",
            "Progress: 50% complete",
            "TODO: Add tests",
            "Implementing new strategy",
        ]
        
        for msg in commit_messages:
            with self.subTest(commit_msg=msg):
                has_wip = any(
                    marker in msg.lower()
                    for marker in wip_markers
                )
                self.assertTrue(has_wip,
                              f"Should detect WIP in '{msg}'")
    
    def test_wip_markers_negative(self):
        """Test that WIP markers are not falsely detected."""
        wip_markers = [
            "wip",
            "work in progress",
            "initial plan",
            "progress:",
            "todo",
            "implementing"
        ]
        
        commit_messages = [
            "Feature complete",
            "Fix bug in module",
            "Add documentation",
            "Update tests",
            "Refactor code",
        ]
        
        for msg in commit_messages:
            with self.subTest(commit_msg=msg):
                has_wip = any(
                    marker in msg.lower()
                    for marker in wip_markers
                )
                self.assertFalse(has_wip,
                               f"Should not detect WIP in '{msg}'")
    
    def test_commit_timing_logic(self):
        """Test that commit timing is calculated correctly."""
        now = datetime.now()
        threshold_minutes = 5
        
        test_cases = [
            (now - timedelta(minutes=1), False, "Recent commit should indicate work in progress"),
            (now - timedelta(minutes=3), False, "3 minutes ago should still be working"),
            (now - timedelta(minutes=5), False, "Exactly 5 minutes is at threshold"),
            (now - timedelta(minutes=6), True, "6 minutes ago should be considered done"),
            (now - timedelta(minutes=10), True, "10 minutes ago should be considered done"),
        ]
        
        for commit_time, expected_done, description in test_cases:
            with self.subTest(description=description):
                minutes_since = (now - commit_time).total_seconds() / 60
                is_done = minutes_since > threshold_minutes
                self.assertEqual(is_done, expected_done, description)
    
    def test_label_detection_positive(self):
        """Test detection of completion labels."""
        completion_labels = ["copilot-completed", "ready-to-merge"]
        
        test_cases = [
            (["copilot-completed"], True),
            (["ready-to-merge"], True),
            (["bug", "copilot-completed"], True),
            (["ready-to-merge", "enhancement"], True),
        ]
        
        for labels, expected in test_cases:
            with self.subTest(labels=labels):
                has_completion_label = any(
                    label in completion_labels
                    for label in labels
                )
                self.assertTrue(has_completion_label,
                              f"Should detect completion label in {labels}")
    
    def test_label_detection_negative(self):
        """Test that completion labels are not falsely detected."""
        completion_labels = ["copilot-completed", "ready-to-merge"]
        
        test_cases = [
            (["bug"], False),
            (["enhancement"], False),
            (["wip", "in-progress"], False),
            (["needs-review"], False),
        ]
        
        for labels, expected in test_cases:
            with self.subTest(labels=labels):
                has_completion_label = any(
                    label in completion_labels
                    for label in labels
                )
                self.assertFalse(has_completion_label,
                               f"Should not detect completion label in {labels}")
    
    def test_combined_detection_logic(self):
        """Test the complete detection logic with various scenarios."""
        # Scenario 1: Copilot PR with completion label
        self.assertTrue(
            self._should_pass(
                is_copilot_pr=True,
                has_completion_label=True,
                has_completion_marker=False,
                minutes_since_last_commit=1,
                has_wip_marker=False
            ),
            "Should pass with completion label"
        )
        
        # Scenario 2: Copilot PR with completion marker in commit
        self.assertTrue(
            self._should_pass(
                is_copilot_pr=True,
                has_completion_label=False,
                has_completion_marker=True,
                minutes_since_last_commit=1,
                has_wip_marker=False
            ),
            "Should pass with completion marker"
        )
        
        # Scenario 3: Copilot PR with old commit (>5 min)
        self.assertTrue(
            self._should_pass(
                is_copilot_pr=True,
                has_completion_label=False,
                has_completion_marker=False,
                minutes_since_last_commit=6,
                has_wip_marker=False
            ),
            "Should pass with old commit"
        )
        
        # Scenario 4: Copilot PR with WIP marker (should fail)
        self.assertFalse(
            self._should_pass(
                is_copilot_pr=True,
                has_completion_label=False,
                has_completion_marker=False,
                minutes_since_last_commit=1,
                has_wip_marker=True
            ),
            "Should fail with WIP marker"
        )
        
        # Scenario 5: Copilot PR with recent activity, no clear signals
        self.assertFalse(
            self._should_pass(
                is_copilot_pr=True,
                has_completion_label=False,
                has_completion_marker=False,
                minutes_since_last_commit=1.5,
                has_wip_marker=False
            ),
            "Should fail with recent activity"
        )
        
        # Scenario 6: Non-Copilot PR (should always pass)
        self.assertTrue(
            self._should_pass(
                is_copilot_pr=False,
                has_completion_label=False,
                has_completion_marker=False,
                minutes_since_last_commit=0.5,
                has_wip_marker=True
            ),
            "Should pass for non-Copilot PR"
        )
    
    def _should_pass(self, is_copilot_pr, has_completion_label, 
                     has_completion_marker, minutes_since_last_commit, 
                     has_wip_marker):
        """
        Simulate the Copilot Sentinel workflow decision logic.
        
        Returns True if the check should pass, False if it should fail.
        """
        # Not a Copilot PR - always pass
        if not is_copilot_pr:
            return True
        
        # Has completion label - pass
        if has_completion_label:
            return True
        
        # Has completion marker in commit - pass
        if has_completion_marker:
            return True
        
        # Old commit (>5 minutes) - pass
        if minutes_since_last_commit > 5:
            return True
        
        # Has WIP marker - fail
        if has_wip_marker:
            return False
        
        # Recent activity (<2 minutes) - fail
        if minutes_since_last_commit < 2:
            return False
        
        # No clear signals, but not too recent - pass
        return True


def run_tests():
    """Run all tests and print results."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCopilotSentinelLogic)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
