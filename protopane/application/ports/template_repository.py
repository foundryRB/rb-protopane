from __future__ import annotations

from typing import Protocol

from protopane.domain.model.template import Template


class TemplateRepository(Protocol):
    """Outbound port: built-in starter templates plus user-saved ones."""

    def list_templates(self) -> list[Template]: ...

    def get(self, slug: str) -> Template:
        """Return the template, or raise TemplateNotFoundError."""
        ...

    def save(self, template: Template) -> None: ...

    def delete(self, slug: str) -> None:
        """Delete a saved template. Raise TemplateNotFoundError when absent,
        BuiltinTemplateError for the built-in set."""
        ...
