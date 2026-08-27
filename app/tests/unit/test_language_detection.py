"""Unit tests for language detection (FR-002, FR-016)."""
import pytest

from src.services.language_detection import (
    SUPPORTED_LANGUAGE,
    UnsupportedSubmissionError,
    detect_language,
)


def test_accepts_python_submission():
    assert detect_language(["main.py", "utils.py"]).language == SUPPORTED_LANGUAGE


def test_rejects_empty_submission():
    with pytest.raises(UnsupportedSubmissionError):
        detect_language([])


def test_rejects_non_python_submission():
    with pytest.raises(UnsupportedSubmissionError):
        detect_language(["Main.java", "pom.xml"])


def test_accepts_mixed_with_python_present():
    assert detect_language(["README.md", "app.py"]).language == SUPPORTED_LANGUAGE
