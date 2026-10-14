"""Raised when a built-in template is targeted by a delete."""

from __future__ import annotations

from protopane.domain.exceptions.protopane_error import ProtopaneError

__all__ = ["BuiltinTemplateError"]


class BuiltinTemplateError(ProtopaneError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"Template '{slug}' is built-in and cannot be deleted")
        self.slug = slug
