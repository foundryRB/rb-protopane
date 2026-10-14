"""Design-system routes: the read-only catalogue of vendored token sets."""

from __future__ import annotations

from fastapi import APIRouter

from protopane.adapters.inbound.http.dtos.design_system_dto import DesignSystemDTO
from protopane.adapters.inbound.http.mappers.design_system_mapper import design_system_to_dto
from protopane.container import Container

__all__ = ["build_design_systems_router"]


def build_design_systems_router(container: Container) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/design-systems", response_model=list[DesignSystemDTO])
    def list_design_systems() -> list[DesignSystemDTO]:
        return [design_system_to_dto(d) for d in container.list_design_systems()]

    @router.get("/identity-sources")
    def list_identity_sources() -> list[dict[str, str]]:
        return container.list_identity_sources()

    @router.get("/identity-sources/{slug}")
    def get_identity_source(slug: str) -> dict:
        return container.get_identity_source(slug)

    @router.get("/design-systems/{slug}")
    def get_design_system(slug: str) -> DesignSystemDTO:
        return design_system_to_dto(container.get_design_system(slug))

    return router
