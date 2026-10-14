"""Rename-project request body."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["RenameProjectRequest"]


class RenameProjectRequest(BaseModel):
    new_slug: str | None = None
    new_name: str | None = None
