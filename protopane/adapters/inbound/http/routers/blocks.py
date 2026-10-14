"""Block routes: the palette vocabulary screens are assembled from."""

from __future__ import annotations

from fastapi import APIRouter

from protopane.adapters.inbound.http.dtos.block_dto import BlockDTO
from protopane.adapters.inbound.http.mappers.block_mapper import block_to_dto
from protopane.container import Container

__all__ = ["build_blocks_router"]


def build_blocks_router(container: Container) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/blocks", response_model=list[BlockDTO])
    def list_blocks() -> list[BlockDTO]:
        return [block_to_dto(b) for b in container.list_blocks()]

    return router
