"""Unit tests for REQ011, REQ012, REQ016 — CLI argument parsing and behaviour."""

from __future__ import annotations

import pytest

from agon.cli import build_parser


# ---------------------------------------------------------------------------
# Correctness review
#   - build_parser tests are pure and fast: no container mocking needed.
#   - They assert on the parsed Namespace object, verifying the CLI contract.
# ---------------------------------------------------------------------------


def test_cli_parses_archive_positional() -> None:
    """The CLI shall accept the source archive as a positional argument (REQ011)."""
    parser = build_parser()
    args = parser.parse_args(["project.tar.gz"])
    assert args.archive == "project.tar.gz"


def test_cli_parses_image_alias() -> None:
    """The CLI shall accept an optional --image alias (REQ011)."""
    parser = build_parser()
    args = parser.parse_args(["--image", "debian:12", "project.tar.gz"])
    assert args.image == "debian:12"


def test_cli_parses_container_paths() -> None:
    """The CLI shall accept optional container upload and extract paths (REQ011)."""
    parser = build_parser()
    args = parser.parse_args(
        [
            "--container-archive-upload-path",
            "/tmp/uploads",
            "--container-extract-path",
            "/tmp/extracted",
            "project.tar.gz",
        ]
    )
    assert args.container_archive_upload_path == "/tmp/uploads"
    assert args.container_extract_path == "/tmp/extracted"


def test_cli_parses_keep_container_flag() -> None:
    """The CLI shall accept --keep-container to retain the container (REQ011 + REQ012)."""
    parser = build_parser()
    args = parser.parse_args(["--keep-container", "project.tar.gz"])
    assert args.keep_container is True


def test_cli_parses_preset_name() -> None:
    """The CLI shall accept an optional --preset name (REQ011 + REQ009)."""
    parser = build_parser()
    args = parser.parse_args(["--preset", "python-project", "project.tar.gz"])
    assert args.preset == "python-project"


def test_cli_parses_skip_setup_flag() -> None:
    """The CLI shall accept --skip-setup to bypass automatic setup (REQ016)."""
    parser = build_parser()
    args = parser.parse_args(["--skip-setup", "project.tar.gz"])
    assert args.skip_setup is True



