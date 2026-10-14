"""Raised when a template slug resolves to nothing."""

from __future__ import annotations

from protopane.domain.exceptions.protopane_error import ProtopaneError

__all__ = ["TemplateNotFoundError"]


class TemplateNotFoundError(ProtopaneError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"Template not found: {slug}")
        self.slug = slug
