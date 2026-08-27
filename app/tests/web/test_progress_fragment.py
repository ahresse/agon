"""Web tests for the live progress fragment (feature 006).

Topic subsections:
- TestRunningFragment   — running review: progress bar + poll trigger
- TestTerminalFragment  — completed review: final breakdown, no poll trigger
- TestReopen            — reopening resumes/renders current state (US3)
- TestAuth              — non-owner denied (FR-009)
"""
from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from src.db import SessionLocal  # noqa: E402
from src.models import Review, Submission, User  # noqa: E402
from src.models import TestResult as _TestResult  # noqa: E402  (aliased: avoid pytest collection)
from src.models.enums import ResultStatus, ReviewStatus  # noqa: E402
from tests.web.conftest import login  # noqa: E402


def _make_review(status: ReviewStatus, completed_results: int = 0) -> str:
    """Create a review owned by 'reviewer' with N completed test results."""
    db = SessionLocal()
    try:
        reviewer = db.query(User).filter(User.username == "reviewer").first()
        sub = Submission(
            candidate_label="cand",
            detected_language="python",
            storage_path="/tmp/x",
            uploaded_by=reviewer.id,
        )
        db.add(sub)
        db.flush()
        review = Review(submission_id=sub.id, reviewer_id=reviewer.id, status=status)
        if status in (ReviewStatus.COMPLETED, ReviewStatus.FAILED):
            review.final_grade = 50.0
        db.add(review)
        db.flush()
        # Attach some completed test results (need a test id; reuse any enabled test).
        from src.models import Test

        tests = db.query(Test).limit(completed_results).all()
        for t in tests:
            db.add(
                _TestResult(
                    review_id=review.id,
                    test_id=t.id,
                    grade=80.0,
                    status=ResultStatus.SUCCESS,
                    pros=[],
                    cons=[],
                )
            )
        db.commit()
        return review.id
    finally:
        db.close()


class TestRunningFragment:
    def test_running_shows_progress_and_poll_trigger(self, client):
        login(client)
        rid = _make_review(ReviewStatus.RUNNING, completed_results=2)
        r = client.get(f"/ui/reviews/{rid}/progress")
        assert r.status_code == 200
        assert "<html" not in r.text.lower()  # fragment, not full page
        assert 'hx-trigger="every 2s"' in r.text
        assert "tests complete" in r.text
        assert "Status:" in r.text

    def test_detail_page_running_embeds_progress(self, client):
        login(client)
        rid = _make_review(ReviewStatus.RUNNING, completed_results=1)
        r = client.get(f"/ui/reviews/{rid}")
        assert r.status_code == 200
        assert 'id="review-progress"' in r.text
        assert 'hx-trigger="every 2s"' in r.text
        # Regression: the poll URL must carry the real review id (not empty).
        assert f'/ui/reviews/{rid}/progress' in r.text
        assert '/ui/reviews//progress' not in r.text


class TestTerminalFragment:
    def test_completed_shows_breakdown_no_poll(self, client):
        login(client)
        rid = _make_review(ReviewStatus.COMPLETED, completed_results=2)
        r = client.get(f"/ui/reviews/{rid}/progress")
        assert r.status_code == 200
        assert 'hx-trigger="every 2s"' not in r.text  # polling stops
        assert "completed" in r.text.lower()
        assert 'id="grade-breakdown"' in r.text  # final breakdown revealed

    def test_detail_page_completed_shows_breakdown_directly(self, client):
        login(client)
        rid = _make_review(ReviewStatus.COMPLETED, completed_results=2)
        r = client.get(f"/ui/reviews/{rid}")
        assert r.status_code == 200
        assert 'id="grade-breakdown"' in r.text
        assert 'hx-trigger="every 2s"' not in r.text


class TestReopen:
    def test_reopen_running_renders_current_progress(self, client):
        login(client)
        rid = _make_review(ReviewStatus.RUNNING, completed_results=3)
        # Simulate reopening: a fresh GET renders current state + keeps polling.
        r = client.get(f"/ui/reviews/{rid}/progress")
        assert r.status_code == 200
        assert 'hx-trigger="every 2s"' in r.text
        assert "3 /" in r.text  # current completed count reflected

    def test_reopen_finished_shows_result_only(self, client):
        login(client)
        rid = _make_review(ReviewStatus.FAILED, completed_results=1)
        r = client.get(f"/ui/reviews/{rid}")
        assert r.status_code == 200
        assert 'hx-trigger="every 2s"' not in r.text


class TestAuth:
    def test_non_owner_denied(self, client):
        # Create a running review owned by 'reviewer', then request as 'admin'.
        login(client)
        rid = _make_review(ReviewStatus.RUNNING, completed_results=1)
        login(client, "admin")
        r = client.get(f"/ui/reviews/{rid}/progress")
        assert r.status_code == 404
