"""Tests for evidence-log capture and incremental progress (bug fix).

- Evidence logs are captured on each test result and rendered in the fragment.
- run_review commits each result as it completes so live progress advances.
"""
from __future__ import annotations

import os
import tempfile

import pytest

pytest.importorskip("sqlalchemy")

from src.db import SessionLocal, engine, init_db  # noqa: E402
from src.models import Base, Review, Submission, User  # noqa: E402
from src.models import TestResult as _TestResult  # noqa: E402
from src.models.enums import ResultStatus, Role, ReviewStatus  # noqa: E402
from src.runners.container_runner import LocalSubprocessRunner  # noqa: E402
from src.runners.test_runner import run_single_test  # noqa: E402
from src.services.review_service import run_review  # noqa: E402
from src.tests_plugins.registry import PluginInput, PluginOutput  # noqa: E402


class _PassPlugin:
    key = "quality.lint_ruff"  # any seeded key

    def run(self, payload: PluginInput) -> PluginOutput:
        return PluginOutput(grade=90.0, pros=["clean"], cons=[], log="ruff: no violations\nmain.py OK")


class _FindingsPlugin:
    key = "quality.complexity_radon"

    def run(self, payload: PluginInput) -> PluginOutput:
        # No explicit log -> runner synthesizes one from pros/cons.
        return PluginOutput(grade=60.0, pros=["ok"], cons=["fn foo is complex"])


class _CrashPlugin:
    key = "quality.security_bandit"

    def run(self, payload: PluginInput) -> PluginOutput:
        raise RuntimeError("boom")


class TestEvidenceLogCapture:
    def test_explicit_log_preserved(self):
        r = run_single_test(LocalSubprocessRunner(), _PassPlugin(), PluginInput(submission_path="/x"))
        assert r.status == ResultStatus.SUCCESS
        assert "ruff: no violations" in r.log

    def test_log_synthesized_from_findings_when_absent(self):
        r = run_single_test(LocalSubprocessRunner(), _FindingsPlugin(), PluginInput(submission_path="/x"))
        assert "fn foo is complex" in r.log
        assert "Issues found" in r.log

    def test_failure_log_has_reason_and_details(self):
        r = run_single_test(LocalSubprocessRunner(), _CrashPlugin(), PluginInput(submission_path="/x"))
        assert r.status == ResultStatus.FAILED
        assert "RuntimeError: boom" in r.log
        assert "--- details ---" in r.log


class TestIncrementalPersistAndLog:
    @pytest.fixture
    def db(self):
        Base.metadata.drop_all(bind=engine)
        init_db()
        session = SessionLocal()
        yield session
        session.close()

    def _review(self, db):
        u = User(username="rev", password_hash="x", role=Role.REVIEWER)
        db.add(u)
        db.flush()
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "main.py"), "w") as fh:
            fh.write("x = 1\n")
        sub = Submission(candidate_label="c", detected_language="python", storage_path=d, uploaded_by=u.id)
        db.add(sub)
        db.flush()
        r = Review(submission_id=sub.id, reviewer_id=u.id)
        db.add(r)
        db.commit()
        return r, d

    def test_results_and_logs_persisted(self, db, monkeypatch):
        # Register two fake plugins under seeded test keys.
        from src.models import Test, TestType
        from src.tests_plugins.registry import registry

        for key in ("quality.lint_ruff", "quality.complexity_radon"):
            db.add(Test(key=key, name=key, type=TestType.METRIC, enabled=True, default_weight=1.0))
        db.commit()
        for key, factory in (("quality.lint_ruff", _PassPlugin), ("quality.complexity_radon", _FindingsPlugin)):
            if key in registry.keys():
                monkeypatch.setitem(registry._factories, key, factory)  # type: ignore[attr-defined]
            else:
                registry.register(key, factory)

        review, d = self._review(db)
        run_review(db, review, d, LocalSubprocessRunner(), 30)
        db.refresh(review)
        results = db.query(_TestResult).filter(_TestResult.review_id == review.id).all()
        assert len(results) == 2
        # Every result carries a non-empty evidence log.
        assert all((res.log or "") != "" for res in results)
        assert any("ruff" in (res.log or "") for res in results)
        assert review.status in (ReviewStatus.COMPLETED, ReviewStatus.FAILED)
