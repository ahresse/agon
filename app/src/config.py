"""Application configuration (T017)."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.environ.get("AGON_DATABASE_URL", "sqlite:///./agon.db")
    upload_dir: str = os.environ.get("AGON_UPLOAD_DIR", "./uploads")
    # LXD image/profile used for containerized test execution (production).
    lxd_image_profile: str = os.environ.get("AGON_LXD_PROFILE", "agon-python")
    # When true, use the non-isolating local runner (CI/dev ONLY, never production).
    use_local_runner: bool = os.environ.get("AGON_USE_LOCAL_RUNNER", "0") == "1"
    # Abstract AI provider endpoint for AI-agent tests (US5).
    ai_provider_url: str | None = os.environ.get("AGON_AI_PROVIDER_URL")
    test_timeout_seconds: int = int(os.environ.get("AGON_TEST_TIMEOUT", "60"))
    # When true, review jobs are drained synchronously in-request instead of by
    # the background worker pool. Enabled in tests for deterministic assertions.
    run_jobs_inline: bool = os.environ.get("AGON_RUN_JOBS_INLINE", "0") == "1"
    # Number of background job-queue workers.
    job_workers: int = int(os.environ.get("AGON_JOB_WORKERS", "2"))
    # Live-progress poll interval (seconds) for the review page (feature 006).
    progress_poll_seconds: int = int(os.environ.get("AGON_PROGRESS_POLL_SECONDS", "2"))


settings = Settings()
