from __future__ import annotations

from protopane.application.events import SCHEME_SAVED, state_fact
from protopane.application.ports.event_publisher import EventPublisher
from protopane.application.ports.project_change_notifier import ProjectChangeNotifier
from protopane.application.ports.project_repository import ProjectRepository
from protopane.domain.exceptions.invalid_theme_error import InvalidThemeError
from protopane.domain.model.project import Project
from protopane.domain.model.scheme import Scheme
from protopane.domain.token_discipline import lint_theme_tokens


class SaveScheme:
    """Upsert one named colour scheme on a project, gated to the canonical shadcn tokens.

    A scheme is a full palette the editor applies in one click, so it carries the same
    token-discipline invariant as the live theme: the canonical set, well-formed, no literals.
    """

    def __init__(
        self,
        repository: ProjectRepository,
        notifier: ProjectChangeNotifier,
        events: EventPublisher | None = None,
    ) -> None:
        self._repository = repository
        self._notifier = notifier
        self._events = events

    def __call__(self, slug: str, scheme_slug: str, name: str, tokens: dict[str, str]) -> Project:
        violations = lint_theme_tokens(tokens)
        if violations:
            raise InvalidThemeError(violations)
        project = self._repository.get(slug)
        project.upsert_scheme(Scheme(slug=scheme_slug, name=name, tokens=dict(tokens)))
        self._repository.save(project)
        self._notifier.publish(slug)
        state_fact(
            self._events,
            event_type=SCHEME_SAVED,
            subject=slug,
            data={"project": slug, "scheme": scheme_slug},
        )
        return project
