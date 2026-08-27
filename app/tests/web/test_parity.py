"""Parity test: the review-detail page presents the same structured breakdown,
pros/cons, and per-test contributions as the read model (US2, Principle IV)."""
from __future__ import annotations

from html import escape

from tests.web.conftest import login, upload


def test_review_detail_shows_breakdown_and_contributions(client):
    login(client)
    url = upload(client)
    html = client.get(url).text
    # Structured breakdown headers present.
    for header in ("Test", "Grade", "Weight", "Contribution", "Findings"):
        assert header in html
    assert "Final grade" in html
    assert "Aggregated findings" in html


def test_review_detail_lists_all_graded_tests(client):
    login(client)
    url = upload(client)
    review_id = url.rsplit("/", 1)[-1]
    # Compare against the JSON read model.
    api = client.get(f"/reviews/{review_id}").json()
    html = client.get(url).text
    for res in api["results"]:
        # Template autoescapes, so compare against the HTML-escaped name.
        assert escape(res["test_name"]) in html
