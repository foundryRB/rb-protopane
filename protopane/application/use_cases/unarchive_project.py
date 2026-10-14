from __future__ import annotations

from protopane.application.events import PROJECT_UNARCHIVED, state_fact
from protopane.application.ports.event_publisher import EventPublisher
from protopane.application.ports.project_repository import ProjectRepository
from protopane.domain.model.project import Project


class UnarchiveProject:
    """Revive an archived project into the default listing."""

    def __init__(
        self, repository: ProjectRepository, events: EventPublisher | None = None
    ) -> None:
        self._repository = repository
        self._events = events

    def __call__(self, slug: str) -> Project:
        project = self._repository.get(slug)
        project.unarchive()
        self._repository.save(project)
        state_fact(
            self._events, event_type=PROJECT_UNARCHIVED, subject=slug, data={"project": slug}
        )
        return project
