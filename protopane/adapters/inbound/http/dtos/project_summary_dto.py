"""Project listing entry DTO."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["ProjectSummaryDTO"]


class ProjectSummaryDTO(BaseModel):
    slug: str
    name: str
    screen_count: int
    archived: bool = False
