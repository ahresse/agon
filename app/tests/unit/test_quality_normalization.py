"""Unit tests for quality-metric grade normalization (T073)."""
from __future__ import annotations

from src.tests_plugins.quality import common


def test_grade_from_penalty_bounds():
    assert common.grade_from_penalty(0.0) == 100.0
    assert common.grade_from_penalty(1000.0) == 0.0
    assert common.grade_from_penalty(40.0) == 60.0


def test_grade_from_ratio_empty_total_is_full():
    assert common.grade_from_ratio(0, 0) == 100.0


def test_grade_from_ratio_partial():
    assert common.grade_from_ratio(3, 4) == 75.0


def test_grade_from_ratio_clamped():
    assert common.grade_from_ratio(5, 4) == 100.0


def test_cap_clamps_range():
    assert common.cap(-5) == 0.0
    assert common.cap(150) == 100.0
    assert common.cap(42.5) == 42.5


def test_count_lines_and_collect_empty(tmp_path):
    # Directory with no python files.
    assert common.collect_python_files(str(tmp_path)) == []
    assert common.count_lines(str(tmp_path)) == 0
