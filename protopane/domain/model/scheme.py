from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Scheme:
    """A named colour scheme saved with a project: a full token set the editor applies in one click.

    Where the project's `theme` is the single live brand, its `schemes` are the palette
    options an engagement pre-configures so the customer can flip between whole looks
    without editing tokens by hand. Identity is the slug within the project.
    """

    slug: str
    name: str
    tokens: dict[str, str] = field(default_factory=dict)
