"""Raised when a project slug resolves to nothing."""

from __future__ import annotations

from protopane.domain.exceptions.protopane_error import ProtopaneError

__all__ = ["ProjectNotFoundError"]


class ProjectNotFoundError(ProtopaneError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"Project not found: {slug}")
        self.slug = slug
