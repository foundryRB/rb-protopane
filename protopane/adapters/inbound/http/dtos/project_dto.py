"""Full project response DTO."""

from __future__ import annotations

from pydantic import BaseModel

from protopane.adapters.inbound.http.dtos.design_system_ref_dto import DesignSystemRefDTO
from protopane.adapters.inbound.http.dtos.scheme_dto import SchemeDTO
from protopane.adapters.inbound.http.dtos.screen_dto import ScreenDTO
from protopane.adapters.inbound.http.dtos.theme_dto import ThemeDTO

__all__ = ["ProjectDTO"]


class ProjectDTO(BaseModel):
    slug: str
    name: str
    archived: bool = False
    theme: ThemeDTO
    screens: list[ScreenDTO]
    schemes: list[SchemeDTO] = []
    design_system: DesignSystemRefDTO | None = None
