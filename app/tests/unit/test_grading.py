"""Unit tests for the grading service (FR-006, FR-007, FR-017)."""
import pytest

from src.services.grading import (
    NoPositiveWeightError,
    ResultInput,
    contribution,
    effective_weight,
    weighted_mean,
)


def test_weighted_mean_basic():
    results = [
        ResultInput("a", grade=80.0, weight=2.0),
        ResultInput("b", grade=60.0, weight=1.0),
    ]
    # (80*2 + 60*1) / 3 = 73.33...
    assert weighted_mean(results) == pytest.approx(73.3333, rel=1e-4)


def test_failed_test_counts_as_zero_but_retains_weight():
    results = [
        ResultInput("a", grade=100.0, weight=1.0),
        ResultInput("b", grade=0.0, weight=1.0),  # failed test contributes 0 (FR-007)
    ]
    assert weighted_mean(results) == 50.0


def test_all_zero_weight_raises(FR_017=True):
    results = [ResultInput("a", grade=90.0, weight=0.0)]
    with pytest.raises(NoPositiveWeightError):
        weighted_mean(results)


def test_effective_weight_override_precedence():
    assert effective_weight(default_weight=1.0, override=None) == 1.0
    assert effective_weight(default_weight=1.0, override=3.0) == 3.0


def test_contribution_sums_to_final_grade():
    results = [
        ResultInput("a", grade=80.0, weight=2.0),
        ResultInput("b", grade=60.0, weight=1.0),
    ]
    total = sum(r.weight for r in results)
    total_contrib = sum(contribution(r, total) for r in results)
    assert total_contrib == pytest.approx(weighted_mean(results), rel=1e-9)
