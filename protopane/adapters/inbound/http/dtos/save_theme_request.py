"""Save-theme request body."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["SaveThemeRequest"]


class SaveThemeRequest(BaseModel):
    tokens: dict[str, str]
    # Library slug when the save seeds from a packaged design system: the
    # project records that provenance (guidance snapshotted verbatim).
    design_system: str | None = None
