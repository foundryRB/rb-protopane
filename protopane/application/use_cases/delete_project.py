from __future__ import annotations

from protopane.application.events import PROJECT_DELETED, state_fact
from protopane.application.ports.event_publisher import EventPublisher
from protopane.application.ports.project_repository import ProjectRepository


class DeleteProject:
    def __init__(
        self, repository: ProjectRepository, events: EventPublisher | None = None
    ) -> None:
        self._repository = repository
        self._events = events

    def __call__(self, slug: str) -> None:
        self._repository.delete(slug)
        state_fact(self._events, event_type=PROJECT_DELETED, subject=slug, data={"project": slug})
