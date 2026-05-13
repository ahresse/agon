"""Unit tests for container utility helpers."""

import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from agon.assessments import AssessmentSpec
from agon.container_utils import container_run
from agon.container_utils import run_assessment_in_container


class ContainerRunTests(unittest.TestCase):
    """Tests for container_run and container-based assessment wrappers."""

    def test_container_run_executes_function_and_returns_stdout(self) -> None:
        """container_run should execute provided function and return stdout."""
        def sample() -> str:
            return "hello"

        with (
            patch(
                "agon.container_utils.uuid.uuid4",
                return_value=SimpleNamespace(hex="abcd1234efgh5678"),
            ),
            patch("agon.container_utils.wait_for_container") as mock_wait,
            patch("agon.container_utils.container_exec_result") as mock_run,
            patch("agon.container_utils.subprocess.run") as mock_subprocess_run,
        ):
            mock_subprocess_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="hello\n",
                stderr="",
            )

            result = container_run(sample)

            self.assertEqual(result, "hello\n")
            mock_wait.assert_called_once_with("agon-run-abcd1234", timeout_seconds=90)
            mock_run.assert_called_once()
            called_name, called_cmd = mock_run.call_args.args
            self.assertEqual(called_name, "agon-run-abcd1234")
            self.assertIn("python3 - <<'PY'", called_cmd)
            self.assertIn("_result = sample()", called_cmd)

            launch_call = mock_subprocess_run.call_args_list[0].args[0]
            delete_call = mock_subprocess_run.call_args_list[-1].args[0]
            self.assertEqual(
                launch_call,
                ["lxc", "launch", "ubuntu:24.04", "agon-run-abcd1234"],
            )
            self.assertEqual(delete_call, ["lxc", "delete", "--force", "agon-run-abcd1234"])

    def test_container_run_rejects_required_arguments(self) -> None:
        """container_run should reject functions requiring positional args."""
        def sample(arg: str) -> str:
            return arg

        with patch("agon.container_utils.subprocess.run") as mock_subprocess_run:
            with self.assertRaises(ValueError):
                container_run(sample)
            mock_subprocess_run.assert_not_called()

    def test_container_run_raises_when_container_execution_fails(self) -> None:
        """container_run should raise RuntimeError when command execution fails."""
        def sample() -> None:
            return None

        with (
            patch(
                "agon.container_utils.uuid.uuid4",
                return_value=SimpleNamespace(hex="abcd1234efgh5678"),
            ),
            patch("agon.container_utils.wait_for_container"),
            patch("agon.container_utils.container_exec_result") as mock_run,
            patch("agon.container_utils.subprocess.run") as mock_subprocess_run,
        ):
            mock_subprocess_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout="",
                stderr="boom",
            )

            with self.assertRaises(RuntimeError):
                container_run(sample)

            delete_call = mock_subprocess_run.call_args_list[-1].args[0]
            self.assertEqual(delete_call, ["lxc", "delete", "--force", "agon-run-abcd1234"])

    def test_run_assessment_in_container_installs_packages_and_runs_command(self) -> None:
        """Assessment wrapper should install deps and execute built command."""
        assessment = AssessmentSpec(
            name="demo",
            weight=1.0,
            command_builder=lambda target_path: f"demo-check {target_path}",
            evaluator=lambda execution: 12,
            required_debian_packages=("demo-package",),
        )

        with (
            patch("agon.container_utils.ensure_debian_package") as mock_install,
            patch("agon.container_utils.container_exec_result") as mock_exec,
        ):
            mock_exec.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="ok\n",
                stderr="",
            )

            result = run_assessment_in_container("box", assessment, "/tmp/project")

            self.assertEqual(result.grade, 12)
            mock_install.assert_called_once_with("box", "demo-package")
            mock_exec.assert_called_once_with("box", "demo-check /tmp/project")


if __name__ == "__main__":
    unittest.main()
