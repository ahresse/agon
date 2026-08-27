"""Unit tests for the git-quality plugin (feature 003).

Organized into topic subsections:

- TestGitLogParsing      — NUL/record parsing of `git log` output
- TestCommitMessageQuality — message scoring heuristics
- TestCommitGranularity  — commit-count granularity scoring
- TestCommitSigning      — signing is rewarded, not required
- TestNoGitHistory       — missing .git is penalized (low, non-zero)
- TestMalformedGit       — corrupted repo raises (runner isolates to FAILED)
- TestDeterminism        — same history -> same grade
- TestRealRepo           — end-to-end against tiny real repositories
"""
from __future__ import annotations

import os
import subprocess
import tempfile

import pytest

from src.tests_plugins.quality import git_history
from src.tests_plugins.quality.git_history import (
    Commit,
    GitHistoryPlugin,
    GitRepositoryError,
    grade_commits,
    parse_git_log,
)
from src.tests_plugins.registry import PluginInput


def _c(subject: str, signing: str = "N", body: str = "") -> Commit:
    return Commit(signing=signing, subject=subject, body=body)


# --------------------------------------------------------------------------- #
# git log parsing
# --------------------------------------------------------------------------- #
class TestGitLogParsing:
    """The NUL-and-record-separated log format parses into Commit records."""

    def test_parses_multiple_records(self):
        out = "G\x00feat: add thing\x00body one\x1eN\x00fix: bug\x00\x1e"
        commits = parse_git_log(out)
        assert len(commits) == 2
        assert commits[0].signing == "G"
        assert commits[0].subject == "feat: add thing"
        assert commits[1].subject == "fix: bug"

    def test_empty_output_is_no_commits(self):
        assert parse_git_log("") == []

    def test_missing_fields_default_safely(self):
        commits = parse_git_log("N\x1e")
        assert len(commits) == 1
        assert commits[0].subject == ""


# --------------------------------------------------------------------------- #
# Message quality
# --------------------------------------------------------------------------- #
class TestCommitMessageQuality:
    """Message scoring rewards clear subjects and penalizes noise/empty/too-long."""

    def test_good_messages_score_high(self):
        commits = [
            _c("feat: add upload endpoint"),
            _c("refactor: extract grading service"),
            _c("test: cover weight overrides"),
        ]
        out = grade_commits(commits)
        assert out.grade >= 60
        assert any("clear" in p.lower() for p in out.pros)

    def test_noise_and_empty_messages_penalized(self):
        good = grade_commits([_c("feat: add real feature")] * 3).grade
        noisy = grade_commits([_c("wip"), _c("fix"), _c("")]).grade
        assert noisy < good

    def test_overly_long_subject_penalized(self):
        long_subject = "x" * 120
        assert grade_commits([_c(long_subject)] * 3).grade < grade_commits([_c("feat: ok work")] * 3).grade


# --------------------------------------------------------------------------- #
# Granularity
# --------------------------------------------------------------------------- #
class TestCommitGranularity:
    """A monolithic single commit scores below a well-split history."""

    def test_single_commit_scores_low_granularity(self):
        one = grade_commits([_c("feat: everything at once")])
        many = grade_commits([_c(f"feat: step {i} done") for i in range(5)])
        assert many.grade > one.grade
        assert any("monolithic" in c.lower() for c in one.cons)

    def test_healthy_history_flagged_as_pro(self):
        out = grade_commits([_c(f"feat: coherent step {i}") for i in range(4)])
        assert any("coherent" in p.lower() for p in out.pros)


# --------------------------------------------------------------------------- #
# Signing (rewarded, not required)
# --------------------------------------------------------------------------- #
class TestCommitSigning:
    """Signed histories score higher; unsigned is allowed with lower score."""

    def test_signed_scores_higher_than_identical_unsigned(self):
        subjects = [f"feat: coherent step {i}" for i in range(4)]
        signed = grade_commits([_c(s, signing="G") for s in subjects])
        unsigned = grade_commits([_c(s, signing="N") for s in subjects])
        assert signed.grade > unsigned.grade
        assert any("signed" in p.lower() for p in signed.pros)

    def test_unsigned_reported_as_con_not_failure(self):
        out = grade_commits([_c(f"feat: step {i} work") for i in range(3)])
        assert out.grade > 0
        assert any("signed" in c.lower() for c in out.cons)

    def test_partial_signing_reported(self):
        commits = [_c("feat: a work", "G"), _c("feat: b work", "N"), _c("feat: c work", "G")]
        out = grade_commits(commits)
        assert any("%" in p for p in out.pros)


