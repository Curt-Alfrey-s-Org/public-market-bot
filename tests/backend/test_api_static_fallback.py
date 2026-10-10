"""
Review 2026-09-25 follow-up: the old committed frontend build in api/static/ was
removed from git (it trusted a client-side role). Production serves the UI from
the separate frontend container. Without api/static/ the API must not serve any
UI: "/" returns a small JSON banner and other non-API paths return 404.
"""

import pytest
from fastapi.testclient import TestClient

import api.main as api_main

pytestmark = pytest.mark.skipif(
    api_main._index_html.exists(),
    reason="a local api/static build is present; fallback behaviour not applicable",
)


def test_root_returns_api_banner_without_static_build():
    r = TestClient(api_main.app).get("/")
    assert r.status_code == 200
    assert r.json()["message"] == "Market Pie5 Bot API"


@pytest.mark.parametrize("path", ["/dashboard", "/settings", "/some/client/route"])
def test_spa_routes_404_without_static_build(path):
    assert TestClient(api_main.app).get(path).status_code == 404
