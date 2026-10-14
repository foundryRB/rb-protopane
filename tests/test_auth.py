from __future__ import annotations

import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest_intent import intent


def _build_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, **env: str) -> TestClient:
    """A TestClient over a freshly built app with isolated dirs and the given auth env."""
    monkeypatch.setenv("PROTOPANE_PROJECTS_DIR", str(tmp_path / "projects"))
    monkeypatch.setenv("PROTOPANE_TEMPLATES_DIR", str(tmp_path / "templates"))
    monkeypatch.setenv("PROTOPANE_FRONTEND_DIST", str(tmp_path / "no-dist"))
    for key in (
        "PROTOPANE_AUTH_USER",
        "PROTOPANE_AUTH_PASSWORD",
        "PROTOPANE_AUTH_DISABLED",
        "PROTOPANE_AUTH_SCOPE",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    from protopane.adapters.inbound.http.app import create_app

    return TestClient(create_app())


def _basic(user: str, password: str) -> dict[str, str]:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@intent("INT-PP-B14")
def test_rejects_without_credentials(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        tmp_path, monkeypatch, PROTOPANE_AUTH_USER="studio", PROTOPANE_AUTH_PASSWORD="s3cret"
    )
    res = client.get("/api/projects")
    assert res.status_code == 401
    assert res.headers.get("WWW-Authenticate", "").lower().startswith("basic")
    # The gate covers every surface, including the /mcp mount.
    assert client.post("/mcp", json={}).status_code == 401


@intent("INT-PP-B15")
def test_accepts_valid_credentials(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        tmp_path, monkeypatch, PROTOPANE_AUTH_USER="studio", PROTOPANE_AUTH_PASSWORD="s3cret"
    )
    assert client.get("/api/projects", headers=_basic("studio", "s3cret")).status_code == 200
    # A wrong password is refused.
    assert client.get("/api/projects", headers=_basic("studio", "nope")).status_code == 401


@intent("INT-PP-B16")
def test_health_is_exempt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        tmp_path, monkeypatch, PROTOPANE_AUTH_USER="studio", PROTOPANE_AUTH_PASSWORD="s3cret"
    )
    res = client.get("/api/health")
    assert res.status_code == 200
    # The route also carries the running build (the OIDC gate skips it, so an
    # external observer reads which release serves without a credential).
    assert res.json()["status"] == "ok"
    assert res.json()["version"]


def test_health_reports_the_running_image_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The chart injects the promoted tag as $APP_VERSION, so the skipped health
    route names which release serves. A constant in code is not freshness."""
    monkeypatch.setenv("APP_VERSION", "3.1.4")
    client = _build_client(tmp_path, monkeypatch)
    assert client.get("/api/health").json()["version"] == "3.1.4"


@intent("INT-PP-B17")
def test_fails_closed_when_unconfigured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # No credentials and not explicitly disabled: protected routes must be closed, not open.
    client = _build_client(tmp_path, monkeypatch)
    assert client.get("/api/projects").status_code == 503
    assert client.post("/mcp", json={}).status_code == 503
    # Health still answers so probes keep working.
    assert client.get("/api/health").status_code == 200


@intent("INT-PP-B28")
def test_mcp_scope_gates_only_the_machine_door(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """scope=mcp keeps /mcp Basic-gated while the human surfaces serve open for
    an OIDC reverse proxy in front to gate."""
    client = _build_client(
        tmp_path,
        monkeypatch,
        PROTOPANE_AUTH_USER="studio",
        PROTOPANE_AUTH_PASSWORD="s3cret",
        PROTOPANE_AUTH_SCOPE="mcp",
    )
    # Enter the app lifespan so the /mcp transport's session manager is running;
    # the gate decision (before routing) is what these assertions exercise.
    with client:
        # The /mcp machine door stays gated: no credential is refused, a valid one admitted.
        assert client.post("/mcp", json={}).status_code == 401
        admitted = client.post("/mcp", json={}, headers=_basic("studio", "s3cret"))
        assert admitted.status_code not in (401, 503)
        # The human surfaces serve open; oauth2-proxy is their gate in front.
        assert client.get("/api/projects").status_code == 200


@intent("INT-PP-B28")
def test_mcp_scope_fails_closed_on_the_machine_door(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """scope=mcp with no credentials fails the /mcp door closed (503) while the
    human surfaces stay open for the proxy."""
    client = _build_client(tmp_path, monkeypatch, PROTOPANE_AUTH_SCOPE="mcp")
    assert client.post("/mcp", json={}).status_code == 503
    assert client.get("/api/projects").status_code == 200
    assert client.get("/api/health").status_code == 200


def test_agent_credential_returns_the_basic_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """/api/agent-credential hands the in-app connect menu the base64 HTTP Basic
    pair; behind oauth2-proxy under scope=mcp only an authenticated human reaches it."""
    client = _build_client(
        tmp_path,
        monkeypatch,
        PROTOPANE_AUTH_USER="studio",
        PROTOPANE_AUTH_PASSWORD="s3cret",
        PROTOPANE_AUTH_SCOPE="mcp",
    )
    res = client.get("/api/agent-credential")
    assert res.status_code == 200
    assert base64.b64decode(res.json()["credential"]).decode() == "studio:s3cret"


def test_agent_credential_fails_closed_when_unconfigured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no credential configured there is nothing to hand out: 503, never an
    empty or bogus credential."""
    client = _build_client(tmp_path, monkeypatch, PROTOPANE_AUTH_SCOPE="mcp")
    assert client.get("/api/agent-credential").status_code == 503


def test_identity_source_machine_reads_require_basic_even_under_oidc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _build_client(tmp_path, monkeypatch, PROTOPANE_AUTH_SCOPE="mcp",
                           PROTOPANE_AUTH_USER="reader", PROTOPANE_AUTH_PASSWORD="secret")
    for path in ("/api/identity-sources", "/api/identity-sources/vodafone-digital-engineering"):
        assert client.get(path).status_code == 401
        assert client.get(path, headers=_basic("reader", "wrong")).status_code == 401
        assert client.get(path, headers=_basic("reader", "secret")).status_code == 200
