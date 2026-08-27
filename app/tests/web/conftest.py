"""Shared fixtures for the server-rendered web interface tests (feature 005)."""
from __future__ import annotations

import io
import os
import zipfile

os.environ.setdefault("AGON_USE_LOCAL_RUNNER", "1")
os.environ.setdefault("AGON_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("AGON_RUN_JOBS_INLINE", "1")

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")
pytest.importorskip("jinja2")

from fastapi.testclient import TestClient  # noqa: E402

from src.api.auth_deps import hash_password  # noqa: E402
from src.api.main import create_app  # noqa: E402
from src.db import SessionLocal, engine, init_db  # noqa: E402
from src.models import Base, Role, Test, TestType, User  # noqa: E402
from src.tests_plugins.quality.builtin import QUALITY_PLUGINS  # noqa: E402


@pytest.fixture
def app():
    application = create_app()
    Base.metadata.drop_all(bind=engine)
    init_db()
    db = SessionLocal()
    db.add(User(username="reviewer", password_hash=hash_password("pw"), role=Role.REVIEWER))
    db.add(User(username="admin", password_hash=hash_password("pw"), role=Role.ADMIN))
    for key, name, _factory in QUALITY_PLUGINS:
        db.add(Test(key=key, name=name, type=TestType.METRIC, enabled=True, default_weight=1.0))
    db.commit()
    db.close()
    return application


@pytest.fixture
def client(app):
    return TestClient(app)


def login(client, username="reviewer", password="pw"):
    r = client.post(
        "/login", data={"username": username, "password": password}, follow_redirects=False
    )
    assert r.status_code == 303, r.text


def make_zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for n, c in files.items():
            zf.writestr(n, c)
    return buf.getvalue()


def upload(client, label="cand"):
    archive = make_zip({"main.py": "def f(a: int) -> int:\n    \"\"\"doc\"\"\"\n    return a + 1\n"})
    r = client.post(
        "/ui/upload",
        data={"candidate_label": label},
        files={"archive": ("s.zip", archive, "application/zip")},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text
    return r.headers["location"]  # /ui/reviews/{id}
