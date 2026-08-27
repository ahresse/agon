"""US4 history persistence + fidelity tests (T063-T064, FR-011, SC-005)."""
from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from tests.http_helpers import fresh_app_client, login, upload_python  # noqa: E402


def test_history_lists_and_reopens_with_intact_breakdown():
    client, _ = fresh_app_client({"rev": "REVIEWER"})
    login(client, "rev")
    r1 = upload_python(client, "cand-1")
    r2 = upload_python(client, "cand-2")

    listing = client.get("/reviews").json()
    ids = {r["id"] for r in listing}
    assert {r1["id"], r2["id"]} <= ids
    labels = {r["candidate_label"] for r in listing}
    assert {"cand-1", "cand-2"} <= labels

    # Reopen and confirm stored breakdown is retrievable and non-empty.
    detail = client.get(f"/reviews/{r1['id']}").json()
    assert detail["results"]
    assert detail["final_grade"] is not None

    # Fidelity: reopening again yields identical stored data.
    detail2 = client.get(f"/reviews/{r1['id']}").json()
    assert detail == detail2


def test_history_scoped_to_reviewer():
    client, _ = fresh_app_client({"a": "REVIEWER", "b": "REVIEWER"})
    login(client, "a")
    ra = upload_python(client, "a-cand")
    login(client, "b")
    listing_b = client.get("/reviews").json()
    assert ra["id"] not in {r["id"] for r in listing_b}
