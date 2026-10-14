"""Palette block response DTO."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["BlockDTO"]


class BlockDTO(BaseModel):
    slug: str
    label: str
    category: str
    html: str
    preview: str | None = None
