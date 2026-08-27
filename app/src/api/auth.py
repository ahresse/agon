"""Auth router (FR-015)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.api.auth_deps import SESSION_COOKIE, sign_session, verify_password
from src.api.schemas import LoginRequest, UserOut
from src.db import get_session
from src.models import User

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_session)) -> UserOut:
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    response.set_cookie(SESSION_COOKIE, sign_session(user.id), httponly=True, samesite="lax")
    return UserOut(id=user.id, username=user.username, role=user.role)
