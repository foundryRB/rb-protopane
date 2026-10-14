"""Domain-to-DTO mappers for templates."""

from __future__ import annotations

from protopane.adapters.inbound.http.dtos.template_dto import TemplateDTO
from protopane.adapters.inbound.http.dtos.template_summary_dto import TemplateSummaryDTO
from protopane.domain.model.template import Template

__all__ = ["template_to_dto", "template_summary_to_dto"]


def template_to_dto(template: Template) -> TemplateDTO:
    return TemplateDTO(
        slug=template.slug, name=template.name, html=template.html, builtin=template.builtin
    )


def template_summary_to_dto(template: Template) -> TemplateSummaryDTO:
    return TemplateSummaryDTO(slug=template.slug, name=template.name, builtin=template.builtin)
