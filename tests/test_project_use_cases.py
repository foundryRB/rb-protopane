from __future__ import annotations

import pytest
from pytest_intent import intent

from protopane.container import Container
from protopane.domain.constants import DEFAULT_SCREEN_SLUG, DEFAULT_THEME_TOKENS
from protopane.domain.exceptions import InvalidSlugError, ProjectExistsError


@intent("INT-PP-B02")
def test_new_project_has_default_theme_and_starter_screen(container: Container) -> None:
    project = container.create_project("Acme")
    assert project.theme.tokens["--primary"]
    assert project.screen(DEFAULT_SCREEN_SLUG) is not None


@intent("INT-PP-B03")
def test_save_theme_persists_tokens(container: Container) -> None:
    project = container.create_project("Acme")
    tokens = {**DEFAULT_THEME_TOKENS, "--primary": "262 83% 58%", "--ring": "262 83% 58%"}
    container.save_theme(project.slug, tokens)
    reloaded = container.get_project(project.slug)
    assert reloaded.theme.tokens["--primary"] == "262 83% 58%"


@intent("INT-PP-B04")
def test_save_screen_upserts_and_persists(container: Container) -> None:
    project = container.create_project("Acme")
    container.save_screen(project.slug, "home", "Home", "<h1>Hi</h1>", "")
    container.save_screen(project.slug, "about", "About", "<h1>About</h1>", "")
    reloaded = container.get_project(project.slug)
    assert {s.slug for s in reloaded.screens} == {"home", "about"}
    home = reloaded.screen("home")
    assert home is not None
    assert home.html == "<h1>Hi</h1>"


@intent("INT-PP-B04")
def test_save_screen_preserves_order_on_update(container: Container) -> None:
    project = container.create_project("Acme")
    container.save_screen(project.slug, "home", "Home", "<h1>Hi</h1>", "")
    container.save_screen(project.slug, "page-2", "Page 2", "<h1>Page 2</h1>", "")

    container.save_screen(project.slug, "home", "Home", "<h1>Updated</h1>", "")

    reloaded = container.get_project(project.slug)
    assert [s.slug for s in reloaded.screens] == ["home", "page-2"]
    assert reloaded.screen("home").html == "<h1>Updated</h1>"


@intent("INT-PP-B30")
def test_rename_refuses_occupied_or_malformed_slug(container: Container) -> None:
    container.create_project("Acme")
    other = container.create_project("Other")

    with pytest.raises(ProjectExistsError):
        container.rename_project("acme", new_slug=other.slug)
    with pytest.raises(InvalidSlugError):
        container.rename_project("acme", new_slug="Not A Slug!")

    # Both refusals left the project untouched at its original identity.
    untouched = container.get_project("acme")
    assert untouched.name == "Acme"


@intent("INT-PP-B07")
def test_export_renders_theme_css_and_screens(container: Container) -> None:
    project = container.create_project("Acme")
    export = container.export_project(project.slug)
    assert export.theme_css.startswith(":root {")
    assert "--primary" in export.theme_css
    assert len(export.screens) >= 1


@intent("INT-PP-B03")
def test_save_theme_records_design_system_provenance(container: Container) -> None:
    project = container.create_project("Acme")
    system = container.list_design_systems()[0]
    container.save_theme(project.slug, dict(DEFAULT_THEME_TOKENS), design_system=system.slug)
    reloaded = container.get_project(project.slug)
    assert reloaded.design_system is not None
    assert reloaded.design_system.slug == system.slug
    assert reloaded.design_system.guidance == system.guidance
    # A later hand-tune refines the identity without erasing where it came from.
    container.save_theme(project.slug, dict(DEFAULT_THEME_TOKENS))
    assert container.get_project(project.slug).design_system is not None


@intent("INT-PP-B03")
def test_save_theme_rejects_unknown_design_system(container: Container) -> None:
    from protopane.domain.exceptions import DesignSystemNotFoundError

    project = container.create_project("Acme")
    with pytest.raises(DesignSystemNotFoundError):
        container.save_theme(project.slug, dict(DEFAULT_THEME_TOKENS), design_system="no-such")
    # The refused save left no provenance behind.
    assert container.get_project(project.slug).design_system is None


@intent("INT-PP-B07")
def test_export_carries_design_system_provenance(container: Container) -> None:
    project = container.create_project("Acme")
    bare = container.export_project(project.slug)
    assert bare.design_system is None
    system = container.list_design_systems()[0]
    container.save_theme(project.slug, dict(DEFAULT_THEME_TOKENS), design_system=system.slug)
    export = container.export_project(project.slug)
    assert export.design_system is not None
    assert export.design_system.name == system.name
    assert export.design_system.guidance == system.guidance
