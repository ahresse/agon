"""Command-line interface for agon."""

from __future__ import annotations

import argparse
from pathlib import Path

from agon import __version__
from agon.framework import run_framework

DEFAULT_LXD_IMAGE = "ubuntu:24.04"
DEFAULT_CONTAINER_ARCHIVE_UPLOAD_PATH = "/home/ubuntu/"
DEFAULT_CONTAINER_EXTRACT_PATH = "/home/ubuntu/extracted/"


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="agon",
        description=(
            "Launch an ephemeral container, upload an archive, extract it, "
            "and run code quality assessments."
        ),
    )
    parser.add_argument("archive", help="Path to the source archive to assess.")
    parser.add_argument(
        "--image",
        default=DEFAULT_LXD_IMAGE,
        help=f"image alias to use (default: {DEFAULT_LXD_IMAGE}).",
    )
    parser.add_argument(
        "--container-archive-upload-path",
        default=DEFAULT_CONTAINER_ARCHIVE_UPLOAD_PATH,
        help=(
            "Directory inside the container where the archive is uploaded "
            f"(default: {DEFAULT_CONTAINER_ARCHIVE_UPLOAD_PATH})."
        ),
    )
    parser.add_argument(
        "--container-extract-path",
        default=DEFAULT_CONTAINER_EXTRACT_PATH,
        help=(
            "Directory inside the container where the archive is extracted "
            f"(default: {DEFAULT_CONTAINER_EXTRACT_PATH})."
        ),
    )
    parser.add_argument(
        "--keep-container",
        action="store_true",
        help="Do not delete the container after execution.",
    )
    parser.add_argument(
        "--preset",
        default="python-project",
        help="Test-suite preset to use (default: python-project).",
    )
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip automatic setup phase.",
    )
    parser.add_argument(
        "--plugin",
        action="append",
        default=[],
        help=(
            "Path to a plugin file (.yaml) defining atomic tests and/or presets. "
            "Can be specified multiple times."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main() -> None:
    """CLI entrypoint: orchestrate container lifecycle and assessments."""
    parser = build_parser()
    args = parser.parse_args()

    summary = run_framework(
        archive_path=args.archive,
        preset=args.preset,
        image=args.image,
        container_archive_upload_path=args.container_archive_upload_path,
        container_extract_path=args.container_extract_path,
        keep_container=args.keep_container,
        skip_setup=args.skip_setup,
        plugin_paths=args.plugin or None,
    )

    scale = summary.grade_scale_maximum
    print(f"\nFinal grade: {summary.final_grade:.2f}/{scale:.0f}")
    for result in summary.results:
        print(f"  {result.name}: {result.grade:.2f}/{scale:.0f} (weight: {result.weight})")


if __name__ == "__main__":
    main()
