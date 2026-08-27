"""Shared helpers for HTTP-layer tests.

Provides a configured TestClient app plus zip/login helpers. Import-guarded so
tests skip cleanly when FastAPI/SQLAlchemy are unavailable.
"""
from __future__ import annotations

import io
import os
import zipfile

os.environ.setdefault("AGON_USE_LOCAL_RUNNER", "1")
os.environ.setdefault("AGON_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("AGON_RUN_JOBS_INLINE", "1")


def make_zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def fresh_app_client(users: dict[str, str], seed_tests: bool = True):
    """Create an app + client with a clean DB, seeded users (username->role) and
    the built-in quality tests. Returns (client, created_user_ids)."""
    from fastapi.testclient import TestClient

    from src.api.auth_deps import hash_password
    from src.api.main import create_app
    from src.db import SessionLocal, engine, init_db
    from src.models import Base, Role, Test, TestType, User
    from src.tests_plugins.quality.builtin import QUALITY_PLUGINS

    app = create_app()
    Base.metadata.drop_all(bind=engine)
    init_db()
    db = SessionLocal()
    ids: dict[str, str] = {}
    for username, role in users.items():
        u = User(username=username, password_hash=hash_password("pw"), role=Role(role))
        db.add(u)
        db.flush()
        ids[username] = u.id
    if seed_tests:
        for key, name, _factory in QUALITY_PLUGINS:
            db.add(
                Test(
                    key=key,
                    name=name,
                    type=TestType.METRIC,
                    enabled=True,
                    default_weight=1.0,
                )
            )
    db.commit()
    db.close()
    return TestClient(app), ids


def login(client, username: str, password: str = "pw") -> None:
    r = client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text


def upload_python(client, label: str = "cand") -> dict:
    archive = make_zip({"main.py": 'def f(a: int) -> int:\n    """doc"""\n    return a + 1\n'})
    r = client.post(
        "/submissions",
        data={"candidate_label": label},
        files={"archive": ("s.zip", archive, "application/zip")},
    )
    assert r.status_code == 202, r.text
    return r.json()
