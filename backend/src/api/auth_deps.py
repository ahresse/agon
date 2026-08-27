"""Authentication and role authorization (T015, FR-014, FR-015).

MVP uses a simple signed session cookie carrying the user id. Password hashing
uses the stdlib (salted PBKDF2) to avoid extra dependencies.
"""
from __future__ import annotations

import hashlib
import hmac
import os

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db import get_session
from src.models import Role, User

_SECRET = os.environ.get("AGON_SECRET", "dev-insecure-secret").encode()
SESSION_COOKIE = "agon_session"


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, _ = stored.split("$", 1)
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(password, bytes.fromhex(salt_hex)), stored)


def sign_session(user_id: str) -> str:
    sig = hmac.new(_SECRET, user_id.encode(), hashlib.sha256).hexdigest()
    return f"{user_id}.{sig}"


def _parse_session(token: str) -> str | None:
    try:
        user_id, sig = token.rsplit(".", 1)
    except ValueError:
        return None
    expected = hmac.new(_SECRET, user_id.encode(), hashlib.sha256).hexdigest()
    return user_id if hmac.compare_digest(sig, expected) else None


def current_user(
    agon_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: Session = Depends(get_session),
) -> User:
    if not agon_session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    user_id = _parse_session(agon_session)
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown user")
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != Role.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin privileges required")
    return user
