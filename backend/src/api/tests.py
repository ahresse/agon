"""Tests configuration router (T059, FR-008, FR-014).

GET /tests lists the configured tests (any authenticated user). Admin-only
PUT /admin/tests/{id} enables/disables a test and sets its global default weight.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.auth_deps import current_user, require_admin
from src.api.schemas import TestConfigUpdate, TestOut
from src.db import get_session
from src.models import Test, User

router = APIRouter(tags=["tests"])


@router.get("/tests", response_model=list[TestOut])
def list_tests(
    db: Session = Depends(get_session), user: User = Depends(current_user)
) -> list[TestOut]:
    tests = db.query(Test).order_by(Test.name.asc()).all()
    return [
        TestOut(
            id=t.id,
            key=t.key,
            name=t.name,
            type=t.type,
            theme=t.theme,
            enabled=t.enabled,
            default_weight=t.default_weight,
        )
        for t in tests
    ]


@router.put("/admin/tests/{test_id}", response_model=TestOut)
def update_test(
    test_id: str,
    payload: TestConfigUpdate,
    db: Session = Depends(get_session),
    admin: User = Depends(require_admin),
) -> TestOut:
    test = db.get(Test, test_id)
    if not test:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test not found")
    if payload.enabled is not None:
        test.enabled = payload.enabled
    if payload.default_weight is not None:
        if payload.default_weight < 0:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Weight must be >= 0")
        test.default_weight = payload.default_weight
    db.add(test)
    db.commit()
    db.refresh(test)
    return TestOut(
        id=test.id,
        key=test.key,
        name=test.name,
        type=test.type,
        theme=test.theme,
        enabled=test.enabled,
        default_weight=test.default_weight,
    )
