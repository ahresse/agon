"""Unit tests for assessment command execution and grading."""

import shutil
import subprocess
import tarfile
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

from agon.assessments import ASSESSMENTS
from agon.assessments import MAX_GRADE
from agon.assessments import run_assessment


def local_command_runner(command: str) -> subprocess.CompletedProcess[str]:
    """Execute a shell command locally and return captured output."""
    return subprocess.run(
        ["bash", "-lc", command],
        check=False,
        text=True,
        capture_output=True,
    )


class AssessmentTests(unittest.TestCase):
    """Behavioral tests for the generic assessment runner."""

    def setUp(self) -> None:
        """Create a temporary workspace for each test."""
        self.tmp_path = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        """Remove the temporary workspace created during setUp."""
        shutil.rmtree(self.tmp_path)

    def _write_sample_file(self, name: str = "sample.py") -> Path:
        """Create a simple Python file and return its path."""
        file_path = self.tmp_path / name
        file_path.write_text("print('hello')\n", encoding="utf-8")
        return file_path

    def _create_tar_gz(self, archive_name: str) -> Path:
        """Create a gzipped tar archive containing one sample file."""
        sample = self._write_sample_file()
        archive_path = self.tmp_path / archive_name
        with tarfile.open(archive_path, "w:gz") as tf:
            tf.add(sample, arcname=sample.name)
        return archive_path

    def _create_zip(self, archive_name: str) -> Path:
        """Create a zip archive containing one sample file."""
        sample = self._write_sample_file()
        archive_path = self.tmp_path / archive_name
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.write(sample, arcname=sample.name)
        return archive_path

    def test_archive_format_valid_tar_gz_gets_max_grade(self) -> None:
        """A valid .tar.gz archive should receive the maximum grade."""
        archive_path = self._create_tar_gz("project.tar.gz")

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = run_assessment(
                ASSESSMENTS["archive-format"],
                str(archive_path),
                local_command_runner,
            )

        self.assertEqual(result.grade, MAX_GRADE)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(caught, [])

    def test_archive_format_disguised_zip_warns_and_scores_zero(self) -> None:
        """A renamed zip should fail archive validation and emit a warning."""
        zip_path = self._create_zip("project.zip")
        disguised_path = self.tmp_path / "project.tar.gz"
        zip_path.rename(disguised_path)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = run_assessment(
                ASSESSMENTS["archive-format"],
                str(disguised_path),
                local_command_runner,
            )

        self.assertEqual(result.grade, 0)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(caught)
        self.assertTrue(any(issubclass(item.category, RuntimeWarning) for item in caught))

    def test_all_assessments_are_registered(self) -> None:
        """Expected assessments are present and weights sum to 1."""
        self.assertEqual(
            tuple(ASSESSMENTS.keys()),
            ("archive-format", "pylint", "flake8"),
        )
        self.assertAlmostEqual(sum(spec.weight for spec in ASSESSMENTS.values()), 1.0)


if __name__ == "__main__":
    unittest.main()
