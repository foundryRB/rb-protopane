from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectSummary:
    """A lightweight project listing entry, without the screen bodies."""

    slug: str
    name: str
    screen_count: int
    archived: bool = False
