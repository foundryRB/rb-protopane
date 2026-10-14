from __future__ import annotations

from typing import Protocol

from protopane.domain.model.block import Block


class BlockLibrary(Protocol):
    """Outbound port: the palette blocks screens are assembled from."""

    def list_blocks(self) -> list[Block]: ...
