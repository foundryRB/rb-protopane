from __future__ import annotations

from protopane.application.ports.identity_source_library import IdentitySourceLibrary


class ListIdentitySources:
    def __init__(self, library: IdentitySourceLibrary) -> None:
        self._library = library

    def __call__(self) -> list[dict[str, str]]:
        return self._library.list_sources()
