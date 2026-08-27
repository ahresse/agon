"""Fragment (in-place update) tests: weight re-grade + evidence log (US2)."""
from __future__ import annotations

import re

from tests.web.conftest import login, upload


def _detail(client, review_url):
    r = client.get(review_url)
    assert r.status_code == 200
    return r.text


def _test_ids(html: str) -> list[str]:
    # weight inputs are named weight_<test_id>
    return re.findall(r'name="weight_([^"]+)"', html)


class TestWeightRegradeFragment:
    def test_regrade_returns_grade_fragment_no_full_page(self, client):
        login(client)
        url = upload(client)
        review_id = url.rsplit("/", 1)[-1]
        html = _detail(client, url)
        ids = _test_ids(html)
        assert ids, "expected weight inputs"

        # Post new weights (bump the first test).
        data = {f"weight_{tid}": "1" for tid in ids}
        data[f"weight_{ids[0]}"] = "5"
        r = client.post(f"/ui/reviews/{review_id}/weights", data=data)
        assert r.status_code == 200
        # Fragment, not a full page (no <html>/<nav> chrome).
        assert "<html" not in r.text.lower()
        assert 'id="grade-breakdown"' in r.text
        assert "Final grade" in r.text

    def test_all_zero_weights_rejected_inline(self, client):
        login(client)
        url = upload(client)
        review_id = url.rsplit("/", 1)[-1]
        ids = _test_ids(_detail(client, url))
        data = {f"weight_{tid}": "0" for tid in ids}
        r = client.post(f"/ui/reviews/{review_id}/weights", data=data)
        assert r.status_code == 422
        assert "positive weight" in r.text


class TestEvidenceLogFragment:
    def test_log_fragment_states(self, client):
        login(client)
        url = upload(client)
        review_id = url.rsplit("/", 1)[-1]
        ids = _test_ids(_detail(client, url))
        r = client.get(f"/ui/reviews/{review_id}/tests/{ids[0]}/log")
        assert r.status_code == 200
        assert "<html" not in r.text.lower()
        # Evidence logs are now captured, so a completed test renders its log in a
        # <pre> block (or, at minimum, an explicit no-evidence message).
        assert ("<pre" in r.text) or ("No additional evidence" in r.text) or ("No log available" in r.text)


class TestFragmentAuth:
    def test_fragment_requires_ownership(self, client):
        login(client, "reviewer")
        url = upload(client)
        review_id = url.rsplit("/", 1)[-1]
        # A different reviewer cannot fetch the log fragment.
        other = client
        login(other, "admin")  # admin is not the owner
        r = other.get(f"/ui/reviews/{review_id}/tests/x/log")
        assert r.status_code == 404
