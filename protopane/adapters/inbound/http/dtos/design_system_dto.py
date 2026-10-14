"""Design-system response DTO."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["DesignSystemDTO"]


class DesignSystemDTO(BaseModel):
    slug: str
    name: str
    category: str
    tokens: dict[str, str]
    guidance: str
    source: str
