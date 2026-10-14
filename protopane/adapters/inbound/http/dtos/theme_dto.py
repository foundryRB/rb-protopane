"""Theme response DTO."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["ThemeDTO"]


class ThemeDTO(BaseModel):
    tokens: dict[str, str]
