"""Submissions router (FR-001, FR-002, FR-003, FR-016)."""
from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.api.auth_deps import current_user
from src.api.schemas import ReviewOut
from src.config import settings
from src.db import get_session
from src.models import Review, Submission, User
from src.services.archive_extraction import (
    UnsafeArchiveError,
    UnsupportedArchiveError,
    extract_archive,
)
from src.services.job_queue import queue
from src.services.language_detection import UnsupportedSubmissionError, detect_language
from src.services.scheduler import schedule_review

router = APIRouter(tags=["submissions"])


@router.post("/submissions", response_model=ReviewOut, status_code=status.HTTP_202_ACCEPTED)
def create_submission(
    candidate_label: str = Form(...),
    archive: UploadFile = File(...),
    db: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> ReviewOut:
    os.makedirs(settings.upload_dir, exist_ok=True)
    extract_dir = tempfile.mkdtemp(prefix="agon-sub-", dir=settings.upload_dir)

    try:
        file_names = _extract_upload(archive, extract_dir)
    except UnsafeArchiveError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    except (UnsupportedArchiveError, OSError):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Corrupted or unreadable archive"
        )

    try:
        detection = detect_language(file_names)
    except UnsupportedSubmissionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))

    submission = Submission(
        candidate_label=candidate_label,
        detected_language=detection.language,
        storage_path=extract_dir,
        uploaded_by=user.id,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    review = Review(submission_id=submission.id, reviewer_id=user.id)
    db.add(review)
    db.commit()
    db.refresh(review)

    # Dispatch assessment asynchronously as a persisted job (FR-003). The reviewer
    # may leave the page and return for results. In tests/dev, jobs may be drained
    # synchronously for deterministic assertions.
    schedule_review(db, review.id, extract_dir)
    if settings.run_jobs_inline:
        queue.run_pending_inline(db)
        db.refresh(review)

    return ReviewOut(
        id=review.id,
        submission_id=review.submission_id,
        reviewer_id=review.reviewer_id,
        status=review.status,
        final_grade=review.final_grade,
    )


def _extract_upload(archive: UploadFile, extract_dir: str) -> list[str]:
    """Persist the uploaded archive and extract it safely (zip or tar.gz).

    Returns the relative paths of extracted regular files. Raises
    UnsupportedArchiveError / UnsafeArchiveError for invalid or unsafe input.
    """
    tmp_path = os.path.join(extract_dir, "_upload.bin")
    with open(tmp_path, "wb") as fh:
        fh.write(archive.file.read())
    try:
        result = extract_archive(tmp_path, extract_dir)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    return result.file_names
