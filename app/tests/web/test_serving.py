"""Serving test: the single Python service serves the web interface + vendored
helper with no JS build artifact (US3, SC-005/SC-007)."""
from __future__ import annotations


class TestSingleServiceServing:
    def test_root_and_login_served(self, client):
        assert client.get("/", follow_redirects=False).status_code == 303
        assert client.get("/login").status_code == 200

    def test_vendored_helper_is_only_script_asset(self, client):
        r = client.get("/static/vendor/htmx.min.js")
        assert r.status_code == 200
        # No separate built bundle is required/served.
        assert client.get("/static/bundle.js").status_code == 404
        assert client.get("/assets/index.js").status_code == 404
