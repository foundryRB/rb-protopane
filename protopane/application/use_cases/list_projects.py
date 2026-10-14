from __future__ import annotations

from protopane.application.ports.project_repository import ProjectRepository
from protopane.domain.model.project_summary import ProjectSummary


class ListProjects:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def __call__(self, include_archived: bool = False) -> list[ProjectSummary]:
        summaries = self._repository.list_summaries()
        if include_archived:
            return summaries
        return [s for s in summaries if not s.archived]
