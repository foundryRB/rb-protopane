"""Domain-to-DTO mapper for palette blocks."""

from __future__ import annotations

from protopane.adapters.inbound.http.dtos.block_dto import BlockDTO
from protopane.domain.model.block import Block

__all__ = ["block_to_dto"]


def block_to_dto(block: Block) -> BlockDTO:
    return BlockDTO(
        slug=block.slug,
        label=block.label,
        category=block.category,
        html=block.html,
        preview=block.preview,
    )
