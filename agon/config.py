"""Grading configuration file loader.

The ``.agon`` file at the working-directory root controls assessment
parameters such as the grade scale maximum (REQ030, REQ031).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_LOGGER = logging.getLogger(__name__)

DEFAULT_GRADE_SCALE_MAXIMUM = 20.0
MAX_CONFIG_FILE_SIZE = 128 * 1024  # 128 KiB (REQ031 guardrail)
MAX_ALLOWED_GRADE_SCALE_MAXIMUM = 10000.0


@dataclass(frozen=True)
class GradingConfig:
    """Runtime grading parameters."""

    grade_scale_maximum: float = DEFAULT_GRADE_SCALE_MAXIMUM


class ConfigLoadError(Exception):
    """Raised when the grading configuration file cannot be loaded or validated."""


def load_grading_config(path: Path | str | None = None) -> GradingConfig:
    """Load and validate the grading configuration file.

    Parameters
    ----------
    path:
        Explicit path to the configuration file.  When ``None``, the file
        ``.agon`` in the current working directory is used.

    Returns
    -------
    GradingConfig:
        Parsed and validated configuration object.

    Raises
    ------
    ConfigLoadError:
        If the file is unreadable, malformed, or contains an invalid
        ``grade_scale_maximum``.
    """
    if path is None:
        path = Path.cwd() / ".agon"
    else:
        path = Path(path)

    # Path traversal guardrail (REQ031)
    resolved = path.resolve()
    cwd = Path.cwd().resolve()
    try:
        resolved.relative_to(cwd)
    except ValueError:
        raise ConfigLoadError(
            f"Configuration file must reside within the working directory: {resolved}"
        ) from None

    if not path.exists():
        _LOGGER.debug("No grading configuration file found at %s; using defaults", path)
        return GradingConfig()

    size = path.stat().st_size
    if size > MAX_CONFIG_FILE_SIZE:
        raise ConfigLoadError(
            f"Configuration file exceeds size limit ({MAX_CONFIG_FILE_SIZE} bytes): {size}"
        )

    try:
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except Exception as exc:
        raise ConfigLoadError(f"Failed to parse configuration file: {exc}") from exc

    if not isinstance(data, dict):
        data = {}

    raw_max = data.get("grade_scale_maximum", DEFAULT_GRADE_SCALE_MAXIMUM)
    try:
        grade_scale_maximum = float(raw_max)
    except (ValueError, TypeError) as exc:
        raise ConfigLoadError(
            f"Invalid grade_scale_maximum value: {raw_max!r}"
        ) from exc

    if not math.isfinite(grade_scale_maximum) or grade_scale_maximum <= 0:
        raise ConfigLoadError(
            f"grade_scale_maximum must be a positive finite number, got {grade_scale_maximum}"
        )
    if grade_scale_maximum > MAX_ALLOWED_GRADE_SCALE_MAXIMUM:
        raise ConfigLoadError(
            f"grade_scale_maximum exceeds maximum allowed value "
            f"{MAX_ALLOWED_GRADE_SCALE_MAXIMUM}: {grade_scale_maximum}"
        )

    return GradingConfig(grade_scale_maximum=grade_scale_maximum)
