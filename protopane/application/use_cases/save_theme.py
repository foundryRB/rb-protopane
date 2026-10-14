from __future__ import annotations

from protopane.application.events import THEME_SAVED, state_fact
from protopane.application.ports.design_system_library import DesignSystemLibrary
from protopane.application.ports.event_publisher import EventPublisher
from protopane.application.ports.project_change_notifier import ProjectChangeNotifier
from protopane.application.ports.project_repository import ProjectRepository
from protopane.domain.exceptions.invalid_theme_error import InvalidThemeError
from protopane.domain.model.design_system_ref import DesignSystemRef
from protopane.domain.model.project import Project
from protopane.domain.model.theme import Theme
from protopane.domain.token_discipline import lint_theme_tokens


class SaveTheme:
    """Replace the project's token set, gated to the canonical shadcn tokens.

    When the save seeds from a packaged design system (`design_system` names its
    library slug), the project records that provenance with the system's guidance
    snapshotted verbatim — the identity's rationale travels with the project into
    the handoff export. Omitting the slug leaves any recorded provenance intact:
    a hand-tune refines the identity, it does not erase where it came from.
    """

    def __init__(
        self,
        repository: ProjectRepository,
        notifier: ProjectChangeNotifier,
        library: DesignSystemLibrary,
        events: EventPublisher | None = None,
    ) -> None:
        self._repository = repository
        self._notifier = notifier
        self._library = library
        self._events = events

    def __call__(
        self, slug: str, tokens: dict[str, str], design_system: str | None = None
    ) -> Project:
        violations = lint_theme_tokens(tokens)
        if violations:
            raise InvalidThemeError(violations)
        project = self._repository.get(slug)
        project.set_theme(Theme(tokens=dict(tokens)))
        if design_system is not None:
            system = self._library.get_design_system(design_system)
            project.record_design_system(
                DesignSystemRef(slug=system.slug, name=system.name, guidance=system.guidance)
            )
        self._repository.save(project)
        self._notifier.publish(slug)
        # The token values stay in the instance; the fact names the design system
        # the theme now follows, if one was recorded (REF-Events section 5).
        state_fact(
            self._events,
            event_type=THEME_SAVED,
            subject=slug,
            data={"project": slug, "design_system": design_system, "tokens": len(tokens)},
        )
        return project
