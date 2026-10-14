from __future__ import annotations

from protopane.application.ports.template_repository import TemplateRepository
from protopane.domain.model.template import Template


class ListTemplates:
    def __init__(self, templates: TemplateRepository) -> None:
        self._templates = templates

    def __call__(self) -> list[Template]:
        return self._templates.list_templates()
