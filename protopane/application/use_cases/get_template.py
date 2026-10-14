from __future__ import annotations

from protopane.application.ports.template_repository import TemplateRepository
from protopane.domain.model.template import Template


class GetTemplate:
    def __init__(self, templates: TemplateRepository) -> None:
        self._templates = templates

    def __call__(self, slug: str) -> Template:
        return self._templates.get(slug)
