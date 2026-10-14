from __future__ import annotations

import re


def slugify(name: str) -> str:
    """Derive a URL-safe slug from a display name. Falls back to 'project' when empty."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "project"
