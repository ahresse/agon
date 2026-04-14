"""Tests that validate static quality metadata."""

import unittest

from agon.assessments import ASSESSMENTS


class QualityCheckTests(unittest.TestCase):
    """Sanity checks for assessment registry metadata."""

    def test_weight_percentages_are_positive(self) -> None:
        """Each assessment must define a strictly positive weight."""
        for assessment in ASSESSMENTS.values():
            self.assertGreater(assessment.weight, 0)


if __name__ == "__main__":
    unittest.main()
