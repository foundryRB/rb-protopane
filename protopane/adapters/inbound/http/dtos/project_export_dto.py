"""Handoff export response DTO: the theme as CSS, the screen bodies, and the
recorded design-system provenance (null for a hand-authored theme)."""

from __future__ import annotations

from pydantic import BaseModel

from protopane.adapters.inbound.http.dtos.design_system_ref_dto import DesignSystemRefDTO
from protopane.adapters.inbound.http.dtos.screen_dto import ScreenDTO

__all__ = ["ProjectExportDTO"]


class ProjectExportDTO(BaseModel):
    theme_css: str
    screens: list[ScreenDTO]
    design_system: DesignSystemRefDTO | None = None
