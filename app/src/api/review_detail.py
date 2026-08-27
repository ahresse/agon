"""Helpers to assemble review detail responses (FR-012)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.api.schemas import ReviewDetailOut, TestResultOut
from src.models import Review, Submission, Test, TestResult, WeightConfiguration
from src.services.grading import contribution, effective_weight


def build_review_detail(db: Session, review: Review) -> ReviewDetailOut:
    submission = db.get(Submission, review.submission_id)
    results = db.query(TestResult).filter(TestResult.review_id == review.id).all()
    overrides = {
        wc.test_id: wc.weight
        for wc in db.query(WeightConfiguration)
        .filter(WeightConfiguration.review_id == review.id)
        .all()
    }

    weighted = []
    for r in results:
        test = db.get(Test, r.test_id)
        eff = effective_weight(test.default_weight, overrides.get(r.test_id))
        weighted.append((r, test, eff))

    total_weight = sum(eff for _, _, eff in weighted)
    agg_pros: list[str] = []
    agg_cons: list[str] = []
    result_out: list[TestResultOut] = []
    for r, test, eff in weighted:
        from src.services.grading import ResultInput

        contrib = contribution(ResultInput(r.test_id, r.grade, eff), total_weight)
        result_out.append(
            TestResultOut(
                test_id=r.test_id,
                test_name=test.name,
                grade=r.grade,
                status=r.status,
                effective_weight=eff,
                contribution=round(contrib, 2),
                pros=r.pros,
                cons=r.cons,
            )
        )
        agg_pros.extend(r.pros)
        agg_cons.extend(r.cons)

    return ReviewDetailOut(
        id=review.id,
        submission_id=review.submission_id,
        reviewer_id=review.reviewer_id,
        status=review.status,
        final_grade=review.final_grade,
        candidate_label=submission.candidate_label if submission else "",
        created_at=review.created_at.isoformat(),
        results=result_out,
        pros=agg_pros,
        cons=agg_cons,
    )
