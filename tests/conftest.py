from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from protopane.container import Container


@pytest.fixture
def container(tmp_path: Path) -> Container:
    """A container wired to isolated, temporary projects + templates directories."""
    return Container(projects_dir=tmp_path / "projects", templates_dir=tmp_path / "templates")


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """A TestClient over the FastAPI app, with persistence in a temp dir and no SPA mount."""
    monkeypatch.setenv("PROTOPANE_PROJECTS_DIR", str(tmp_path / "projects"))
    monkeypatch.setenv("PROTOPANE_TEMPLATES_DIR", str(tmp_path / "templates"))
    monkeypatch.setenv("PROTOPANE_FRONTEND_DIST", str(tmp_path / "no-dist"))
    monkeypatch.setenv("PROTOPANE_AUTH_DISABLED", "true")
    from protopane.adapters.inbound.http.app import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
