"""Reviews weights router (T053, FR-009, FR-010, FR-017): PUT /reviews/{id}/weights.

Applies per-review reviewer weight overrides, then recomputes the final grade
instantly from stored TestResults without re-running any test (FR-010, SC-003).
Rejects a configuration where no enabled test carries a positive effective weight
(FR-017). Overrides are scoped to the review and never affect other reviewers
(FR-009, SC-007).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.auth_deps import current_user
from src.api.review_detail import build_review_detail
from src.api.schemas import ReviewDetailOut, WeightOverrideRequest
from src.db import get_session
from src.models import Review, Test, TestResult, User, WeightConfiguration
from src.services.grading import (
    NoPositiveWeightError,
    ResultInput,
    effective_weight,
    weighted_mean,
)

router = APIRouter(tags=["reviews"])


@router.put("/reviews/{review_id}/weights", response_model=ReviewDetailOut)
def update_weights(
    review_id: str,
    payload: WeightOverrideRequest,
    db: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> ReviewDetailOut:
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    if review.reviewer_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your review")

    # Validate referenced tests exist and weights are non-negative.
    for ov in payload.overrides:
        if ov.weight < 0:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Weights must be >= 0")
        if not db.get(Test, ov.test_id):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown test {ov.test_id}")

    # Upsert per-review overrides (scoped to this review only).
    existing = {
        wc.test_id: wc
        for wc in db.query(WeightConfiguration)
        .filter(WeightConfiguration.review_id == review_id)
        .all()
    }
    for ov in payload.overrides:
        if ov.test_id in existing:
            existing[ov.test_id].weight = ov.weight
            db.add(existing[ov.test_id])
        else:
            db.add(
                WeightConfiguration(review_id=review_id, test_id=ov.test_id, weight=ov.weight)
            )
    db.flush()

    # Recompute from stored results only (no re-execution).
    results = db.query(TestResult).filter(TestResult.review_id == review_id).all()
    overrides = {
        wc.test_id: wc.weight
        for wc in db.query(WeightConfiguration)
        .filter(WeightConfiguration.review_id == review_id)
        .all()
    }
    result_inputs: list[ResultInput] = []
    for r in results:
        test = db.get(Test, r.test_id)
        eff = effective_weight(test.default_weight, overrides.get(r.test_id))
        result_inputs.append(ResultInput(test_id=r.test_id, grade=r.grade, weight=eff))

    try:
        review.final_grade = weighted_mean(result_inputs) if result_inputs else 0.0
    except NoPositiveWeightError:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "At least one enabled test must have a positive weight.",
        )

    db.add(review)
    db.commit()
    db.refresh(review)
    return build_review_detail(db, review)
