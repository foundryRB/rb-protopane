"""Screen response DTO."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["ScreenDTO"]


class ScreenDTO(BaseModel):
    slug: str
    name: str
    html: str
    css: str
