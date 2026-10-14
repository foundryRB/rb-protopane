from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient
from pytest_intent import intent


def _client_with_dist(dist: Path) -> TestClient:
    os.environ["PROTOPANE_PROJECTS_DIR"] = str(dist.parent / "projects")
    os.environ["PROTOPANE_FRONTEND_DIST"] = str(dist)
    os.environ["PROTOPANE_AUTH_DISABLED"] = "true"
    from protopane.adapters.inbound.http.app import create_app

    return TestClient(create_app())


@intent("INT-PP-B09")
def test_serves_built_spa(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><div id=root>SPA</div>", encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log('app')", encoding="utf-8")

    with _client_with_dist(dist) as client:
        root = client.get("/")
        assert root.status_code == 200
        assert "SPA" in root.text

        # A client-side route falls back to index.html (SPA routing).
        spa_route = client.get("/p/acme")
        assert spa_route.status_code == 200
        assert "SPA" in spa_route.text

        # Real static assets are served as themselves.
        asset = client.get("/assets/app.js")
        assert asset.status_code == 200
        assert "console.log" in asset.text

        # The API still works under the same app.
        assert client.get("/api/projects").status_code == 200


@intent("INT-PP-B10")
def test_build_hint_when_frontend_missing(tmp_path: Path) -> None:
    with _client_with_dist(tmp_path / "no-dist") as client:
        root = client.get("/")
        assert root.status_code == 503
        assert "not built" in root.text.lower()
        # The API is unaffected by the missing frontend.
        assert client.get("/api/projects").status_code == 200
