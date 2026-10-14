from __future__ import annotations

from importlib.resources import files

from protopane.application.events import PROJECT_CREATED, state_fact
from protopane.application.ports.event_publisher import EventPublisher
from protopane.application.ports.project_repository import ProjectRepository
from protopane.application.ports.template_repository import TemplateRepository
from protopane.domain.constants import (
    DEFAULT_SCREEN_NAME,
    DEFAULT_SCREEN_SLUG,
    DEFAULT_THEME_TOKENS,
)
from protopane.domain.model.project import Project
from protopane.domain.model.screen import Screen
from protopane.domain.model.theme import Theme
from protopane.domain.slugify import slugify

_STARTER_HTML = (
    files("protopane").joinpath("starter_screen.html").read_text(encoding="utf-8").strip()
)


class CreateProject:
    def __init__(
        self,
        repository: ProjectRepository,
        templates: TemplateRepository,
        events: EventPublisher | None = None,
    ) -> None:
        self._repository = repository
        self._templates = templates
        self._events = events

    def __call__(self, name: str, template_slug: str | None = None) -> Project:
        html = self._templates.get(template_slug).html if template_slug else _STARTER_HTML
        slug = self._unique_slug(slugify(name))
        project = Project(
            slug=slug,
            name=name.strip() or slug,
            theme=Theme(tokens=dict(DEFAULT_THEME_TOKENS)),
            screens=[
                Screen(slug=DEFAULT_SCREEN_SLUG, name=DEFAULT_SCREEN_NAME, html=html, css="")
            ],
        )
        self._repository.save(project)
        # The project is persisted before the fact is stated; the event carries the
        # slug and the template it started from, never the markup (REF-Events section 5).
        state_fact(
            self._events,
            event_type=PROJECT_CREATED,
            subject=slug,
            data={"project": slug, "template": template_slug},
        )
        return project

    def _unique_slug(self, base: str) -> str:
        if not self._repository.exists(base):
            return base
        suffix = 2
        while self._repository.exists(f"{base}-{suffix}"):
            suffix += 1
        return f"{base}-{suffix}"
