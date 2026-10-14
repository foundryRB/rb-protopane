from __future__ import annotations

from protopane.application.events import PROJECT_RENAMED, state_fact
from protopane.application.ports.event_publisher import EventPublisher
from protopane.application.ports.project_repository import ProjectRepository
from protopane.domain.exceptions.invalid_slug_error import InvalidSlugError
from protopane.domain.model.project import Project
from protopane.domain.slugify import slugify


class RenameProject:
    """Rename a project's display name and, when a new slug is given, its identity.

    The slug is the storage key and the join key other systems look a project up
    by, so a slug rename detaches the project from whatever referenced the old
    slug. An occupied or malformed target slug is refused with the reason.
    """

    def __init__(
        self, repository: ProjectRepository, events: EventPublisher | None = None
    ) -> None:
        self._repository = repository
        self._events = events

    def __call__(
        self, slug: str, new_slug: str | None = None, new_name: str | None = None
    ) -> Project:
        if new_slug is not None and slugify(new_slug) != new_slug:
            raise InvalidSlugError(new_slug)
        project = self._repository.get(slug)
        if new_slug is not None and new_slug != slug:
            self._repository.rename(slug, new_slug)
            project.slug = new_slug
        if new_name is not None:
            project.name = new_name.strip() or project.name
        self._repository.save(project)
        state_fact(
            self._events,
            event_type=PROJECT_RENAMED,
            subject=project.slug,
            data={"project": project.slug, "previous": slug, "name_changed": new_name is not None},
        )
        return project
