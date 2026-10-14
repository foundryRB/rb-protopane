from __future__ import annotations

from dataclasses import dataclass

from protopane.domain.model.design_system_ref import DesignSystemRef
from protopane.domain.model.screen import Screen


@dataclass(frozen=True)
class ProjectExport:
    """A project rendered for handoff: the theme as CSS plus the screen bodies,
    and the recorded design-system provenance when the identity was seeded from
    the packaged library (None for a hand-authored theme)."""

    theme_css: str
    screens: list[Screen]
    design_system: DesignSystemRef | None = None
