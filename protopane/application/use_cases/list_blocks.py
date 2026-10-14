from __future__ import annotations

from protopane.application.ports.block_library import BlockLibrary
from protopane.domain.model.block import Block


class ListBlocks:
    def __init__(self, library: BlockLibrary) -> None:
        self._library = library

    def __call__(self) -> list[Block]:
        return self._library.list_blocks()
