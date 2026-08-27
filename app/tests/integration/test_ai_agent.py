"""US5 AI-agent test integration (T067, FR-013, SC-006).

Verifies the AI-agent plugin returns a bounded grade with pros/cons and folds
into the weighted mean like a metric test. Uses the deterministic stub provider.
"""
from __future__ import annotations

import os
import tempfile

from src.services.grading import ResultInput, weighted_mean
from src.tests_plugins.ai_agent_example import factory as ai_factory
from src.tests_plugins.registry import PluginInput

SOURCE = '''
# A well-commented module.
def greet(name: str) -> str:
    """Return a greeting."""
    # build the message
    return f"Hello {name}"
'''


def _write(source: str) -> str:
    d = tempfile.mkdtemp(prefix="agon-ai-")
    with open(os.path.join(d, "main.py"), "w", encoding="utf-8") as fh:
        fh.write(source)
    return d


def test_ai_agent_returns_bounded_grade_with_evidence():
    plugin = ai_factory()
    out = plugin.run(PluginInput(submission_path=_write(SOURCE), config={"theme": "readability"}))
    assert 0.0 <= out.grade <= 100.0
    assert out.pros or out.cons


def test_ai_agent_folds_into_weighted_mean():
    plugin = ai_factory()
    ai = plugin.run(PluginInput(submission_path=_write(SOURCE), config={"theme": "readability"}))
    # AI grade combined with a metric grade using weights.
    final = weighted_mean(
        [
            ResultInput("metric", grade=80.0, weight=1.0),
            ResultInput("ai", grade=ai.grade, weight=1.0),
        ]
    )
    assert final == (80.0 + ai.grade) / 2


def test_ai_agent_empty_source_scores_zero():
    plugin = ai_factory()
    d = tempfile.mkdtemp(prefix="agon-ai-empty-")
    out = plugin.run(PluginInput(submission_path=d))
    assert out.grade == 0.0
    assert out.cons
