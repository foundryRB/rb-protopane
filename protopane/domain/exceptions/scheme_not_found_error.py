"""Raised when a scheme slug resolves to nothing within a project."""

from __future__ import annotations

from protopane.domain.exceptions.protopane_error import ProtopaneError

__all__ = ["SchemeNotFoundError"]


class SchemeNotFoundError(ProtopaneError):
    def __init__(self, project_slug: str, scheme_slug: str) -> None:
        super().__init__(f"Scheme not found: {project_slug}/{scheme_slug}")
        self.project_slug = project_slug
        self.scheme_slug = scheme_slug