# --------------------------------------------------------------------------- #
# No git history (penalized)
# --------------------------------------------------------------------------- #
class TestNoGitHistory:
    """A submission without a .git is penalized with a low, non-zero grade."""

    def test_missing_git_dir_low_grade(self):
        d = tempfile.mkdtemp(prefix="agon-nogit-")
        with open(os.path.join(d, "main.py"), "w") as fh:
            fh.write("x = 1\n")
        out = GitHistoryPlugin().run(PluginInput(submission_path=d, timeout_seconds=30))
        assert out.grade <= 25
        assert any("no git history" in c.lower() for c in out.cons)

    def test_empty_history_low_grade(self):
        out = grade_commits([])
        assert out.grade <= 25


# --------------------------------------------------------------------------- #
# Malformed repo (runner isolates to FAILED)
# --------------------------------------------------------------------------- #
class TestMalformedGit:
    """A present but unreadable .git raises so the runner records FAILED."""

    def test_corrupt_git_dir_raises(self, monkeypatch):
        d = tempfile.mkdtemp(prefix="agon-badgit-")
        os.makedirs(os.path.join(d, ".git"))  # present but not a real repo

        def fake_run(args, cwd, timeout):
            from src.tests_plugins.quality.common import ToolResult

            return ToolResult(returncode=128, stdout="", stderr="fatal: not a git repository")

        monkeypatch.setattr(git_history.common, "run_tool", fake_run)
        with pytest.raises(GitRepositoryError):
            GitHistoryPlugin().run(PluginInput(submission_path=d, timeout_seconds=30))

    def test_uses_safe_directory_flag(self, monkeypatch):
        # Regression: foreign-owned repos in the container need safe.directory=*.
        d = tempfile.mkdtemp(prefix="agon-safe-")
        os.makedirs(os.path.join(d, ".git"))
        captured = {}

        def fake_run(args, cwd, timeout):
            from src.tests_plugins.quality.common import ToolResult

            captured["args"] = args
            return ToolResult(returncode=0, stdout="N\x00feat: work here\x00\x1e", stderr="")

        monkeypatch.setattr(git_history.common, "run_tool", fake_run)
        GitHistoryPlugin().run(PluginInput(submission_path=d, timeout_seconds=30))
        assert "safe.directory=*" in captured["args"]


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #
class TestDeterminism:
    """The same history yields the same grade."""

    def test_same_history_same_grade(self):
        commits = [_c(f"feat: step {i} done", "G") for i in range(4)]
        assert grade_commits(commits).grade == grade_commits(commits).grade


# --------------------------------------------------------------------------- #
# Real repositories (end-to-end, requires the git binary)
# --------------------------------------------------------------------------- #
def _git(cwd, *args):
    env = {**os.environ, "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@e.x",
           "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@e.x"}
    subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True, text=True, env=env)


def _make_repo(commit_subjects) -> str:
    d = tempfile.mkdtemp(prefix="agon-repo-")
    _git(d, "init", "-q")
    _git(d, "config", "commit.gpgsign", "false")
    for i, subject in enumerate(commit_subjects):
        with open(os.path.join(d, f"f{i}.py"), "w") as fh:
            fh.write(f"x = {i}\n")
        _git(d, "add", "-A")
        _git(d, "commit", "-q", "-m", subject)
    return d


_HAS_GIT = subprocess.run(["git", "--version"], capture_output=True).returncode == 0


@pytest.mark.skipif(not _HAS_GIT, reason="git binary not available")
class TestRealRepo:
    """End-to-end grading against tiny real repositories."""

    def test_well_formed_history_scores_well(self):
        d = _make_repo(
            ["feat: add module", "refactor: split helpers", "test: cover helpers", "docs: add readme"]
        )
        out = GitHistoryPlugin().run(PluginInput(submission_path=d, timeout_seconds=60))
        assert 0 <= out.grade <= 100
        assert out.grade >= 40

    def test_single_noisy_commit_scores_lower(self):
        good = GitHistoryPlugin().run(
            PluginInput(submission_path=_make_repo(
                ["feat: a work", "feat: b work", "feat: c work"]), timeout_seconds=60)
        ).grade
        bad = GitHistoryPlugin().run(
            PluginInput(submission_path=_make_repo(["wip"]), timeout_seconds=60)
        ).grade
        assert bad < good

    def test_nested_repo_is_found(self):
        parent = tempfile.mkdtemp(prefix="agon-nested-")
        inner = _make_repo(["feat: add module", "test: add tests", "docs: readme"])
        target = os.path.join(parent, "project")
        os.rename(inner, target)
        out = GitHistoryPlugin().run(PluginInput(submission_path=parent, timeout_seconds=60))
        assert out.grade >= 40
