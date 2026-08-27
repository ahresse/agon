"""Page-level authentication for the server-rendered web interface (feature 005).

Unlike the JSON API (which raises 401/403), page requests redirect unauthenticated
users to the login page and deny non-admins access to admin pages. Reuses the
existing signed-session mechanism (auth_deps).
"""
from __future__ import annotations

from fastapi import Cookie, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from src.api.auth_deps import SESSION_COOKIE, _parse_session
from src.db import get_session
from src.models import Role, User


class _RedirectException(Exception):
    """Internal signal carrying a redirect/response to return from a page route."""

    def __init__(self, response: RedirectResponse) -> None:
        self.response = response


def optional_user(
    agon_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: Session = Depends(get_session),
) -> User | None:
    """Return the signed-in user, or None (does not raise)."""
    if not agon_session:
        return None
    user_id = _parse_session(agon_session)
    if not user_id:
        return None
    return db.get(User, user_id)


def page_user(user: User | None = Depends(optional_user)) -> User:
    """Require a signed-in user for a page; redirect to /login otherwise."""
    if user is None:
        raise _RedirectException(RedirectResponse("/login", status_code=303))
    return user


def admin_page_user(user: User | None = Depends(optional_user)) -> User:
    """Require an admin for a page; redirect non-users to login, deny reviewers."""
    if user is None:
        raise _RedirectException(RedirectResponse("/login", status_code=303))
    if user.role != Role.ADMIN:
        raise _RedirectException(RedirectResponse("/ui/reviews", status_code=303))
    return user
