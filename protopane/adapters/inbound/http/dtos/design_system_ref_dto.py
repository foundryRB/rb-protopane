"""The design-system provenance a project recorded at seed time."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["DesignSystemRefDTO"]


class DesignSystemRefDTO(BaseModel):
    slug: str
    name: str
    guidance: str
