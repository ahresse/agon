"""Reviews router (FR-011, FR-012)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.auth_deps import current_user
from src.api.review_detail import build_review_detail
from src.api.schemas import ReviewDetailOut, ReviewSummaryOut
from src.db import get_session
from src.models import Review, Submission, User

router = APIRouter(tags=["reviews"])


@router.get("/reviews", response_model=list[ReviewSummaryOut])
def list_reviews(
    db: Session = Depends(get_session), user: User = Depends(current_user)
) -> list[ReviewSummaryOut]:
    reviews = (
        db.query(Review)
        .filter(Review.reviewer_id == user.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    out: list[ReviewSummaryOut] = []
    for r in reviews:
        submission = db.get(Submission, r.submission_id)
        out.append(
            ReviewSummaryOut(
                id=r.id,
                submission_id=r.submission_id,
                reviewer_id=r.reviewer_id,
                status=r.status,
                final_grade=r.final_grade,
                candidate_label=submission.candidate_label if submission else "",
                created_at=r.created_at.isoformat(),
            )
        )
    return out


@router.get("/reviews/{review_id}", response_model=ReviewDetailOut)
def get_review(
    review_id: str, db: Session = Depends(get_session), user: User = Depends(current_user)
) -> ReviewDetailOut:
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    return build_review_detail(db, review)
