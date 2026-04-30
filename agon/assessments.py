"""Assessment definitions for agon."""

from __future__ import annotations

import logging
import re
import shlex
import warnings
from dataclasses import dataclass
from typing import Callable

MAX_GRADE = 20.0
_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class AssessmentExecution:
    """Normalized command execution data for an assessment."""

    name: str
    target_path: str
    stdout: str
    stderr: str
    returncode: int


@dataclass(frozen=True)
class AssessmentResult:
    """Final result for one assessment."""

    name: str
    command: str
    grade: float
    weight: float
    stdout: str
    stderr: str
    returncode: int


AssessmentEvaluator = Callable[[AssessmentExecution], float]
AssessmentCommandBuilder = Callable[[str], str]
AssessmentCommandRunner = Callable[[str], object]
DependencyInstaller = Callable[[str], None]


@dataclass(frozen=True)
class AssessmentSpec:
    """Definition of a reusable assessment."""

    name: str
    weight: float
    command_builder: AssessmentCommandBuilder
    evaluator: AssessmentEvaluator
    required_debian_packages: tuple[str, ...] = ()


ArchiveFormatCheck = Callable[[AssessmentExecution], str | None]


def _build_archive_format_command(target_path: str) -> str:
    quoted_target = shlex.quote(target_path)
    return f"python3 -m tarfile -l {quoted_target} >/dev/null"


def _build_pylint_command(target_path: str) -> str:
    return f"pylint {shlex.quote(target_path)}/*"


def _build_flake8_command(target_path: str) -> str:
    quoted_target = shlex.quote(target_path)
    return (
        f"python_loc=$(find {quoted_target} -type f -name '*.py' -print0 2>/dev/null | "
        "xargs -0 -r cat | wc -l); "
        "python_loc=${python_loc//[[:space:]]/}; "
        "echo AGON_LOC:${python_loc:-0}; "
        f"flake8 {quoted_target}"
    )


def _check_archive_format_extension(execution: AssessmentExecution) -> str | None:
    """Ensure the assessed archive uses the required .tar.gz suffix."""
    if execution.target_path.endswith(".tar.gz"):
        return None
    return f"Expected a .tar.gz archive: {execution.target_path}"


def _check_archive_format_content(execution: AssessmentExecution) -> str | None:
    """Ensure the assessed archive is a valid tar.gz payload."""
    if execution.returncode == 0:
        return None
    return (
        execution.stderr
        or execution.stdout
        or f"Archive format validation failed: {execution.target_path}"
    )


ARCHIVE_FORMAT_CHECKS: tuple[ArchiveFormatCheck, ...] = (
    _check_archive_format_extension,
    _check_archive_format_content,
)


def _evaluate_archive_format(execution: AssessmentExecution) -> float:
    failures = [
        message
        for check in ARCHIVE_FORMAT_CHECKS
        if (message := check(execution)) is not None
    ]
    if not failures:
        return MAX_GRADE

    warnings.warn("\n".join(failures), RuntimeWarning, stacklevel=2)
    penalty_per_failed_check = 10.0
    penalty = penalty_per_failed_check * len(failures)
    return max(0.0, MAX_GRADE - penalty)


def _evaluate_pylint(execution: AssessmentExecution) -> float:
    combined = execution.stdout + execution.stderr
    match = re.search(r"rated at\s+([0-9]+\.[0-9]+)/10", combined)
    if match:
        return max(0, min(MAX_GRADE, float(match.group(1)) * 2))
    return 0 if execution.returncode != 0 else MAX_GRADE


def _evaluate_flake8(execution: AssessmentExecution) -> float:
    _LOGGER.debug("Flake8 exit_code=%s target=%s", execution.returncode, execution.target_path)

    output_text = execution.stdout + "\n" + execution.stderr
    line_of_code = 0
    loc_match = re.search(r"AGON_LOC:(\d+)", output_text)
    if loc_match:
        line_of_code = int(loc_match.group(1))

    _LOGGER.info("Flake8 LOC=%s target=%s", line_of_code, execution.target_path)

    if execution.returncode == 0:
        _LOGGER.info("Flake8 passed with no errors for target=%s", execution.target_path)
        return MAX_GRADE

    errors = [
        line
        for line in output_text.splitlines()
        if line.strip() and not line.startswith("AGON_LOC:")
    ]
    _LOGGER.info("Flake8 reported %s issue lines for target=%s", len(errors), execution.target_path)

    penalty = 0.0
    if line_of_code > 0:
        penalty = len(errors) * MAX_GRADE / line_of_code

    final_grade = max(0, MAX_GRADE - penalty)
    _LOGGER.info(
        "Flake8 penalty=%.3f grade=%.3f target=%s", penalty, final_grade, execution.target_path
    )

    return final_grade


ASSESSMENTS: dict[str, AssessmentSpec] = {
    "archive-format": AssessmentSpec(
        name="archive-format",
        weight=0.2,
        command_builder=_build_archive_format_command,
        evaluator=_evaluate_archive_format,
    ),
    "pylint": AssessmentSpec(
        name="pylint",
        weight=0.8,
        command_builder=_build_pylint_command,
        evaluator=_evaluate_pylint,
        required_debian_packages=("pylint",),
    ),
    "flake8": AssessmentSpec(
        name="flake8",
        weight=0.4,
        command_builder=_build_flake8_command,
        evaluator=_evaluate_flake8,
        required_debian_packages=("flake8",),
    ),
}


def run_assessment(
    assessment: AssessmentSpec,
    target_path: str,
    command_runner: AssessmentCommandRunner,
    dependency_installer: DependencyInstaller | None = None,
) -> AssessmentResult:
    """Run one assessment in any execution environment."""
    if dependency_installer is not None:
        for package_name in assessment.required_debian_packages:
            dependency_installer(package_name)

    command = assessment.command_builder(target_path)
    process = command_runner(command)
    stdout = str(getattr(process, "stdout", "")).strip()
    stderr = str(getattr(process, "stderr", "")).strip()
    returncode = int(getattr(process, "returncode", 1))
    execution = AssessmentExecution(
        name=assessment.name,
        target_path=target_path,
        stdout=stdout,
        stderr=stderr,
        returncode=returncode,
    )
    grade = max(0, min(MAX_GRADE, assessment.evaluator(execution)))
    return AssessmentResult(
        name=assessment.name,
        command=command,
        grade=grade,
        weight=assessment.weight,
        stdout=stdout,
        stderr=stderr,
        returncode=returncode,
    )
