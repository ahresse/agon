"""US3 admin config tests (T056-T058, FR-008, FR-014)."""
from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from tests.http_helpers import fresh_app_client, login, upload_python  # noqa: E402


def test_admin_updates_default_weight_and_reviewer_forbidden():
    client, _ = fresh_app_client({"admin": "ADMIN", "rev": "REVIEWER"})
    login(client, "admin")
    test = client.get("/tests").json()[0]

    r = client.put(f"/admin/tests/{test['id']}", json={"default_weight": 3.0})
    assert r.status_code == 200
    assert r.json()["default_weight"] == 3.0

    login(client, "rev")
    r = client.put(f"/admin/tests/{test['id']}", json={"default_weight": 7.0})
    assert r.status_code == 403


def test_disabled_test_excluded_from_new_assessment():
    client, _ = fresh_app_client({"admin": "ADMIN", "rev": "REVIEWER"})
    login(client, "admin")
    tests = client.get("/tests").json()
    disabled = tests[0]
    r = client.put(f"/admin/tests/{disabled['id']}", json={"enabled": False})
    assert r.status_code == 200

    login(client, "rev")
    review = upload_python(client)
    detail = client.get(f"/reviews/{review['id']}").json()
    graded_ids = {res["test_id"] for res in detail["results"]}
    assert disabled["id"] not in graded_ids


def test_admin_user_management_crud_and_role_guard():
    client, _ = fresh_app_client({"admin": "ADMIN", "rev": "REVIEWER"})
    # Reviewer forbidden.
    login(client, "rev")
    assert client.post("/admin/users", json={"username": "x", "password": "p"}).status_code == 403

    # Admin can create and promote.
    login(client, "admin")
    r = client.post("/admin/users", json={"username": "newbie", "password": "p"})
    assert r.status_code == 201
    uid = r.json()["id"]
    assert r.json()["role"] == "REVIEWER"

    r = client.put(f"/admin/users/{uid}", json={"role": "ADMIN"})
    assert r.status_code == 200
    assert r.json()["role"] == "ADMIN"

    usernames = {u["username"] for u in client.get("/admin/users").json()}
    assert {"admin", "rev", "newbie"} <= usernames
