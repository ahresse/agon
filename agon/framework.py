"""Framework orchestrator."""

from __future__ import annotations

import logging
import warnings
from pathlib import Path

from agon.config import load_grading_config
from agon.container import ContainerManager
from agon.grading import aggregate_grades, evaluate_agent_based, evaluate_deterministic
from agon.models import ExecutionData, ExecutionStrategy, Summary, TestResult, TestType
from agon.packages import ensure_packages
from agon.presets import load_preset
from agon.setup import execute_setup_steps, infer_steps
from agon.summary import generate_summary

_LOGGER = logging.getLogger(__name__)


def run_atomic_tests(
    container_name: str,
    tests: list,
    extracted_path: str,
    setup_failed: bool = False,
    grade_scale_maximum: float = 20.0,
) -> tuple[list[TestResult], float]:
    """Execute a list of atomic tests inside the container and return results + final grade."""
    from agon.container import container_exec_result
    from agon.plugins import (
        MAX_AGENT_CONTEXT,
        run_custom_evaluator,
        run_regex_evaluator,
        run_script_evaluator,
    )

    results: list[TestResult] = []

    for test in tests:
        if setup_failed and test.execution_strategy == ExecutionStrategy.POST_EXTRACT:
            results.append(
                TestResult(
                    test_id=test.id,
                    name=test.name,
                    grade=0.0,
                    weight=test.weight,
                )
            )
            continue

        packages_ok = ensure_packages(container_name, test.required_debian_packages)
        if not packages_ok:
            results.append(
                TestResult(
                    test_id=test.id,
                    name=test.name,
                    grade=0.0,
                    weight=test.weight,
                )
            )
            continue

        if test.test_type == TestType.DETERMINISTIC:
            evaluator_type = (test.evaluator or {}).get("type") if test.evaluator else None

            if evaluator_type == "regex":
                grade = run_regex_evaluator(
                    container_name, extracted_path, test.evaluator, grade_scale_maximum
                )
                results.append(
                    TestResult(
                        test_id=test.id,
                        name=test.name,
                        grade=grade,
                        weight=test.weight,
                        exit_code=None,
                    )
                )
            elif evaluator_type == "script":
                grade = run_script_evaluator(
                    container_name, extracted_path, test, grade_scale_maximum
                )
                results.append(
                    TestResult(
                        test_id=test.id,
                        name=test.name,
                        grade=grade,
                        weight=test.weight,
                        exit_code=None,
                    )
                )
            elif evaluator_type == "custom":
                if not test.command:
                    _LOGGER.warning(
                        "Custom evaluator test %s has no command; returning 0.0",
                        test.id,
                    )
                    grade = 0.0
                else:
                    command = f"cd {extracted_path!r} && {test.command}"
                    proc = container_exec_result(container_name, command)
                    grade = run_custom_evaluator(
                        test.evaluator,
                        proc.returncode,
                        proc.stdout,
                        proc.stderr,
                        grade_scale_maximum,
                    )
                results.append(
                    TestResult(
                        test_id=test.id,
                        name=test.name,
                        grade=grade,
                        weight=test.weight,
                        exit_code=None,
                    )
                )
            else:
                # Default deterministic: run a shell command and grade on exit code
                command = f"cd {extracted_path!r} && {test.command}"
                proc = container_exec_result(container_name, command)
                data = ExecutionData(
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    returncode=proc.returncode,
                )
                default_evaluator = (
                    lambda e: grade_scale_maximum if e.returncode == 0 else 0.0
                )
                grade = evaluate_deterministic(data, default_evaluator, grade_scale_maximum)
                results.append(
                    TestResult(
                        test_id=test.id,
                        name=test.name,
                        grade=grade,
                        weight=test.weight,
                        exit_code=proc.returncode,
                    )
                )
        else:
            # Agent-based: gather source tree excerpt (capped at 128 KiB) and evaluate
            proc = container_exec_result(
                container_name,
                f"find {extracted_path!r} -type f -exec cat {{}} + | head -c {MAX_AGENT_CONTEXT}",
            )
            grade, reasoning = evaluate_agent_based(
                test.grading_prompt, proc.stdout, grade_scale_maximum
            )
            results.append(
                TestResult(
                    test_id=test.id,
                    name=test.name,
                    grade=grade,
                    weight=test.weight,
                    ai_reasoning=reasoning,
                )
            )

    final_grade = aggregate_grades(results)
    return results, final_grade


def run_framework(
    archive_path: str,
    preset: str = "python-project",
    image: str | None = None,
    container_archive_upload_path: str | None = None,
    container_extract_path: str | None = None,
    keep_container: bool = False,
    skip_setup: bool = False,
    plugin_paths: list[str] | None = None,
) -> Summary:
    """Run the full agon workflow and return a structured summary."""
    from agon.plugins import PluginRegistry

    grading_config = load_grading_config()
    registry = PluginRegistry()
    if plugin_paths:
        registry.load_plugins(plugin_paths)

    mgr = ContainerManager()
    container_name = mgr.launch(image or "ubuntu:24.04")

    try:
        archive = Path(archive_path)
        upload_dir = (container_archive_upload_path or "/home/ubuntu").rstrip("/") or "/"
        extract_dir = (container_extract_path or "/home/ubuntu/extracted").rstrip("/") or "/"

        remote_archive_path = f"{upload_dir}/{archive.name}"

        mgr.exec(container_name, f"mkdir -p '{upload_dir}'")
        mgr.upload_file(container_name, str(archive), remote_archive_path)

        mgr.exec(container_name, f"mkdir -p '{extract_dir}'")
        archive_name_lower = archive.name.lower()
        if archive_name_lower.endswith(".zip"):
            mgr.exec(container_name, f"unzip -q '{remote_archive_path}' -d '{extract_dir}'")
        elif archive_name_lower.endswith(".tar.gz"):
            mgr.exec(container_name, f"tar xf '{remote_archive_path}' -C '{extract_dir}'")
        else:
            raise ValueError("Archive must be a .zip or .tar.gz archive.")

        result = mgr.exec(container_name, f"ls -1 '{extract_dir}'")
        items = [item for item in result.stdout.splitlines() if item]
        if len(items) == 1:
            extracted_path = f"{extract_dir}/{items[0]}"
        else:
            extracted_path = extract_dir

        # Setup phase
        setup_outputs = []
        setup_failed = False
        if not skip_setup:
            steps = infer_steps(extracted_path)
            setup_outputs = execute_setup_steps(container_name, steps)
            if any(o.returncode != 0 for o in setup_outputs):
                setup_failed = True
                warnings.warn(
                    "Setup step failed. Dependent tests will receive zero grade.",
                    RuntimeWarning,
                )

        suite = load_preset(preset, registry=registry)
        test_results, final_grade = run_atomic_tests(
            container_name,
            suite.tests,
            extracted_path,
            setup_failed=setup_failed,
            grade_scale_maximum=grading_config.grade_scale_maximum,
        )

        summary = generate_summary(
            test_results,
            final_grade,
            setup_outputs=setup_outputs,
            grade_scale_maximum=grading_config.grade_scale_maximum,
        )
        return summary
    finally:
        if not keep_container:
            mgr.delete(container_name)
