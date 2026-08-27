"""Page render + auth tests for the server-rendered web interface (US1)."""
from __future__ import annotations

from tests.web.conftest import login


class TestPublicAndAuthRedirects:
    def test_login_page_renders(self, client):
        r = client.get("/login")
        assert r.status_code == 200
        assert "Sign in" in r.text

    def test_protected_page_redirects_to_login(self, client):
        r = client.get("/ui/reviews", follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"] == "/login"

    def test_root_redirects(self, client):
        assert client.get("/", follow_redirects=False).status_code == 303


class TestReviewerPages:
    def test_history_and_upload_render(self, client):
        login(client)
        assert client.get("/ui/reviews").status_code == 200
        r = client.get("/ui/upload")
        assert r.status_code == 200
        assert "Upload" in r.text

    def test_bad_login_shows_error(self, client):
        r = client.post("/login", data={"username": "reviewer", "password": "nope"})
        assert r.status_code == 401
        assert "Invalid credentials" in r.text


class TestAdminAccessControl:
    def test_reviewer_denied_admin_pages(self, client):
        login(client, "reviewer")
        r = client.get("/ui/admin/tests", follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"] == "/ui/reviews"

    def test_admin_pages_render(self, client):
        login(client, "admin")
        assert client.get("/ui/admin/tests").status_code == 200
        assert client.get("/ui/admin/users").status_code == 200


class TestStaticAsset:
    def test_vendored_helper_served(self, client):
        r = client.get("/static/vendor/htmx.min.js")
        assert r.status_code == 200
        assert "htmx" in r.text
