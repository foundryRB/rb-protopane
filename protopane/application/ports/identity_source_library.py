from __future__ import annotations

from typing import Protocol


class IdentitySourceLibrary(Protocol):
    """Read-only approved identity source projections owned by the hub."""

    def list_sources(self) -> list[dict[str, str]]: ...

    def get_source(self, slug: str) -> dict | None: ...
