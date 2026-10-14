"""Raised when a target slug is not a well-formed slug."""

from __future__ import annotations

from protopane.domain.exceptions.protopane_error import ProtopaneError

__all__ = ["InvalidSlugError"]


class InvalidSlugError(ProtopaneError):
    def __init__(self, slug: str) -> None:
        super().__init__(
            f"Invalid slug: {slug!r} (a slug is lowercase letters and digits "
            f"separated by single hyphens, e.g. 'acme-v2')"
        )
        self.slug = slug
