"""Raised when deleting a screen would leave the project empty."""

from __future__ import annotations

from protopane.domain.exceptions.protopane_error import ProtopaneError

__all__ = ["LastScreenError"]


class LastScreenError(ProtopaneError):
    def __init__(self, project_slug: str, screen_slug: str) -> None:
        super().__init__(
            f"Cannot delete '{screen_slug}': a project keeps at least one screen "
            f"(delete the project '{project_slug}' instead)"
        )
        self.project_slug = project_slug
        self.screen_slug = screen_slug
