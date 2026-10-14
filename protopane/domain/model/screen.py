from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Screen:
    """One prototyped screen: a GrapesJS export (html + css) with an identity within a project."""

    slug: str
    name: str
    html: str
    css: str
