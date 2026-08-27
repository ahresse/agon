"""Reviews detail router (T043, FR-012): GET /reviews/{id}.

Returns the structured per-test breakdown (grade, effective weight, contribution)
plus aggregated pros/cons. The detail-assembly helper lives in review_detail.py.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.auth_deps import current_user
from src.api.review_detail import build_review_detail
from src.api.schemas import ReviewDetailOut
from src.db import get_session
from src.models import Review, User

router = APIRouter(tags=["reviews"])


@router.get("/reviews/{review_id}", response_model=ReviewDetailOut)
def get_review(
    review_id: str, db: Session = Depends(get_session), user: User = Depends(current_user)
) -> ReviewDetailOut:
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    return build_review_detail(db, review)
