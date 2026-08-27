"""Model package.

Only dependency-free enums are exported eagerly. ORM models (which require
SQLAlchemy) are imported lazily via ``__getattr__`` so that pure-logic modules
and their tests can import ``src.models.enums`` without SQLAlchemy installed.
"""
from .enums import ResultStatus, ReviewStatus, Role, TestType
from .enums import JobStatus

__all__ = [
    "Base",
    "Role",
    "TestType",
    "ReviewStatus",
    "ResultStatus",
    "JobStatus",
    "User",
    "Test",
    "Submission",
    "Review",
    "TestResult",
    "WeightConfiguration",
    "Job",
]

_ORM_EXPORTS = {
    "Base": ("base", "Base"),
    "User": ("user", "User"),
    "Test": ("test", "Test"),
    "Submission": ("submission", "Submission"),
    "Review": ("review", "Review"),
    "TestResult": ("test_result", "TestResult"),
    "WeightConfiguration": ("weight_configuration", "WeightConfiguration"),
    "Job": ("job", "Job"),
}


def __getattr__(name: str):
    if name in _ORM_EXPORTS:
        module_name, attr = _ORM_EXPORTS[name]
        import importlib

        module = importlib.import_module(f"{__name__}.{module_name}")
        return getattr(module, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
