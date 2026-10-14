"""Raised when a design-system slug resolves to nothing in the packaged library."""

from __future__ import annotations

from protopane.domain.exceptions.protopane_error import ProtopaneError

__all__ = ["DesignSystemNotFoundError"]


class DesignSystemNotFoundError(ProtopaneError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"Design system not found: {slug}")
        self.slug = slug
