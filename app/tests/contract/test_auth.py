"""Auth + role distinction contract test (T025, FR-014, FR-015)."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("AGON_USE_LOCAL_RUNNER", "1")
os.environ.setdefault("AGON_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("AGON_RUN_JOBS_INLINE", "1")

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402

from src.api.auth_deps import hash_password  # noqa: E402
from src.api.main import create_app  # noqa: E402
from src.db import SessionLocal, engine, init_db  # noqa: E402
from src.models import Base, Role, User  # noqa: E402


@pytest.fixture
def client():
    app = create_app()
    Base.metadata.drop_all(bind=engine)
    init_db()
    db = SessionLocal()
    db.add(User(username="admin", password_hash=hash_password("pw"), role=Role.ADMIN))
    db.add(User(username="rev", password_hash=hash_password("pw"), role=Role.REVIEWER))
    db.commit()
    db.close()
    return TestClient(app)


def _login(client, username):
    r = client.post("/auth/login", json={"username": username, "password": "pw"})
    assert r.status_code == 200
    return r.json()


def test_login_success_returns_role(client):
    body = _login(client, "admin")
    assert body["role"] == "ADMIN"
    body = _login(client, "rev")
    assert body["role"] == "REVIEWER"


def test_login_bad_credentials_rejected(client):
    r = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


def test_admin_route_allows_admin_denies_reviewer(client):
    # Reviewer is forbidden from admin user-management (403).
    _login(client, "rev")
    r = client.get("/admin/users")
    assert r.status_code == 403

    # Admin is allowed.
    _login(client, "admin")
    r = client.get("/admin/users")
    assert r.status_code == 200
    assert any(u["username"] == "admin" for u in r.json())


def test_unauthenticated_admin_route_rejected(client):
    fresh = TestClient(create_app())
    r = fresh.get("/admin/users")
    assert r.status_code == 401
