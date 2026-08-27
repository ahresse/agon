"""Integration test: upload→run→grade happy path over the domain core (US1).

Exercises language detection, the metric plugin running via a container runner,
failure isolation, and weighted-mean grading end-to-end without the HTTP layer.
"""
import os
import tempfile

from src.models.enums import ResultStatus
from src.runners.container_runner import LocalSubprocessRunner
from src.runners.test_runner import run_single_test
from src.services.grading import ResultInput, weighted_mean
from src.services.language_detection import detect_language
from src.tests_plugins.metric_example import factory as metric_factory

GOOD_SOURCE = '''
def add(a, b):
    """Return the sum of a and b."""
    return a + b


def sub(a, b):
    """Return the difference of a and b."""
    return a - b
'''


def _write_submission(source: str) -> str:
    d = tempfile.mkdtemp(prefix="agon-sub-")
    with open(os.path.join(d, "main.py"), "w", encoding="utf-8") as fh:
        fh.write(source)
    return d


def test_upload_run_grade_happy_path():
    path = _write_submission(GOOD_SOURCE)
    # language detection accepts Python
    assert detect_language(["main.py"]).language == "python"

    runner = LocalSubprocessRunner()
    plugin = metric_factory()
    from src.tests_plugins.registry import PluginInput

    result = run_single_test(runner, plugin, PluginInput(submission_path=path))
    assert result.status == ResultStatus.SUCCESS
    assert 0 <= result.grade <= 100

    final = weighted_mean([ResultInput(result.test_key, result.grade, weight=1.0)])
    assert final == result.grade


def test_failure_isolation_still_produces_grade():
    # One failed test (grade 0) plus one passing test still yields a final grade.
    results = [
        ResultInput("failing", grade=0.0, weight=1.0),
        ResultInput("passing", grade=90.0, weight=1.0),
    ]
    assert weighted_mean(results) == 45.0
