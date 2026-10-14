from __future__ import annotations

from protopane.application.ports.identity_source_library import IdentitySourceLibrary
from protopane.domain.exceptions import DesignSystemNotFoundError


class GetIdentitySource:
    def __init__(self, library: IdentitySourceLibrary) -> None:
        self._library = library

    def __call__(self, slug: str) -> dict:
        source = self._library.get_source(slug)
        if source is None:
            raise DesignSystemNotFoundError(slug)
        return source
