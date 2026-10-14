"""Create-project request body."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["CreateProjectRequest"]


class CreateProjectRequest(BaseModel):
    name: str
    template: str | None = None
