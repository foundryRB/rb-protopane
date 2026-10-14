from __future__ import annotations

from protopane.application.events import PROJECT_ARCHIVED, state_fact
from protopane.application.ports.event_publisher import EventPublisher
from protopane.application.ports.project_repository import ProjectRepository
from protopane.domain.model.project import Project


class ArchiveProject:
    """Park a project: it keeps all its data but leaves the default listing."""

    def __init__(
        self, repository: ProjectRepository, events: EventPublisher | None = None
    ) -> None:
        self._repository = repository
        self._events = events

    def __call__(self, slug: str) -> Project:
        project = self._repository.get(slug)
        project.archive()
        self._repository.save(project)
        state_fact(self._events, event_type=PROJECT_ARCHIVED, subject=slug, data={"project": slug})
        return project
