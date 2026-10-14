from __future__ import annotations

from protopane.adapters.outbound.blocks.packaged_blocks import PACKAGED_BLOCKS
from protopane.domain.model.block import Block


class PackagedBlockLibrary:
    """The block vocabulary shipped with the package. Implements BlockLibrary."""

    def list_blocks(self) -> list[Block]:
        return list(PACKAGED_BLOCKS)
