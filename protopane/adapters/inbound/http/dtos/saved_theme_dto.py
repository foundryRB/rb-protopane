"""Saved-theme response DTO: the live tokens and the provenance the project records."""

from __future__ import annotations

from pydantic import BaseModel

from protopane.adapters.inbound.http.dtos.design_system_ref_dto import DesignSystemRefDTO

__all__ = ["SavedThemeDTO"]


class SavedThemeDTO(BaseModel):
    tokens: dict[str, str]
    design_system: DesignSystemRefDTO | None = None
