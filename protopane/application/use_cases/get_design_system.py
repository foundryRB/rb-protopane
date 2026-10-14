from __future__ import annotations

from protopane.application.ports.design_system_library import DesignSystemLibrary
from protopane.domain.model.design_system import DesignSystem


class GetDesignSystem:
    def __init__(self, library: DesignSystemLibrary) -> None:
        self._library = library

    def __call__(self, slug: str) -> DesignSystem:
        return self._library.get_design_system(slug)
