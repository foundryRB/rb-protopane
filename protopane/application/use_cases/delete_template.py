from __future__ import annotations

from protopane.application.ports.template_repository import TemplateRepository


class DeleteTemplate:
    def __init__(self, templates: TemplateRepository) -> None:
        self._templates = templates

    def __call__(self, slug: str) -> None:
        self._templates.delete(slug)
