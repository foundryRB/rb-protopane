from __future__ import annotations

from protopane.application.ports.design_system_library import DesignSystemLibrary
from protopane.domain.model.design_system import DesignSystem


class ListDesignSystems:
    def __init__(self, library: DesignSystemLibrary) -> None:
        self._library = library

    def __call__(self) -> list[DesignSystem]:
        return self._library.list_design_systems()
