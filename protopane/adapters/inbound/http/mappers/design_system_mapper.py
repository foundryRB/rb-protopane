"""Domain-to-DTO mapper for design systems."""

from __future__ import annotations

from protopane.adapters.inbound.http.dtos.design_system_dto import DesignSystemDTO
from protopane.domain.model.design_system import DesignSystem

__all__ = ["design_system_to_dto"]


def design_system_to_dto(design_system: DesignSystem) -> DesignSystemDTO:
    return DesignSystemDTO(
        slug=design_system.slug,
        name=design_system.name,
        category=design_system.category,
        tokens=design_system.tokens,
        guidance=design_system.guidance,
        source=design_system.source,
    )
