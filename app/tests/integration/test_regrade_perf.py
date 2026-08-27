"""Performance test: weight-change re-grade completes < 2s (T074, SC-003)."""
from __future__ import annotations

import time

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from tests.http_helpers import fresh_app_client, login, upload_python  # noqa: E402


def test_regrade_under_2_seconds():
    client, _ = fresh_app_client({"rev": "REVIEWER"})
    login(client, "rev")
    review = upload_python(client)
    test = client.get("/tests").json()[0]

    # Measure only the recompute path (no test re-execution).
    start = time.perf_counter()
    r = client.put(
        f"/reviews/{review['id']}/weights",
        json={"overrides": [{"test_id": test["id"], "weight": 4.0}]},
    )
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed < 2.0, f"re-grade took {elapsed:.3f}s"
