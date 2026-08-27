"""Pydantic response/request schemas mirroring contracts/openapi.yaml."""
from __future__ import annotations

from pydantic import BaseModel

from src.models.enums import ResultStatus, ReviewStatus, Role, TestType


class LoginRequest(BaseModel):
    username: str
    password: str


class WeightOverride(BaseModel):
    test_id: str
    weight: float


class WeightOverrideRequest(BaseModel):
    overrides: list[WeightOverride]


class TestConfigUpdate(BaseModel):
    enabled: bool | None = None
    default_weight: float | None = None


class UserCreate(BaseModel):
    username: str
    password: str
    role: Role = Role.REVIEWER


class UserRoleUpdate(BaseModel):
    role: Role


class UserOut(BaseModel):
    id: str
    username: str
    role: Role


class TestOut(BaseModel):
    id: str
    key: str
    name: str
    type: TestType
    theme: str | None = None
    enabled: bool
    default_weight: float


class ReviewOut(BaseModel):
    id: str
    submission_id: str
    reviewer_id: str
    status: ReviewStatus
    final_grade: float | None = None


class ReviewSummaryOut(ReviewOut):
    candidate_label: str
    created_at: str


class TestResultOut(BaseModel):
    test_id: str
    test_name: str
    grade: float
    status: ResultStatus
    effective_weight: float
    contribution: float
    pros: list[str]
    cons: list[str]


class ReviewDetailOut(ReviewSummaryOut):
    results: list[TestResultOut]
    pros: list[str]
    cons: list[str]
