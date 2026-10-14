"""Template routes: the built-in and saved starting screens."""

from __future__ import annotations

from fastapi import APIRouter, Response

from protopane.adapters.inbound.http.dtos.save_template_request import SaveTemplateRequest
from protopane.adapters.inbound.http.dtos.template_dto import TemplateDTO
from protopane.adapters.inbound.http.dtos.template_summary_dto import TemplateSummaryDTO
from protopane.adapters.inbound.http.mappers.template_mapper import (
    template_summary_to_dto,
    template_to_dto,
)
from protopane.container import Container

__all__ = ["build_templates_router"]


def build_templates_router(container: Container) -> APIRouter:
    """Wire the template routes to the container's use cases. Presentation only, no logic."""
    router = APIRouter(prefix="/api")

    @router.get("/templates", response_model=list[TemplateSummaryDTO])
    def list_templates() -> list[TemplateSummaryDTO]:
        return [template_summary_to_dto(t) for t in container.list_templates()]

    @router.get("/templates/{slug}", response_model=TemplateDTO)
    def get_template(slug: str) -> TemplateDTO:
        return template_to_dto(container.get_template(slug))

    @router.post("/templates", response_model=TemplateDTO, status_code=201)
    def save_template(body: SaveTemplateRequest) -> TemplateDTO:
        return template_to_dto(container.save_template(body.name, body.html))

    @router.delete("/templates/{slug}", status_code=204)
    def delete_template(slug: str) -> Response:
        container.delete_template(slug)
        return Response(status_code=204)

    return router
