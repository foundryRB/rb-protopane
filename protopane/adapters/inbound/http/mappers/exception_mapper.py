"""Mapping from domain exceptions to HTTP status codes."""

from __future__ import annotations

from protopane.domain.exceptions import (
    BuiltinTemplateError,
    DesignSystemNotFoundError,
    InvalidSlugError,
    InvalidThemeError,
    LastScreenError,
    OffTokenMarkupError,
    ProjectExistsError,
    ProjectNotFoundError,
    SchemeNotFoundError,
    ScreenNotFoundError,
    TemplateNotFoundError,
)

__all__ = ["STATUS_MAP", "DEFAULT_STATUS"]

STATUS_MAP: dict[type[Exception], int] = {
    ProjectNotFoundError: 404,
    DesignSystemNotFoundError: 404,
    SchemeNotFoundError: 404,
    ScreenNotFoundError: 404,
    TemplateNotFoundError: 404,
    ProjectExistsError: 409,
    BuiltinTemplateError: 409,
    LastScreenError: 409,
    OffTokenMarkupError: 422,
    InvalidThemeError: 422,
    InvalidSlugError: 422,
}
DEFAULT_STATUS = 500
