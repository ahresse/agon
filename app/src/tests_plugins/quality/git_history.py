"""git_history plugin (feature 003): assess candidate commit quality.

Grades a submission's git history on three axes and folds into the same weighted
model as other tests:

- **Message quality** — non-empty, adequate subject length, no noise words.
- **Granularity** — multiple coherent commits (not one monolith, not all trivial).
- **Signing** — signed commits are rewarded (not required); the signing ratio is
  reported as evidence.

A submission with no git history is penalized with a low grade (FR-005). A
corrupted/unreadable repository raises so the runner records the test as FAILED
(FR-007). Reads the history with the container's ``git`` (Constitution II).

Parsing/scoring is separated from the git invocation so the scoring is unit
testable without a real repository.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

from src.tests_plugins.quality import common
from src.tests_plugins.registry import PluginInput, PluginOutput

KEY = "quality.git_history"

# Only inspect a recent window so large histories stay within the time limit (FR-008).
MAX_COMMITS = 200

# NUL-delimited fields per commit: signing flag, subject, body.
_LOG_FORMAT = "%G?%x00%s%x00%b%x1e"

_NOISE_SUBJECTS = {"wip", "fix", "fixes", "stuff", "asdf", "temp", "tmp", "update", "changes", "."}
_MAX_SUBJECT_LEN = 72
_MIN_SUBJECT_LEN = 5
_NO_GIT_GRADE = 15.0  # low, non-zero: reflects missing version control (FR-005)


class GitRepositoryError(RuntimeError):
    """Raised when a present .git cannot be read (corrupted history)."""


@dataclass(frozen=True)
class Commit:
    signing: str  # git %G? flag: G/U good, N none, B bad, E error, etc.
    subject: str
    body: str

    @property
    def signed(self) -> bool:
        return self.signing in {"G", "U"}


class GitHistoryPlugin:
    key = KEY

    def run(self, payload: PluginInput) -> PluginOutput:
        root = payload.submission_path
        git_dir = _find_git_dir(root)
        if git_dir is None:
            return PluginOutput(
                grade=_NO_GIT_GRADE,
                pros=[],
                cons=["No git history found; submission is not under version control."],
            )
        commits = _read_commits(root, git_dir, payload.timeout_seconds)
        return grade_commits(commits, inspected_window=len(commits) >= MAX_COMMITS)


# --------------------------------------------------------------------------- #
# Scoring (pure; unit-testable without a repo)
# --------------------------------------------------------------------------- #
def grade_commits(commits: list[Commit], inspected_window: bool = False) -> PluginOutput:
    if not commits:
        # A present but empty history reads as no usable commits.
        return PluginOutput(grade=_NO_GIT_GRADE, cons=["Git history contains no commits."])

    msg_score = _message_quality(commits)
    gran_score = _granularity(commits)
    sign_ratio = sum(1 for c in commits if c.signed) / len(commits)
    sign_score = 100.0 * sign_ratio

    # Weighted blend: message 45%, granularity 35%, signing 20% (signing rewarded,
    # not required — a fully unsigned but otherwise excellent history still scores well).
    grade = common.cap(0.45 * msg_score + 0.35 * gran_score + 0.20 * sign_score)

    pros: list[str] = []
    cons: list[str] = []

    if msg_score >= 80:
        pros.append("Commit messages are clear and well-formed.")
    else:
        cons.append("Some commit messages are empty, too long, or noise ('wip'/'fix').")

    if gran_score >= 70:
        pros.append(f"History is split into {len(commits)} coherent commits.")
    elif len(commits) == 1:
        cons.append("Single monolithic commit; work is not broken into steps.")
    else:
        cons.append("Commit granularity could be improved.")

    if sign_ratio >= 0.999:
        pros.append("All commits are signed.")
    elif sign_ratio > 0:
        pros.append(f"{sign_ratio:.0%} of commits are signed.")
    else:
        cons.append("No commits are signed (signing is rewarded but not required).")

    if inspected_window:
        cons.append(f"Only the most recent {MAX_COMMITS} commits were assessed.")

    return PluginOutput(grade=grade, pros=pros, cons=cons)


def _message_quality(commits: list[Commit]) -> float:
    good = 0
    for c in commits:
        subject = c.subject.strip()
        if not subject:
            continue
        if len(subject) < _MIN_SUBJECT_LEN or len(subject) > _MAX_SUBJECT_LEN:
            continue
        if subject.lower().rstrip(".!") in _NOISE_SUBJECTS:
            continue
        good += 1
    return common.grade_from_ratio(good, len(commits))


def _granularity(commits: list[Commit]) -> float:
    n = len(commits)
    if n == 1:
        return 20.0
    if n == 2:
        return 60.0
    if 3 <= n <= 50:
        return 100.0
    # Very large histories are fine but slightly less focused per commit.
    return 85.0


# --------------------------------------------------------------------------- #
# Git invocation (side-effecting; thin wrapper)
# --------------------------------------------------------------------------- #
def _find_git_dir(root: str) -> str | None:
    if os.path.isfile(root):
        return None
    candidate = os.path.join(root, ".git")
    if os.path.isdir(candidate) or os.path.isfile(candidate):
        return candidate
    # Some archives nest the repo one level down (e.g. project/.git).
    for entry in sorted(os.listdir(root)):
        sub = os.path.join(root, entry, ".git")
        if os.path.isdir(sub) or os.path.isfile(sub):
            return sub
    return None


def _read_commits(root: str, git_dir: str, timeout: int) -> list[Commit]:
    work_tree = os.path.dirname(git_dir)
    try:
        result = common.run_tool(
            [
                "git",
                # The submission is injected with foreign ownership inside the
                # container; disable git's dubious-ownership guard for it.
                "-c",
                "safe.directory=*",
                "-C",
                work_tree,
                "log",
                f"--max-count={MAX_COMMITS}",
                f"--pretty=format:{_LOG_FORMAT}",
            ],
            cwd=work_tree,
            timeout=timeout,
        )
    except FileNotFoundError as exc:  # git binary missing in the environment
        raise GitRepositoryError("git is not available to read the history.") from exc
    except subprocess.SubprocessError as exc:
        raise GitRepositoryError("Failed to read git history.") from exc

    if result.returncode != 0:
        raise GitRepositoryError(
            f"git could not read the repository: {result.stderr.strip() or 'unknown error'}"
        )
    return parse_git_log(result.stdout)


def parse_git_log(stdout: str) -> list[Commit]:
    commits: list[Commit] = []
    for record in stdout.split("\x1e"):
        record = record.strip("\n")
        if not record.strip():
            continue
        fields = record.split("\x00")
        signing = fields[0] if len(fields) > 0 else "N"
        subject = fields[1] if len(fields) > 1 else ""
        body = fields[2] if len(fields) > 2 else ""
        commits.append(Commit(signing=signing or "N", subject=subject, body=body))
    return commits


def factory() -> GitHistoryPlugin:
    return GitHistoryPlugin()
