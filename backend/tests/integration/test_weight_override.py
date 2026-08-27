"""US2 weight-override tests (T049-T051, FR-009/010/017, SC-003/007)."""
from __future__ import annotations

import time

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from tests.http_helpers import fresh_app_client, login, upload_python  # noqa: E402


def _first_two_tests(client):
    r = client.get("/tests")
    assert r.status_code == 200
    tests = r.json()
    assert len(tests) >= 2
    return tests[0], tests[1]


def test_weight_override_recomputes_without_reexecution_under_2s():
    client, _ = fresh_app_client({"rev": "REVIEWER"})
    login(client, "rev")
    review = upload_python(client)
    detail = client.get(f"/reviews/{review['id']}").json()
    original_ran_at = {r["test_id"]: r for r in detail["results"]}
    t0, t1 = _first_two_tests(client)

    start = time.perf_counter()
    r = client.put(
        f"/reviews/{review['id']}/weights",
        json={"overrides": [{"test_id": t0["id"], "weight": 5.0}, {"test_id": t1["id"], "weight": 0.0}]},
    )
    elapsed = time.perf_counter() - start
    assert r.status_code == 200, r.text
    assert elapsed < 2.0  # SC-003

    updated = r.json()
    # Effective weight for t0 is now 5.0; recompute reflects it.
    weights = {res["test_id"]: res["effective_weight"] for res in updated["results"]}
    assert weights[t0["id"]] == 5.0
    assert weights[t1["id"]] == 0.0
    # No re-execution: results still present (same set of tests graded).
    assert set(r["test_id"] for r in updated["results"]) == set(original_ran_at)


def test_all_zero_weights_rejected():
    client, _ = fresh_app_client({"rev": "REVIEWER"})
    login(client, "rev")
    review = upload_python(client)
    tests = client.get("/tests").json()
    overrides = [{"test_id": t["id"], "weight": 0.0} for t in tests]
    r = client.put(f"/reviews/{review['id']}/weights", json={"overrides": overrides})
    assert r.status_code == 422


def test_override_isolation_between_reviewers():
    client, _ = fresh_app_client({"a": "REVIEWER", "b": "REVIEWER"})
    # Reviewer A uploads and overrides weights.
    login(client, "a")
    review_a = upload_python(client, "cand-a")
    t0, t1 = _first_two_tests(client)
    client.put(
        f"/reviews/{review_a['id']}/weights",
        json={"overrides": [{"test_id": t0["id"], "weight": 9.0}]},
    )
    a_detail = client.get(f"/reviews/{review_a['id']}").json()
    a_weight = {r["test_id"]: r["effective_weight"] for r in a_detail["results"]}[t0["id"]]
    assert a_weight == 9.0

    # Reviewer B uploads the (separate) review; A's override does not leak.
    login(client, "b")
    review_b = upload_python(client, "cand-b")
    b_detail = client.get(f"/reviews/{review_b['id']}").json()
    b_weight = {r["test_id"]: r["effective_weight"] for r in b_detail["results"]}[t0["id"]]
    assert b_weight == 1.0  # default, unaffected by A
