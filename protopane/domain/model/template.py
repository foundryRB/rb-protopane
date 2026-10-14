from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Template:
    """A reusable starting screen: a named GrapesJS html layout. Built-in or user-saved."""

    slug: str
    name: str
    html: str
    builtin: bool
