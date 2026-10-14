from __future__ import annotations

from protopane.application.ports.template_repository import TemplateRepository
from protopane.domain.exceptions.off_token_markup_error import OffTokenMarkupError
from protopane.domain.model.template import Template
from protopane.domain.slugify import slugify
from protopane.domain.token_discipline import lint_markup


class SaveTemplate:
    """Capture a layout for reuse, gated by token discipline: a template seeds
    project screens, so off-token markup here would propagate."""

    def __init__(self, templates: TemplateRepository) -> None:
        self._templates = templates

    def __call__(self, name: str, html: str) -> Template:
        violations = lint_markup(html, "")
        if violations:
            raise OffTokenMarkupError(f"Template '{name}'", violations)
        template = Template(
            slug=slugify(name),
            name=name.strip() or "Template",
            html=html,
            builtin=False,
        )
        self._templates.save(template)
        return template
