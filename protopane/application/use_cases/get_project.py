from __future__ import annotations

from protopane.application.ports.project_repository import ProjectRepository
from protopane.domain.model.project import Project


class GetProject:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def __call__(self, slug: str) -> Project:
        return self._repository.get(slug)
