"""Server-rendered web interface routes (feature 005).

Delivers the whole reviewer/admin experience as HTML pages plus htmx fragments,
reusing the existing services, session auth, and read models. No project-authored
JavaScript: interactivity is server-driven and swapped in place by the vendored
htmx helper.
"""
from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from src.api.auth_deps import SESSION_COOKIE, hash_password, sign_session, verify_password
from src.api.review_detail import build_review_detail
from src.api.web_auth import (
    _RedirectException,
    admin_page_user,
    optional_user,
    page_user,
)
from src.api.web_render import render_fragment, render_page
from src.config import settings
from src.db import get_session
from src.models import Review, Role, Submission, Test, TestResult, User, WeightConfiguration
from src.services.archive_extraction import (
    UnsafeArchiveError,
    UnsupportedArchiveError,
    extract_archive,
)
from src.services.grading import (
    NoPositiveWeightError,
    ResultInput,
    effective_weight,
    weighted_mean,
)
from src.services.job_queue import queue
from src.services.language_detection import UnsupportedSubmissionError, detect_language
from src.services.review_progress import get_review_progress
from src.services.scheduler import schedule_review

router = APIRouter(tags=["web"])


# --------------------------------------------------------------------------- #
# Auth / root
# --------------------------------------------------------------------------- #
@router.get("/", response_class=HTMLResponse)
def root(user: User | None = Depends(optional_user)) -> RedirectResponse:
    if user is None:
        return RedirectResponse("/login", status_code=303)
    return RedirectResponse("/ui/reviews", status_code=303)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user: User | None = Depends(optional_user)) -> HTMLResponse:
    if user is not None:
        return RedirectResponse("/ui/reviews", status_code=303)
    return render_page(request, "login.html", {"current_user": None})


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session),
) -> HTMLResponse:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return render_page(
            request,
            "login.html",
            {"current_user": None, "error": "Invalid credentials"},
            status_code=401,
        )
    resp = RedirectResponse("/ui/reviews", status_code=303)
    resp.set_cookie(SESSION_COOKIE, sign_session(user.id), httponly=True, samesite="lax")
    return resp


@router.post("/logout")
def logout() -> RedirectResponse:
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(SESSION_COOKIE)
    return resp


# --------------------------------------------------------------------------- #
# Upload
# --------------------------------------------------------------------------- #
@router.get("/ui/upload", response_class=HTMLResponse)
def upload_page(request: Request, user: User = Depends(page_user)) -> HTMLResponse:
    return render_page(request, "upload.html", {"current_user": user})


@router.post("/ui/upload", response_class=HTMLResponse)
def upload_submit(
    request: Request,
    candidate_label: str = Form(...),
    archive: UploadFile = File(...),
    user: User = Depends(page_user),
    db: Session = Depends(get_session),
) -> HTMLResponse:
    os.makedirs(settings.upload_dir, exist_ok=True)
    extract_dir = tempfile.mkdtemp(prefix="agon-sub-", dir=settings.upload_dir)
    try:
        file_names = _extract_upload(archive, extract_dir)
    except UnsafeArchiveError as exc:
        return _upload_error(request, user, str(exc))
    except (UnsupportedArchiveError, OSError):
        return _upload_error(request, user, "Corrupted or unreadable archive")
    try:
        detection = detect_language(file_names)
    except UnsupportedSubmissionError as exc:
        return _upload_error(request, user, str(exc))

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
    schedule_review(db, review.id, extract_dir)
    if settings.run_jobs_inline:
        queue.run_pending_inline(db)
    return RedirectResponse(f"/ui/reviews/{review.id}", status_code=303)


def _upload_error(request: Request, user: User, message: str) -> HTMLResponse:
    return render_page(
        request, "upload.html", {"current_user": user, "error": message}, status_code=422
    )


def _extract_upload(archive: UploadFile, extract_dir: str) -> list[str]:
    tmp_path = os.path.join(extract_dir, "_upload.bin")
    with open(tmp_path, "wb") as fh:
        fh.write(archive.file.read())
    try:
        result = extract_archive(tmp_path, extract_dir)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    return result.file_names


