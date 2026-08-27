"""Repo-hygiene meta-tests for Agon's OWN git history.

These assess the quality of the commits in *this* repository (not a candidate
submission). They run only when executed inside a git repository with a readable
history; otherwise they are skipped (e.g. shallow CI clones or tarball builds).

Policy (per project decision):
- Commit message conventions and atomicity are ENFORCED (hard assertions).
- Commit signing is REPORT-ONLY (informational), so the suite does not fail on
  unsigned commits.

Subsections:
- TestCommitMessageConventions
- TestCommitAtomicity
- TestCommitSigning (report-only)
"""
from __future__ import annotations

import os
import re
import subprocess

import pytest

# Conventional-commit-ish subject: type(optional-scope): summary
_SUBJECT_RE = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]+\))?: .+"
)
_MAX_SUBJECT_LEN = 80  # pragmatic modern limit


def _repo_root() -> str | None:
    here = os.path.dirname(os.path.abspath(__file__))
    proc = subprocess.run(
        ["git", "-C", here, "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip() if proc.returncode == 0 else None


_ROOT = _repo_root()


def _log(*fmt_args: str) -> list[str]:
    out = subprocess.run(
        ["git", "-C", _ROOT, "log", f"--pretty=format:{fmt_args[0]}"],
        capture_output=True,
        text=True,
    )
    return [ln for ln in out.stdout.splitlines()]


pytestmark = pytest.mark.skipif(_ROOT is None, reason="not inside a git repository")


# --------------------------------------------------------------------------- #
# Message conventions (enforced)
# --------------------------------------------------------------------------- #
class TestCommitMessageConventions:
    """Every commit subject follows a conventional, bounded-length format."""

    def test_all_subjects_are_conventional(self):
        subjects = _log("%s")
        assert subjects, "expected at least one commit"
        bad = [s for s in subjects if not _SUBJECT_RE.match(s)]
        assert not bad, f"non-conventional commit subjects: {bad}"

    def test_subjects_within_length_limit(self):
        subjects = _log("%s")
        too_long = [s for s in subjects if len(s) > _MAX_SUBJECT_LEN]
        assert not too_long, f"subjects exceed {_MAX_SUBJECT_LEN} chars: {too_long}"

    def test_no_empty_subjects(self):
        subjects = _log("%s")
        assert all(s.strip() for s in subjects)


# --------------------------------------------------------------------------- #
# Atomicity (enforced)
# --------------------------------------------------------------------------- #
class TestCommitAtomicity:
    """History is composed of multiple, non-empty commits."""

    def test_history_has_multiple_commits(self):
        assert len(_log("%H")) >= 2, "history should be split into multiple commits"

    def test_no_empty_commits(self):
        # A commit that changed nothing (same tree as its parent) is disallowed.
        hashes = _log("%H")
        empties: list[str] = []
        for h in hashes:
            show = subprocess.run(
                ["git", "-C", _ROOT, "show", "--stat", "--oneline", h],
                capture_output=True,
                text=True,
            )
            # First line is the subject; subsequent lines list changed files.
            body = "\n".join(show.stdout.splitlines()[1:])
            if not body.strip():
                empties.append(h)
        assert not empties, f"empty commits found: {empties}"


# --------------------------------------------------------------------------- #
# Signing (report-only)
# --------------------------------------------------------------------------- #
class TestCommitSigning:
    """Report the signing ratio without failing (signing is not required)."""

    def test_report_signing_ratio(self, capsys):
        flags = _log("%G?")
        if not flags:
            pytest.skip("no commits")
        signed = sum(1 for f in flags if f in {"G", "U"})
        ratio = signed / len(flags)
        with capsys.disabled():
            print(f"\n[repo-hygiene] commit signing: {signed}/{len(flags)} ({ratio:.0%}) signed")
        # Report-only: always passes.
        assert 0.0 <= ratio <= 1.0
