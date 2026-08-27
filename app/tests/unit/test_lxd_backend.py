"""Unit tests for the LXD execution backend (Constitution II).

Mocks the ``lxc`` CLI so the launch→push→exec→parse→delete lifecycle and result
parsing are covered without a real LXD daemon.
"""
from __future__ import annotations

import json
import types

import pytest

from src.runners import lxd_backend
from src.runners.lxd_backend import LXDExecutionError, execute_in_lxd
from src.tests_plugins.registry import PluginInput


class _Plugin:
    key = "quality.lint_ruff"


def _fake_proc(returncode=0, stdout="", stderr=""):
    return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def test_successful_run_parses_result(monkeypatch, tmp_path):
    sub = tmp_path / "submission"
    sub.mkdir()
    (sub / "main.py").write_text("x = 1\n")

    calls = []

    def fake_run(args, capture_output, text, timeout):
        calls.append(args)
        # args = ["lxc", <subcommand>, ...]
        if args[1] == "exec" and "in_container" in " ".join(args):
            return _fake_proc(stdout=json.dumps({"grade": 88.0, "pros": ["ok"], "cons": []}))
        return _fake_proc()

    monkeypatch.setattr(lxd_backend.subprocess, "run", fake_run)

    out = execute_in_lxd("agon-python", _Plugin(), PluginInput(submission_path=str(sub)))
    assert out.grade == 88.0
    assert out.pros == ["ok"]
    # container was launched and deleted
    joined = [" ".join(c) for c in calls]
    assert any("lxc launch agon-python" in j for j in joined)
    assert any(j.startswith("lxc delete") for j in joined)
    # file push targets must be prefixed with the container name (name/path form)
    push_targets = [c[-1] for c in calls if len(c) > 2 and c[1] == "file" and c[2] == "push"]
    assert push_targets, "expected file push calls"
    assert all(t.startswith("agon-run-") for t in push_targets), push_targets


def test_nonzero_exec_raises(monkeypatch, tmp_path):
    sub = tmp_path / "s"
    sub.mkdir()

    def fake_run(args, capture_output, text, timeout):
        if args[1] == "exec" and "in_container" in " ".join(args):
            return _fake_proc(returncode=1, stderr="boom")
        return _fake_proc()

    monkeypatch.setattr(lxd_backend.subprocess, "run", fake_run)
    with pytest.raises(LXDExecutionError):
        execute_in_lxd("agon-python", _Plugin(), PluginInput(submission_path=str(sub)))


def test_container_error_result_raises(monkeypatch, tmp_path):
    sub = tmp_path / "s"
    sub.mkdir()

    def fake_run(args, capture_output, text, timeout):
        if args[1] == "exec" and "in_container" in " ".join(args):
            return _fake_proc(stdout=json.dumps({"error": "unknown plugin"}))
        return _fake_proc()

    monkeypatch.setattr(lxd_backend.subprocess, "run", fake_run)
    with pytest.raises(LXDExecutionError):
        execute_in_lxd("agon-python", _Plugin(), PluginInput(submission_path=str(sub)))


def test_delete_called_even_on_failure(monkeypatch, tmp_path):
    sub = tmp_path / "s"
    sub.mkdir()
    calls = []

    def fake_run(args, capture_output, text, timeout):
        calls.append(args)
        if args[1] == "launch":
            raise lxd_backend.subprocess.TimeoutExpired(cmd="lxc launch", timeout=1)
        return _fake_proc()

    monkeypatch.setattr(lxd_backend.subprocess, "run", fake_run)
    with pytest.raises(Exception):
        execute_in_lxd("agon-python", _Plugin(), PluginInput(submission_path=str(sub)))
    # delete attempted in finally
    assert any(c[1] == "delete" for c in calls)


def test_missing_image_gives_actionable_error(monkeypatch, tmp_path):
    sub = tmp_path / "s"
    sub.mkdir()

    def fake_run(args, capture_output, text, timeout):
        if args[1] == "launch":
            return _fake_proc(returncode=1, stderr='Error: Failed to find image "agon-python"')
        return _fake_proc()

    monkeypatch.setattr(lxd_backend.subprocess, "run", fake_run)
    with pytest.raises(LXDExecutionError, match="provision"):
        execute_in_lxd("agon-python", _Plugin(), PluginInput(submission_path=str(sub)))


def test_missing_lxc_binary_gives_actionable_error(monkeypatch, tmp_path):
    sub = tmp_path / "s"
    sub.mkdir()

    def fake_run(args, capture_output, text, timeout):
        raise FileNotFoundError("lxc")

    monkeypatch.setattr(lxd_backend.subprocess, "run", fake_run)
    with pytest.raises(LXDExecutionError, match="AGON_USE_LOCAL_RUNNER"):
        execute_in_lxd("agon-python", _Plugin(), PluginInput(submission_path=str(sub)))


def test_image_available_true_and_false(monkeypatch):
    def ok(args, capture_output, text, timeout):
        return _fake_proc(returncode=0)

    monkeypatch.setattr(lxd_backend.subprocess, "run", ok)
    assert lxd_backend.image_available("agon-python") is True

    def missing(args, capture_output, text, timeout):
        return _fake_proc(returncode=1)

    monkeypatch.setattr(lxd_backend.subprocess, "run", missing)
    assert lxd_backend.image_available("agon-python") is False
