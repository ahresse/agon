"""Language detection (FR-002, FR-016).

Detects the primary language of an uploaded submission from its file set and
rejects anything that is not Python, as well as empty or source-less uploads.
Kept dependency-free and pure for testability.
"""
from __future__ import annotations

from dataclasses import dataclass

SUPPORTED_LANGUAGE = "python"
_PYTHON_EXTENSIONS = {".py", ".pyi"}


class UnsupportedSubmissionError(ValueError):
    """Raised when a submission is not assessable (FR-002, FR-016)."""


@dataclass(frozen=True)
class DetectionResult:
    language: str


def detect_language(file_names: list[str]) -> DetectionResult:
    """Detect language from archive member file names.

    Accepts a submission only when it contains at least one Python source file.
    Raises UnsupportedSubmissionError for empty, source-less, or non-Python input.
    """
    if not file_names:
        raise UnsupportedSubmissionError("Submission is empty; no files were found.")

    has_python = any(_has_ext(name, _PYTHON_EXTENSIONS) for name in file_names)
    if not has_python:
        raise UnsupportedSubmissionError(
            "Unsupported submission: only Python code is supported. "
            "No Python source files were detected."
        )
    return DetectionResult(language=SUPPORTED_LANGUAGE)


def _has_ext(name: str, extensions: set[str]) -> bool:
    lowered = name.lower()
    return any(lowered.endswith(ext) for ext in extensions)
