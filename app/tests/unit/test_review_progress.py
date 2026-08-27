"""Unit tests for review progress + ETA computation (feature 006).

Topic subsections:
- TestProgressFraction   — completed/total, failures count, terminal
- TestEta                — estimating…, non-negative, monotonic, terminal=0
- TestEdgeCases          — total=0, over-count clamping
"""
from __future__ import annotations

from src.models.enums import ReviewStatus
from src.services.review_progress import compute_progress


class TestProgressFraction:
    def test_half_done(self):
        p = compute_progress(total=4, completed=2, status=ReviewStatus.RUNNING, elapsed_seconds=10)
        assert p.completed == 2 and p.total == 4
        assert p.fraction == 0.5
        assert p.percent == 50
        assert p.is_terminal is False

    def test_failures_count_as_completed(self):
        # The caller passes total result rows (successes + failures), so a run
        # with a failed test still advances.
        p = compute_progress(total=3, completed=3, status=ReviewStatus.COMPLETED, elapsed_seconds=9)
        assert p.fraction == 1.0

    def test_terminal_is_full(self):
        for st in (ReviewStatus.COMPLETED, ReviewStatus.FAILED):
            p = compute_progress(total=5, completed=5, status=st, elapsed_seconds=20)
            assert p.is_terminal is True
            assert p.fraction == 1.0
            assert p.eta_seconds == 0


class TestEta:
    def test_estimating_when_none_completed(self):
        p = compute_progress(total=4, completed=0, status=ReviewStatus.RUNNING, elapsed_seconds=5)
        assert p.eta_seconds is None  # -> "estimating…"

    def test_eta_non_negative(self):
        p = compute_progress(total=4, completed=1, status=ReviewStatus.RUNNING, elapsed_seconds=10)
        assert p.eta_seconds is not None and p.eta_seconds >= 0

    def test_eta_decreases_as_more_complete(self):
        # Fixed elapsed: more completed -> lower per-test estimate * fewer remaining.
        e1 = compute_progress(4, 1, ReviewStatus.RUNNING, 10).eta_seconds
        e2 = compute_progress(4, 2, ReviewStatus.RUNNING, 10).eta_seconds
        e3 = compute_progress(4, 3, ReviewStatus.RUNNING, 10).eta_seconds
        assert e1 > e2 > e3
        assert e3 >= 0

    def test_eta_zero_when_terminal(self):
        p = compute_progress(4, 4, ReviewStatus.COMPLETED, 40)
        assert p.eta_seconds == 0

    def test_eta_formula(self):
        # 10s elapsed / 2 completed = 5s per test; 2 remaining -> 10s.
        p = compute_progress(total=4, completed=2, status=ReviewStatus.RUNNING, elapsed_seconds=10)
        assert p.eta_seconds == 10


class TestEdgeCases:
    def test_total_zero_is_full_no_negative_eta(self):
        p = compute_progress(total=0, completed=0, status=ReviewStatus.RUNNING, elapsed_seconds=3)
        assert p.fraction == 1.0
        # No remaining work -> eta 0 (completed<=0 but nothing remains).
        assert (p.eta_seconds is None) or (p.eta_seconds >= 0)

    def test_completed_clamped_to_total(self):
        p = compute_progress(total=3, completed=99, status=ReviewStatus.RUNNING, elapsed_seconds=9)
        assert p.completed == 3
        assert p.fraction == 1.0
        assert p.eta_seconds is not None and p.eta_seconds >= 0