# --------------------------------------------------------------------------- #
# History + review detail
# --------------------------------------------------------------------------- #
@router.get("/ui/reviews", response_class=HTMLResponse)
def history_page(
    request: Request, user: User = Depends(page_user), db: Session = Depends(get_session)
) -> HTMLResponse:
    reviews = (
        db.query(Review)
        .filter(Review.reviewer_id == user.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    rows = []
    for r in reviews:
        submission = db.get(Submission, r.submission_id)
        rows.append(
            {
                "id": r.id,
                "candidate_label": submission.candidate_label if submission else "",
                "created_at": r.created_at.isoformat(),
                "status": r.status.value,
                "final_grade": r.final_grade,
            }
        )
    return render_page(request, "history.html", {"current_user": user, "reviews": rows})


@router.get("/ui/reviews/{review_id}", response_class=HTMLResponse)
def review_detail_page(
    review_id: str,
    request: Request,
    user: User = Depends(page_user),
    db: Session = Depends(get_session),
) -> HTMLResponse:
    review = db.get(Review, review_id)
    if not review or review.reviewer_id != user.id:
        return render_page(
            request,
            "message.html",
            {"current_user": user, "message": "Review not found."},
            status_code=404,
        )
    detail = build_review_detail(db, review)
    progress = get_review_progress(db, review)
    return render_page(
        request,
        "review_detail.html",
        {
            "current_user": user,
            "review": detail,
            "review_id": review_id,
            "progress": progress,
            "poll_seconds": settings.progress_poll_seconds,
        },
    )


@router.get("/ui/reviews/{review_id}/progress", response_class=HTMLResponse)
def review_progress_fragment(
    review_id: str,
    request: Request,
    user: User = Depends(page_user),
    db: Session = Depends(get_session),
) -> HTMLResponse:
    """Live progress fragment: status + progress bar + ETA (feature 006).

    While running, the fragment self-polls every `poll_seconds`; once terminal it
    omits the poll trigger (polling stops) and renders the final grade + breakdown.
    Owner-only, reusing the review access rule.
    """
    review = db.get(Review, review_id)
    if not review or review.reviewer_id != user.id:
        return render_fragment(
            request, "fragments/message.html", {"message": "Review not found."}, status_code=404
        )
    progress = get_review_progress(db, review)
    context = {
        "review_id": review_id,
        "progress": progress,
        "poll_seconds": settings.progress_poll_seconds,
    }
    if progress.is_terminal:
        # Reveal the stored breakdown; no more polling.
        context["review"] = build_review_detail(db, review)
    return render_fragment(request, "fragments/progress.html", context)


# --------------------------------------------------------------------------- #
# Fragments: weight re-grade + evidence log (in-place, server-driven)
# --------------------------------------------------------------------------- #
@router.post("/ui/reviews/{review_id}/weights", response_class=HTMLResponse)
async def update_weights_fragment(
    review_id: str,
    request: Request,
    user: User = Depends(page_user),
    db: Session = Depends(get_session),
) -> HTMLResponse:
    review = db.get(Review, review_id)
    if not review or review.reviewer_id != user.id:
        return render_fragment(
            request, "fragments/message.html", {"message": "Review not found."}, status_code=404
        )

    # Read weight_<test_id> form fields.
    form = dict(await request.form())
    results = db.query(TestResult).filter(TestResult.review_id == review_id).all()
    existing = {
        wc.test_id: wc
        for wc in db.query(WeightConfiguration)
        .filter(WeightConfiguration.review_id == review_id)
        .all()
    }
    for r in results:
        raw = form.get(f"weight_{r.test_id}")
        if raw is None or raw == "":
            continue
        try:
            weight = float(raw)
        except ValueError:
            continue
        if weight < 0:
            weight = 0.0
        if r.test_id in existing:
            existing[r.test_id].weight = weight
            db.add(existing[r.test_id])
        else:
            db.add(WeightConfiguration(review_id=review_id, test_id=r.test_id, weight=weight))
    db.flush()

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
        db.refresh(review)
        detail = build_review_detail(db, review)
        return render_fragment(
            request,
            "fragments/grade.html",
            {
                "review": detail,
                "error": "At least one enabled test must have a positive weight.",
            },
            status_code=422,
        )

    db.add(review)
    db.commit()
    db.refresh(review)
    detail = build_review_detail(db, review)
    return render_fragment(request, "fragments/grade.html", {"review": detail})


@router.get("/ui/reviews/{review_id}/tests/{test_id}/log", response_class=HTMLResponse)
def evidence_log_fragment(
    review_id: str,
    test_id: str,
    request: Request,
    user: User = Depends(page_user),
    db: Session = Depends(get_session),
) -> HTMLResponse:
    review = db.get(Review, review_id)
    if not review or review.reviewer_id != user.id:
        return render_fragment(
            request, "fragments/message.html", {"message": "Review not found."}, status_code=404
        )
    result = (
        db.query(TestResult)
        .filter(TestResult.review_id == review_id, TestResult.test_id == test_id)
        .first()
    )
    # `log` is optional (feature 004); may be absent on this model version.
    log = getattr(result, "log", None) if result else None
    return render_fragment(request, "fragments/evidence_log.html", {"log": log})


# --------------------------------------------------------------------------- #
# Admin: tests + users
# --------------------------------------------------------------------------- #
@router.get("/ui/admin/tests", response_class=HTMLResponse)
def admin_tests_page(
    request: Request, admin: User = Depends(admin_page_user), db: Session = Depends(get_session)
) -> HTMLResponse:
    tests = db.query(Test).order_by(Test.name.asc()).all()
    return render_page(request, "admin_tests.html", {"current_user": admin, "tests": tests})


@router.post("/ui/admin/tests/{test_id}", response_class=HTMLResponse)
async def admin_tests_update(
    test_id: str,
    request: Request,
    admin: User = Depends(admin_page_user),
    db: Session = Depends(get_session),
) -> HTMLResponse:
    form = dict(await request.form())
    test = db.get(Test, test_id)
    if test:
        test.enabled = form.get("enabled") == "on"
        raw = form.get("default_weight")
        if raw not in (None, ""):
            try:
                w = float(raw)
                if w >= 0:
                    test.default_weight = w
            except ValueError:
                pass
        db.add(test)
        db.commit()
    return RedirectResponse("/ui/admin/tests", status_code=303)


@router.get("/ui/admin/users", response_class=HTMLResponse)
def admin_users_page(
    request: Request, admin: User = Depends(admin_page_user), db: Session = Depends(get_session)
) -> HTMLResponse:
    users = db.query(User).order_by(User.username.asc()).all()
    return render_page(request, "admin_users.html", {"current_user": admin, "users": users})


@router.post("/ui/admin/users", response_class=HTMLResponse)
def admin_users_create(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("REVIEWER"),
    admin: User = Depends(admin_page_user),
    db: Session = Depends(get_session),
) -> HTMLResponse:
    if not db.query(User).filter(User.username == username).first():
        db.add(
            User(
                username=username,
                password_hash=hash_password(password),
                role=Role(role) if role in Role.__members__ else Role.REVIEWER,
            )
        )
        db.commit()
    return RedirectResponse("/ui/admin/users", status_code=303)


@router.post("/ui/admin/users/{user_id}", response_class=HTMLResponse)
def admin_users_update_role(
    user_id: str,
    role: str = Form(...),
    admin: User = Depends(admin_page_user),
    db: Session = Depends(get_session),
) -> RedirectResponse:
    target = db.get(User, user_id)
    if target and role in Role.__members__:
        target.role = Role(role)
        db.add(target)
        db.commit()
    return RedirectResponse("/ui/admin/users", status_code=303)
