from __future__ import annotations

from protopane.application.events import PROJECT_EXPORTED, state_fact
from protopane.application.ports.event_publisher import EventPublisher
from protopane.application.ports.project_repository import ProjectRepository
from protopane.domain.model.project_export import ProjectExport


class ExportProject:
    def __init__(
        self, repository: ProjectRepository, events: EventPublisher | None = None
    ) -> None:
        self._repository = repository
        self._events = events

    def __call__(self, slug: str) -> ProjectExport:
        project = self._repository.get(slug)
        export = ProjectExport(
            theme_css=project.theme.to_css(),
            screens=list(project.screens),
            design_system=project.design_system,
        )
        # The export is the version that leaves the hub for its durable home; the
        # fact counts what left, the markup itself rides the export (REF-Events section 5).
        state_fact(
            self._events,
            event_type=PROJECT_EXPORTED,
            subject=slug,
            data={"project": slug, "screens": len(export.screens)},
        )
        return export
