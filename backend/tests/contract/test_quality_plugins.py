"""Conformance test for the six Python quality metric plugins (T029).

Each plugin must return a deterministic 0-100 grade with structured pros/cons on
fixture code, and must run without requiring external tools (plugins degrade to
AST-based analysis when tools are absent). Also verifies per-anti-pattern
detection for stdlib_idioms (C1).
"""
from __future__ import annotations

import os
import tempfile

import pytest

from src.tests_plugins.quality.builtin import QUALITY_PLUGINS
from src.tests_plugins.registry import PluginInput

CLEAN_SOURCE = '''
"""A tidy module."""
from __future__ import annotations


def add(a: int, b: int) -> int:
    """Return the sum of a and b."""
    return a + b


def totals(values: list[int]) -> int:
    """Return the running total using an idiomatic comprehension."""
    return sum(v for v in values)
'''

MESSY_SOURCE = '''
def f(items, acc=[]):
    for i in range(len(items)):
        try:
            acc.append(items[i])
        except:
            pass
    return acc
'''


def _write(source: str) -> str:
    d = tempfile.mkdtemp(prefix="agon-quality-")
    with open(os.path.join(d, "main.py"), "w", encoding="utf-8") as fh:
        fh.write(source)
    return d


@pytest.mark.parametrize("key,name,factory", QUALITY_PLUGINS)
def test_plugin_returns_bounded_grade(key, name, factory):
    plugin = factory()
    path = _write(CLEAN_SOURCE)
    out = plugin.run(PluginInput(submission_path=path))
    assert 0.0 <= out.grade <= 100.0
    assert isinstance(out.pros, list) and isinstance(out.cons, list)
    assert out.pros or out.cons  # some evidence is always produced


@pytest.mark.parametrize("key,name,factory", QUALITY_PLUGINS)
def test_plugin_is_deterministic(key, name, factory):
    path = _write(CLEAN_SOURCE)
    g1 = factory().run(PluginInput(submission_path=path)).grade
    g2 = factory().run(PluginInput(submission_path=path)).grade
    assert g1 == g2


def test_clean_scores_higher_than_messy_overall():
    path_clean = _write(CLEAN_SOURCE)
    path_messy = _write(MESSY_SOURCE)
    for _key, _name, factory in QUALITY_PLUGINS:
        plugin = factory()
        clean = plugin.run(PluginInput(submission_path=path_clean)).grade
        messy = plugin.run(PluginInput(submission_path=path_messy)).grade
        assert clean >= messy, f"{plugin.key}: clean {clean} < messy {messy}"


def test_stdlib_idioms_detects_each_antipattern():
    from src.tests_plugins.quality.stdlib_idioms import factory as si_factory

    cases = {
        "bare except": "def g():\n    try:\n        pass\n    except:\n        pass\n",
        "mutable default": "def g(a=[]):\n    return a\n",
        "range(len)": "def g(x):\n    for i in range(len(x)):\n        print(x[i])\n",
    }
    for label, src in cases.items():
        path = _write(src)
        out = si_factory().run(PluginInput(submission_path=path))
        assert out.cons, f"expected an anti-pattern con for {label}"
