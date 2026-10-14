from __future__ import annotations

from pathlib import Path

from pytest_intent import intent

from protopane.adapters.outbound.persistence.file_project_repository import FileProjectRepository
from protopane.domain.constants import DEFAULT_SCREEN_SLUG, DEFAULT_THEME_TOKENS
from protopane.domain.model.project import Project
from protopane.domain.model.screen import Screen
from protopane.domain.model.theme import Theme


def _project(slug: str) -> Project:
    return Project(
        slug=slug,
        name=slug.replace("-", " ").title(),
        theme=Theme(tokens=dict(DEFAULT_THEME_TOKENS)),
        screens=[Screen(slug=DEFAULT_SCREEN_SLUG, name="Home", html="<h1>Hi</h1>", css="")],
    )


@intent("INT-PP-B18")
def test_listing_skips_unreadable_project(tmp_path: Path) -> None:
    repo = FileProjectRepository(tmp_path)
    repo.save(_project("good-one"))
    repo.save(_project("good-two"))
    # A corrupt project.json must not take down the listing of the others.
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "project.json").write_text("{ not valid json", encoding="utf-8")

    slugs = {s.slug for s in repo.list_summaries()}
    assert slugs == {"good-one", "good-two"}


@intent("INT-PP-B19")
def test_save_is_atomic(tmp_path: Path) -> None:
    repo = FileProjectRepository(tmp_path)
    repo.save(_project("acme"))
    directory = tmp_path / "acme"
    # The temp file was consumed by the atomic replace; only the final file remains.
    assert (directory / "project.json").is_file()
    assert not list(directory.glob("*.tmp"))
    assert repo.get("acme").slug == "acme"
    # Overwriting also leaves a single complete file, never a partial one.
    repo.save(_project("acme"))
    assert not list(directory.glob("*.tmp"))
    assert repo.get("acme").name == "Acme"
