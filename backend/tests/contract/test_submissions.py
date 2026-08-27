"""Contract test for POST /submissions and GET /reviews/{id} (US1).

Skipped automatically when FastAPI/SQLAlchemy are not installed (e.g. minimal CI);
runs fully in a provisioned environment. Uses the non-isolating local runner via
AGON_USE_LOCAL_RUNNER so no LXD daemon is required for the test.
"""
from __future__ import annotations

import io
import os
import tarfile
import zipfile

import pytest

os.environ.setdefault("AGON_USE_LOCAL_RUNNER", "1")
os.environ.setdefault("AGON_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("AGON_RUN_JOBS_INLINE", "1")

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402

from src.api.auth_deps import hash_password  # noqa: E402
from src.api.main import create_app  # noqa: E402
from src.db import SessionLocal, engine, init_db  # noqa: E402
from src.models import Base, Role, Test, TestType, User  # noqa: E402
from src.tests_plugins.metric_example import KEY as METRIC_KEY  # noqa: E402


@pytest.fixture
def client():
    app = create_app()
    Base.metadata.drop_all(bind=engine)
    init_db()
    db = SessionLocal()
    db.add(User(username="reviewer", password_hash=hash_password("pw"), role=Role.REVIEWER))
    db.add(
        Test(key=METRIC_KEY, name="Readability", type=TestType.METRIC, enabled=True, default_weight=1.0)
    )
    db.commit()
    db.close()
    return TestClient(app)


def _zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def _targz(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, content in files.items():
            data = content.encode()
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _login(client):
    r = client.post("/auth/login", json={"username": "reviewer", "password": "pw"})
    assert r.status_code == 200


def test_upload_python_returns_202_and_grade(client):
    _login(client)
    archive = _zip({"main.py": 'def f():\n    """doc"""\n    return 1\n'})
    r = client.post(
        "/submissions",
        data={"candidate_label": "cand-1"},
        files={"archive": ("s.zip", archive, "application/zip")},
    )
    assert r.status_code == 202
    body = r.json()
    assert body["final_grade"] is not None
    detail = client.get(f"/reviews/{body['id']}").json()
    assert detail["results"]
    assert "pros" in detail and "cons" in detail


def test_upload_targz_returns_202_and_grade(client):
    _login(client)
    archive = _targz({"pkg/main.py": 'def f():\n    """doc"""\n    return 2\n'})
    r = client.post(
        "/submissions",
        data={"candidate_label": "cand-targz"},
        files={"archive": ("s.tar.gz", archive, "application/gzip")},
    )
    assert r.status_code == 202, r.text
    assert r.json()["final_grade"] is not None


def test_upload_tgz_extension_accepted(client):
    _login(client)
    archive = _targz({"main.py": "x = 1\n"})
    r = client.post(
        "/submissions",
        data={"candidate_label": "cand-tgz"},
        files={"archive": ("s.tgz", archive, "application/gzip")},
    )
    assert r.status_code == 202, r.text


def test_upload_malformed_gzip_returns_422(client):
    _login(client)
    r = client.post(
        "/submissions",
        data={"candidate_label": "cand-bad"},
        files={"archive": ("s.tar.gz", b"\x1f\x8b not a real gzip", "application/gzip")},
    )
    assert r.status_code == 422


def test_upload_non_python_returns_422(client):
    _login(client)
    archive = _zip({"Main.java": "class Main {}"})
    r = client.post(
        "/submissions",
        data={"candidate_label": "cand-2"},
        files={"archive": ("s.zip", archive, "application/zip")},
    )
    assert r.status_code == 422


def test_unauthenticated_upload_rejected(client):
    archive = _zip({"main.py": "x = 1\n"})
    r = client.post(
        "/submissions",
        data={"candidate_label": "cand-3"},
        files={"archive": ("s.zip", archive, "application/zip")},
    )
    assert r.status_code == 401
