from __future__ import annotations

from importlib.resources import files

from protopane.domain.model.template import Template

# (slug, display name) for each built-in template html under protopane/templates_lib/.
_BUILTIN: list[tuple[str, str]] = [
    ("components", "Components"),
    ("landing", "Landing page"),
    ("dashboard", "Dashboard"),
    ("analytics", "Analytics"),
    ("pricing", "Pricing page"),
    ("settings", "Settings page"),
    ("form", "Sign-in form"),
]


def builtin_templates() -> list[Template]:
    base = files("protopane").joinpath("templates_lib")
    templates: list[Template] = []
    for slug, name in _BUILTIN:
        html = base.joinpath(f"{slug}.html").read_text(encoding="utf-8").strip()
        templates.append(Template(slug=slug, name=name, html=html, builtin=True))
    return templates
