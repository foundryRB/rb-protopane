from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignSystemRef:
    """The design system a project's identity was seeded from, snapshotted.

    Where `DesignSystem` is the packaged library entry, this is the project's own
    verbatim capture of it at seed time: the guidance text travels WITH the project
    so the handoff export carries the human rationale even if the packaged corpus
    moves on. None on a project means the theme was authored by hand.
    """

    slug: str
    name: str
    guidance: str
