from __future__ import annotations

from protopane.application.events import SCREEN_DELETED, state_fact
from protopane.application.ports.event_publisher import EventPublisher
from protopane.application.ports.project_change_notifier import ProjectChangeNotifier
from protopane.application.ports.project_repository import ProjectRepository
from protopane.domain.model.project import Project


class DeleteScreen:
    def __init__(
        self,
        repository: ProjectRepository,
        notifier: ProjectChangeNotifier,
        events: EventPublisher | None = None,
    ) -> None:
        self._repository = repository
        self._notifier = notifier
        self._events = events

    def __call__(self, slug: str, screen_slug: str) -> Project:
        project = self._repository.get(slug)
        project.remove_screen(screen_slug)
        self._repository.save(project)
        self._notifier.publish(slug)
        state_fact(
            self._events,
            event_type=SCREEN_DELETED,
            subject=slug,
            data={"project": slug, "screen": screen_slug},
        )
        return project
