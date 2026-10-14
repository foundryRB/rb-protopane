from __future__ import annotations

from fastapi.testclient import TestClient


def test_config_reports_chat_disabled_by_default(client: TestClient) -> None:
    res = client.get("/api/config")
    assert res.status_code == 200
    assert res.json() == {"chatEnabled": False}


def test_chat_route_absent_when_agent_disabled(client: TestClient) -> None:
    # Fail closed: with the agent flag unset, the chat POST route is never mounted.
    # The SPA catch-all (a GET route) claims the path, so POST resolves to 405, not 200.
    res = client.post("/api/projects/whatever/chat", json={"message": "hi", "history": []})
    assert res.status_code in (404, 405)
