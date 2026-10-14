from __future__ import annotations

from protopane.application.events import SCREEN_SAVED, state_fact
from protopane.application.ports.event_publisher import EventPublisher
from protopane.application.ports.project_change_notifier import ProjectChangeNotifier
from protopane.application.ports.project_repository import ProjectRepository
from protopane.domain.exceptions.off_token_markup_error import OffTokenMarkupError
from protopane.domain.model.project import Project
from protopane.domain.model.screen import Screen
from protopane.domain.token_discipline import lint_markup


class SaveScreen:
    """Upsert one screen, gated by token discipline: off-token markup never persists."""

    def __init__(
        self,
        repository: ProjectRepository,
        notifier: ProjectChangeNotifier,
        events: EventPublisher | None = None,
    ) -> None:
        self._repository = repository
        self._notifier = notifier
        self._events = events

    def __call__(self, slug: str, screen_slug: str, name: str, html: str, css: str) -> Project:
        violations = lint_markup(html, css)
        if violations:
            raise OffTokenMarkupError(f"Screen '{screen_slug}'", violations)
        project = self._repository.get(slug)
        project.upsert_screen(Screen(slug=screen_slug, name=name, html=html, css=css))
        self._repository.save(project)
        self._notifier.publish(slug)
        state_fact(
            self._events,
            event_type=SCREEN_SAVED,
            subject=slug,
            data={"project": slug, "screen": screen_slug},
        )
        return project
