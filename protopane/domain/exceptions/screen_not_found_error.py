"""Raised when a screen slug resolves to nothing within a project."""

from __future__ import annotations

from protopane.domain.exceptions.protopane_error import ProtopaneError

__all__ = ["ScreenNotFoundError"]


class ScreenNotFoundError(ProtopaneError):
    def __init__(self, project_slug: str, screen_slug: str) -> None:
        super().__init__(f"Screen not found: {project_slug}/{screen_slug}")
        self.project_slug = project_slug
        self.screen_slug = screen_slug
