from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignSystem:
    """A read-only reference palette distilled from an open-design DESIGN.md.

    Where a project's `theme` is the live brand and its `schemes` are saved palette
    options, a design system is a shipped, immutable starting point: the upstream
    corpus's prose reduced to the canonical 19-key shadcn `tokens` a project can seed
    from, with the non-color `guidance` kept verbatim so the human rationale survives.
    Identity is the slug within the packaged library.
    """

    slug: str
    name: str
    category: str
    tokens: dict[str, str]
    guidance: str
    source: str
