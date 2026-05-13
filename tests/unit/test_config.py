"""Unit tests for REQ030 and REQ031 — grading configuration file."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from agon.config import (
    ConfigLoadError,
    GradingConfig,
    DEFAULT_GRADE_SCALE_MAXIMUM,
    MAX_ALLOWED_GRADE_SCALE_MAXIMUM,
    MAX_CONFIG_FILE_SIZE,
    load_grading_config,
)


def test_load_grading_config_defaults_when_file_missing(tmp_path: Path, monkeypatch) -> None:
    """When no .agon file exists, load_grading_config shall default to 20.0 (REQ031)."""
    monkeypatch.chdir(tmp_path)
    config = load_grading_config()
    assert config.grade_scale_maximum == DEFAULT_GRADE_SCALE_MAXIMUM


def test_load_grading_config_reads_present_value(tmp_path: Path, monkeypatch) -> None:
    """When .agon contains grade_scale_maximum, it shall be parsed and returned (REQ031)."""
    monkeypatch.chdir(tmp_path)
    config_file = tmp_path / ".agon"
    config_file.write_text("grade_scale_maximum: 100\n", encoding="utf-8")
    config = load_grading_config()
    assert config.grade_scale_maximum == 100.0


def test_load_grading_config_ignores_unknown_keys(tmp_path: Path, monkeypatch) -> None:
    """Unknown keys in .agon shall be ignored."""
    monkeypatch.chdir(tmp_path)
    config_file = tmp_path / ".agon"
    config_file.write_text("grade_scale_maximum: 50\nsome_other_key: true\n", encoding="utf-8")
    config = load_grading_config()
    assert config.grade_scale_maximum == 50.0


def test_load_grading_config_rejects_missing_key(tmp_path: Path, monkeypatch) -> None:
    """When the file exists but lacks grade_scale_maximum, default to 20.0."""
    monkeypatch.chdir(tmp_path)
    config_file = tmp_path / ".agon"
    config_file.write_text("other: value\n", encoding="utf-8")
    config = load_grading_config()
    assert config.grade_scale_maximum == DEFAULT_GRADE_SCALE_MAXIMUM


def test_load_grading_config_rejects_non_numeric_value(tmp_path: Path, monkeypatch) -> None:
    """A non-numeric grade_scale_maximum shall raise ConfigLoadError (REQ031)."""
    monkeypatch.chdir(tmp_path)
    config_file = tmp_path / ".agon"
    config_file.write_text("grade_scale_maximum: not_a_number\n", encoding="utf-8")
    with pytest.raises(ConfigLoadError):
        load_grading_config()


def test_load_grading_config_rejects_negative_value(tmp_path: Path, monkeypatch) -> None:
    """A negative grade_scale_maximum shall raise ConfigLoadError (REQ031)."""
    monkeypatch.chdir(tmp_path)
    config_file = tmp_path / ".agon"
    config_file.write_text("grade_scale_maximum: -5\n", encoding="utf-8")
    with pytest.raises(ConfigLoadError):
        load_grading_config()


def test_load_grading_config_rejects_zero_value(tmp_path: Path, monkeypatch) -> None:
    """A zero grade_scale_maximum shall raise ConfigLoadError (REQ031)."""
    monkeypatch.chdir(tmp_path)
    config_file = tmp_path / ".agon"
    config_file.write_text("grade_scale_maximum: 0\n", encoding="utf-8")
    with pytest.raises(ConfigLoadError):
        load_grading_config()


def test_load_grading_config_rejects_nan(tmp_path: Path, monkeypatch) -> None:
    """A NaN grade_scale_maximum shall raise ConfigLoadError (REQ031)."""
    monkeypatch.chdir(tmp_path)
    config_file = tmp_path / ".agon"
    config_file.write_text("grade_scale_maximum: .nan\n", encoding="utf-8")
    with pytest.raises(ConfigLoadError):
        load_grading_config()


def test_load_grading_config_rejects_infinite(tmp_path: Path, monkeypatch) -> None:
    """An infinite grade_scale_maximum shall raise ConfigLoadError (REQ031)."""
    monkeypatch.chdir(tmp_path)
    config_file = tmp_path / ".agon"
    config_file.write_text("grade_scale_maximum: .inf\n", encoding="utf-8")
    with pytest.raises(ConfigLoadError):
        load_grading_config()


def test_load_grading_config_rejects_too_large_value(tmp_path: Path, monkeypatch) -> None:
    """A grade_scale_maximum exceeding 10000 shall raise ConfigLoadError (REQ031)."""
    monkeypatch.chdir(tmp_path)
    config_file = tmp_path / ".agon"
    config_file.write_text(f"grade_scale_maximum: {MAX_ALLOWED_GRADE_SCALE_MAXIMUM + 1}\n", encoding="utf-8")
    with pytest.raises(ConfigLoadError):
        load_grading_config()


def test_load_grading_config_rejects_oversized_file(tmp_path: Path, monkeypatch) -> None:
    """A .agon file larger than 128 KiB shall raise ConfigLoadError (REQ031)."""
    monkeypatch.chdir(tmp_path)
    config_file = tmp_path / ".agon"
    config_file.write_text("x" * (MAX_CONFIG_FILE_SIZE + 1), encoding="utf-8")
    with pytest.raises(ConfigLoadError):
        load_grading_config()


def test_load_grading_config_explicit_path(tmp_path: Path, monkeypatch) -> None:
    """An explicit path shall be honoured."""
    monkeypatch.chdir(tmp_path)
    config_file = tmp_path / "custom.agon"
    config_file.write_text("grade_scale_maximum: 42\n", encoding="utf-8")
    config = load_grading_config(config_file)
    assert config.grade_scale_maximum == 42.0


def test_load_grading_config_path_traversal_rejection(tmp_path: Path, monkeypatch) -> None:
    """Paths outside the working directory shall be rejected (REQ031)."""
    monkeypatch.chdir(tmp_path)
    outside = tmp_path.parent / "outside.agon"
    outside.write_text("grade_scale_maximum: 10\n", encoding="utf-8")
    with pytest.raises(ConfigLoadError):
        load_grading_config(outside)
