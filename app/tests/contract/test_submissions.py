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


def _upload(client, filename, data, label="cand", ctype="application/octet-stream"):
    return client.post(
        "/submissions",
        data={"candidate_label": label},
        files={"archive": (filename, data, ctype)},
    )


# --------------------------------------------------------------------------- #
# Accepted uploads (happy path across formats)
# --------------------------------------------------------------------------- #
class TestAcceptedUploads:
    """Valid Python archives in each supported format are accepted and graded."""

    def test_zip_returns_202_and_grade(self, client):
        _login(client)
        archive = _zip({"main.py": 'def f():\n    """doc"""\n    return 1\n'})
        r = _upload(client, "s.zip", archive, "cand-1", "application/zip")
        assert r.status_code == 202
        body = r.json()
        assert body["final_grade"] is not None
        detail = client.get(f"/reviews/{body['id']}").json()
        assert detail["results"]
        assert "pros" in detail and "cons" in detail

    def test_targz_returns_202_and_grade(self, client):
        _login(client)
        archive = _targz({"pkg/main.py": 'def f():\n    """doc"""\n    return 2\n'})
        r = _upload(client, "s.tar.gz", archive, "cand-targz", "application/gzip")
        assert r.status_code == 202, r.text
        assert r.json()["final_grade"] is not None

    def test_tgz_extension_accepted(self, client):
        _login(client)
        archive = _targz({"main.py": "x = 1\n"})
        r = _upload(client, "s.tgz", archive, "cand-tgz", "application/gzip")
        assert r.status_code == 202, r.text

    def test_plain_tar_accepted(self, client):
        _login(client)
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:") as tf:
            data = b"x = 1\n"
            info = tarfile.TarInfo("main.py")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        r = _upload(client, "s.tar", buf.getvalue(), "cand-tar", "application/x-tar")
        assert r.status_code == 202, r.text


# --------------------------------------------------------------------------- #
# Rejected uploads (unsupported / unusable / unsafe)
# --------------------------------------------------------------------------- #
class TestRejectedUploads:
    """Non-Python, corrupted, and unsafe archives are rejected with 422."""

    def test_malformed_gzip_returns_422(self, client):
        _login(client)
        r = _upload(client, "s.tar.gz", b"\x1f\x8b not a real gzip", "cand-bad", "application/gzip")
        assert r.status_code == 422

    def test_non_python_returns_422(self, client):
        _login(client)
        archive = _zip({"Main.java": "class Main {}"})
        r = _upload(client, "s.zip", archive, "cand-2", "application/zip")
        assert r.status_code == 422

    def test_path_traversal_returns_422(self, client):
        _login(client)
        archive = _zip({"../escape.py": "import os\n"})
        r = _upload(client, "evil.zip", archive, "cand-evil", "application/zip")
        assert r.status_code == 422

    def test_symlink_member_returns_422(self, client):
        _login(client)
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            info = tarfile.TarInfo("link.py")
            info.type = tarfile.SYMTYPE
            info.linkname = "/etc/passwd"
            tf.addfile(info)
        r = _upload(client, "link.tar.gz", buf.getvalue(), "cand-link", "application/gzip")
        assert r.status_code == 422


# --------------------------------------------------------------------------- #
# Authentication gate
# --------------------------------------------------------------------------- #
class TestAuthGate:
    """Upload requires an authenticated session."""

    def test_unauthenticated_upload_rejected(self, client):
        archive = _zip({"main.py": "x = 1\n"})
        r = _upload(client, "s.zip", archive, "cand-3", "application/zip")
        assert r.status_code == 401

