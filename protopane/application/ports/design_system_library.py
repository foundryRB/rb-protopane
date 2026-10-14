from __future__ import annotations

from typing import Protocol

from protopane.domain.model.design_system import DesignSystem


class DesignSystemLibrary(Protocol):
    """Outbound port: the read-only catalogue of vendored design systems."""

    def list_design_systems(self) -> list[DesignSystem]: ...

    def get_design_system(self, slug: str) -> DesignSystem:
        """Return the design system, or raise DesignSystemNotFoundError."""
        ...
