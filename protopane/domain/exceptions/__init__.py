"""The domain's public errors, re-exported for terse imports."""

from __future__ import annotations

from protopane.domain.exceptions.builtin_template_error import BuiltinTemplateError
from protopane.domain.exceptions.design_system_not_found_error import DesignSystemNotFoundError
from protopane.domain.exceptions.invalid_slug_error import InvalidSlugError
from protopane.domain.exceptions.invalid_theme_error import InvalidThemeError
from protopane.domain.exceptions.last_screen_error import LastScreenError
from protopane.domain.exceptions.off_token_markup_error import OffTokenMarkupError
from protopane.domain.exceptions.project_exists_error import ProjectExistsError
from protopane.domain.exceptions.project_not_found_error import ProjectNotFoundError
from protopane.domain.exceptions.protopane_error import ProtopaneError
from protopane.domain.exceptions.scheme_not_found_error import SchemeNotFoundError
from protopane.domain.exceptions.screen_not_found_error import ScreenNotFoundError
from protopane.domain.exceptions.template_not_found_error import TemplateNotFoundError

__all__ = [
    "ProtopaneError",
    "BuiltinTemplateError",
    "DesignSystemNotFoundError",
    "InvalidSlugError",
    "InvalidThemeError",
    "LastScreenError",
    "OffTokenMarkupError",
    "ProjectExistsError",
    "ProjectNotFoundError",
    "SchemeNotFoundError",
    "ScreenNotFoundError",
    "TemplateNotFoundError",
]
