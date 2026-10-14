from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Block:
    """One palette block: named, categorized markup in the token-backed utility
    vocabulary. Blocks are the shared vocabulary every door builds screens from,
    so each one has a real-component counterpart at handoff."""

    slug: str
    label: str
    category: str
    html: str
    preview: str | None = None
