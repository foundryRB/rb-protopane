"""Template listing entry DTO."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["TemplateSummaryDTO"]


class TemplateSummaryDTO(BaseModel):
    slug: str
    name: str
    builtin: bool
