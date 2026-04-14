"""Command-line interface for agon."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import uuid
from pathlib import Path

from agon import __version__
from agon.assessments import ASSESSMENTS
from agon.assessments import MAX_GRADE
from agon.assessments import AssessmentResult
from agon.container_utils import delete_container
from agon.container_utils import extract_archive_in_container
from agon.container_utils import open_shell
from agon.container_utils import run_assessment_in_container
from agon.container_utils import show_directory_tree
from agon.container_utils import upload_archive_to_container
from agon.container_utils import wait_for_container

# Display formatting constants
BANNER_WIDTH_MAJOR = 72
BANNER_WIDTH_MINOR = 50

# LXD and container defaults
DEFAULT_LXD_IMAGE = "ubuntu:24.04"
DEFAULT_CONTAINER_USER = "ubuntu"
DEFAULT_CONTAINER_ARCHIVE_UPLOAD_PATH = f"/home/{DEFAULT_CONTAINER_USER}/"
DEFAULT_CONTAINER_EXTRACT_PATH = f"/home/{DEFAULT_CONTAINER_USER}/extracted/"


class OutputFormatter:
    """Centralized handler for terminal output formatting."""

    NAME_COL_WIDTH = 20
    WEIGHT_COL_WIDTH = 3

    @staticmethod
    def banner_major(text: str = "") -> str:
        """Format a major section banner."""
        line = "=" * BANNER_WIDTH_MAJOR
        if text:
            return f"\n{line}\n{text}\n{line}"
        return line

    @staticmethod
    def banner_minor() -> str:
        """Format a minor separator line."""
        return "-" * BANNER_WIDTH_MINOR

    @staticmethod
    def color_grade(grade: float) -> str:
        """Return an ANSI truecolor code for a grade on red-to-green gradient."""
        ratio = max(0.0, min(1.0, grade / MAX_GRADE if MAX_GRADE else 0.0))
        red = int(255 * (1.0 - ratio))
        green = int(255 * ratio)
        return f"\033[38;2;{red};{green};0m"

    @staticmethod
    def format_grade(grade: float) -> str:
        """Format a grade with color and text."""
        color = OutputFormatter.color_grade(grade)
        return f"{color}{grade:.2f}/{MAX_GRADE}\033[0m"

    @staticmethod
    def format_assessment_result(result: AssessmentResult) -> str:
        """Format a single assessment result line."""
        weight_pct = int(result.weight * 100)
        return (
            f"- {result.name:<{OutputFormatter.NAME_COL_WIDTH}} "
            f"[{weight_pct:>{OutputFormatter.WEIGHT_COL_WIDTH}}%]: "
            f"{OutputFormatter.format_grade(float(result.grade))} "
            f"(exit code: {result.returncode})"
        )


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="agon",
        description=(
            "Launch an ephemeral LXD container, upload an archive, extract it, "
            "and run code quality assessments."
        ),
    )
    parser.add_argument("archive", help="Path to the source archive to assess.")
    parser.add_argument(
        "--image",
        default=DEFAULT_LXD_IMAGE,
        help=f"LXD image alias to use (default: {DEFAULT_LXD_IMAGE}).",
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
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a shell command, capture output, and raise on failure."""
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def format_subprocess_error(exc: subprocess.CalledProcessError) -> str:
    """Format a CalledProcessError into a human-readable string."""
    command = exc.cmd if isinstance(exc.cmd, list) else [str(exc.cmd)]
    details = [
        f"command: {' '.join(str(part) for part in command)}",
        f"exit code: {exc.returncode}",
    ]
    stdout = (exc.stdout or "").strip()
    stderr = (exc.stderr or "").strip()
    if stdout:
        details.append(f"stdout:\n{stdout}")
    if stderr:
        details.append(f"stderr:\n{stderr}")
    if not stdout and not stderr:
        details.append("No stdout/stderr captured.")
    return "\n".join(details)


def validate_archive_and_env(archive_path: Path, parser: argparse.ArgumentParser) -> None:
    """Validate that archive exists and lxc is available."""
    if not archive_path.exists():
        parser.error(f"Archive not found: {archive_path}")
    if shutil.which("lxc") is None:
        raise RuntimeError("lxc command not found. Install and configure LXD first.")


def sanitize_name(raw_name: str) -> str:
    """Sanitize a string into a valid LXD container name component."""
    cleaned = re.sub(r"[^a-z0-9-]+", "-", raw_name.lower()).strip("-")
    return cleaned or "archive"


def generate_container_name(archive_path: Path) -> str:
    """Generate a unique container name from archive stem and UUID."""
    return f"agon-{sanitize_name(archive_path.stem)}-{uuid.uuid4().hex[:8]}"


def run_quality_assessments(
    container_name: str, extracted_path: str
) -> list[AssessmentResult]:
    """Run pylint and flake8 quality assessments inside the container."""
    return [
        run_assessment_in_container(container_name, ASSESSMENTS["pylint"], extracted_path),
        run_assessment_in_container(container_name, ASSESSMENTS["flake8"], extracted_path),
    ]


def display_assessment_results(results: list[AssessmentResult]) -> float:
    """Print weighted assessment results and return the total grade."""
    print("\nAssessment results:")
    weighted_sum = 0.0
    total_weight = 0.0
    for result in results:
        print(OutputFormatter.format_assessment_result(result))
        weighted_sum += result.grade * result.weight
        total_weight += result.weight

    total_grade = weighted_sum / total_weight if total_weight else 0.0
    print(f"\n{OutputFormatter.banner_minor()}")
    print(f"Total grade: {OutputFormatter.format_grade(total_grade)}")
    print(OutputFormatter.banner_minor())
    return total_grade


def main() -> None:
    """CLI entrypoint: orchestrate container lifecycle and assessments."""
    # Parse and validate inputs
    parser = build_parser()
    args = parser.parse_args()
    archive_path = Path(args.archive).expanduser().resolve()
    validate_archive_and_env(archive_path, parser)

    # Setup container lifecycle
    container_name = generate_container_name(archive_path)
    print(f"Launching LXD container {container_name} from {args.image}...")
    run_cmd(["lxc", "launch", args.image, container_name])

    keep_container = bool(args.keep_container)
    try:
        # Prepare archive for assessment
        wait_for_container(container_name)
        container_archive_path = upload_archive_to_container(
            container_name,
            archive_path,
            args.container_archive_upload_path,
        )

        # Run archive format assessment
        archive_result = run_assessment_in_container(
            container_name,
            ASSESSMENTS["archive-format"],
            container_archive_path,
        )

        # Extract and display archive contents
        extracted_path = extract_archive_in_container(
            container_name,
            container_archive_path,
            args.container_extract_path,
        )
        show_directory_tree(container_name, extracted_path)

        # Run quality assessments and display results
        print("Running quality assessments...")
        quality_results = run_quality_assessments(container_name, extracted_path)
        all_results = [archive_result] + quality_results
        display_assessment_results(all_results)

        # Open interactive shell
        open_shell(container_name, DEFAULT_CONTAINER_USER)
    except (subprocess.CalledProcessError, RuntimeError, TimeoutError, ValueError) as exc:
        if isinstance(exc, subprocess.CalledProcessError):
            raise SystemExit(f"Error:\n{format_subprocess_error(exc)}") from exc
        raise SystemExit(f"Error: {exc}") from exc
    finally:
        if keep_container:
            print(f"Container retained: {container_name}")
        else:
            print(f"Cleaning up container {container_name}...")
            delete_container(container_name)


if __name__ == "__main__":
    main()
