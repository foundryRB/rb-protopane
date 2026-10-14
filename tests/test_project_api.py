from __future__ import annotations

from fastapi.testclient import TestClient
from pytest_intent import intent


@intent("INT-PP-B01")
def test_create_lists_and_persists(client: TestClient) -> None:
    created = client.post("/api/projects", json={"name": "Acme Corp"})
    assert created.status_code == 201
    slug = created.json()["slug"]

    listing = client.get("/api/projects")
    assert listing.status_code == 200
    assert slug in [p["slug"] for p in listing.json()]


@intent("INT-PP-B05")
def test_missing_project_is_404(client: TestClient) -> None:
    assert client.get("/api/projects/does-not-exist").status_code == 404


@intent("INT-PP-B06")
def test_same_name_yields_distinct_slugs(client: TestClient) -> None:
    first = client.post("/api/projects", json={"name": "Acme"}).json()["slug"]
    second = client.post("/api/projects", json={"name": "Acme"}).json()["slug"]
    assert first != second


@intent("INT-PP-B08")
def test_delete_removes_project(client: TestClient) -> None:
    slug = client.post("/api/projects", json={"name": "Temp"}).json()["slug"]
    assert client.delete(f"/api/projects/{slug}").status_code == 204
    assert client.get(f"/api/projects/{slug}").status_code == 404


@intent("INT-PP-B29")
def test_rename_moves_slug_and_persists_new_name(client: TestClient) -> None:
    client.post("/api/projects", json={"name": "Foundry Console"})
    renamed = client.post(
        "/api/projects/foundry-console/rename",
        json={"new_slug": "foundry-console-v1-design", "new_name": "Foundry Console (v1)"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["slug"] == "foundry-console-v1-design"
    assert renamed.json()["name"] == "Foundry Console (v1)"

    # The project moved whole: theme and screens answer at the new slug, not the old.
    moved = client.get("/api/projects/foundry-console-v1-design")
    assert moved.status_code == 200
    assert moved.json()["theme"]["tokens"]["--primary"]
    assert len(moved.json()["screens"]) >= 1
    assert client.get("/api/projects/foundry-console").status_code == 404


def test_rename_refusals_carry_the_reason(client: TestClient) -> None:
    client.post("/api/projects", json={"name": "Acme"})
    client.post("/api/projects", json={"name": "Other"})

    occupied = client.post("/api/projects/acme/rename", json={"new_slug": "other"})
    assert occupied.status_code == 409
    assert "other" in occupied.json()["detail"]

    malformed = client.post("/api/projects/acme/rename", json={"new_slug": "Not A Slug!"})
    assert malformed.status_code == 422
    assert "Not A Slug!" in malformed.json()["detail"]


@intent("INT-PP-B31")
def test_archive_parks_and_unarchive_revives(client: TestClient) -> None:
    slug = client.post("/api/projects", json={"name": "Stale Work"}).json()["slug"]

    archived = client.post(f"/api/projects/{slug}/archive")
    assert archived.status_code == 200
    assert archived.json()["archived"] is True

    # Parked out of the default listing, but visible (and marked) on request.
    assert slug not in [p["slug"] for p in client.get("/api/projects").json()]
    full = client.get("/api/projects", params={"include_archived": "true"}).json()
    assert next(p for p in full if p["slug"] == slug)["archived"] is True

    # The data is parked, not deleted: the project still reads back whole.
    assert client.get(f"/api/projects/{slug}").status_code == 200

    assert client.post(f"/api/projects/{slug}/unarchive").status_code == 200
    listing = client.get("/api/projects").json()
    assert next(p for p in listing if p["slug"] == slug)["archived"] is False


@intent("INT-PP-B27")
def test_named_schemes_persist_validate_and_delete(client: TestClient) -> None:
    slug = client.post("/api/projects", json={"name": "Palette Co"}).json()["slug"]
    tokens = client.get(f"/api/projects/{slug}").json()["theme"]["tokens"]

    # A full canonical token set saves as a named scheme and persists on the project.
    saved = client.put(
        f"/api/projects/{slug}/schemes/candy", json={"name": "Candy", "tokens": tokens}
    )
    assert saved.status_code == 200
    assert [(s["slug"], s["name"]) for s in saved.json()["schemes"]] == [("candy", "Candy")]
    # It survives a reload: persisted, not merely echoed.
    assert client.get(f"/api/projects/{slug}").json()["schemes"][0]["slug"] == "candy"

    # A partial / non-canonical set is refused, exactly like the live theme.
    bad = client.put(
        f"/api/projects/{slug}/schemes/broken",
        json={"name": "Broken", "tokens": {"--primary": "10 20% 30%"}},
    )
    assert bad.status_code == 422

    # Deleting removes it; deleting an unknown scheme is a 404.
    deleted = client.delete(f"/api/projects/{slug}/schemes/candy")
    assert deleted.status_code == 200
    assert deleted.json()["schemes"] == []
    assert client.delete(f"/api/projects/{slug}/schemes/candy").status_code == 404


@intent("INT-PP-B07")
def test_export_carries_design_system_over_http(client: TestClient) -> None:
    slug = client.post("/api/projects", json={"name": "Provenance Co"}).json()["slug"]
    tokens = client.get(f"/api/projects/{slug}").json()["theme"]["tokens"]
    system = client.get("/api/design-systems").json()[0]

    # A hand-authored theme exports with no provenance.
    assert client.get(f"/api/projects/{slug}/export").json()["design_system"] is None

    # Seeding from the library records it; the export and the project carry it.
    saved = client.put(
        f"/api/projects/{slug}/theme",
        json={"tokens": tokens, "design_system": system["slug"]},
    )
    assert saved.status_code == 200
    assert saved.json()["design_system"]["slug"] == system["slug"]
    export = client.get(f"/api/projects/{slug}/export").json()
    assert export["design_system"]["name"] == system["name"]
    assert export["design_system"]["guidance"] == system["guidance"]

    # An unknown library slug is a 404, and leaves no provenance behind.
    bad = client.put(
        f"/api/projects/{slug}/theme",
        json={"tokens": tokens, "design_system": "no-such-system"},
    )
    assert bad.status_code == 404
