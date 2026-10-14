from __future__ import annotations

from fastapi.testclient import TestClient
from pytest_intent import intent


@intent("INT-PP-B11")
def test_lists_builtin_templates(client: TestClient) -> None:
    res = client.get("/api/templates")
    assert res.status_code == 200
    slugs = [t["slug"] for t in res.json()]
    assert {"landing", "dashboard", "form"} <= set(slugs)


@intent("INT-PP-B12")
def test_create_from_template_uses_its_html(client: TestClient) -> None:
    template = client.get("/api/templates/landing").json()
    created = client.post("/api/projects", json={"name": "Acme", "template": "landing"})
    assert created.status_code == 201
    assert created.json()["screens"][0]["html"] == template["html"]


@intent("INT-PP-B13")
def test_save_template_is_listable_and_retrievable(client: TestClient) -> None:
    saved = client.post("/api/templates", json={"name": "My Hero", "html": "<h1>Hero</h1>"})
    assert saved.status_code == 201
    slug = saved.json()["slug"]

    got = client.get(f"/api/templates/{slug}")
    assert got.status_code == 200
    assert got.json()["html"] == "<h1>Hero</h1>"
    assert slug in [t["slug"] for t in client.get("/api/templates").json()]
