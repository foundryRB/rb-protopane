"""Raised when a project slug is already taken."""

from __future__ import annotations

from protopane.domain.exceptions.protopane_error import ProtopaneError

__all__ = ["ProjectExistsError"]


class ProjectExistsError(ProtopaneError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"Project already exists: {slug}")
        self.slug = slug
