"""Named-scheme response DTO."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["SchemeDTO"]


class SchemeDTO(BaseModel):
    slug: str
    name: str
    tokens: dict[str, str]
