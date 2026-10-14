from __future__ import annotations

from typing import Protocol

from protopane.domain.model.project import Project
from protopane.domain.model.project_summary import ProjectSummary


class ProjectRepository(Protocol):
    """Outbound port: where projects are persisted. Implemented by an adapter."""

    def list_summaries(self) -> list[ProjectSummary]: ...

    def get(self, slug: str) -> Project:
        """Return the project, or raise ProjectNotFoundError."""
        ...

    def save(self, project: Project) -> None: ...

    def delete(self, slug: str) -> None:
        """Delete the project, or raise ProjectNotFoundError."""
        ...

    def rename(self, slug: str, new_slug: str) -> None:
        """Move the project's storage to the new slug, so it is keyed there and gone
        from the old one. Raise ProjectNotFoundError for a missing source and
        ProjectExistsError for an occupied target."""
        ...

    def exists(self, slug: str) -> bool: ...
