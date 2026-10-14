from __future__ import annotations

import json
import re
from importlib.resources import files

from protopane.adapters.outbound.design_systems.design_md_parser import parse_design_md
from protopane.domain.exceptions import DesignSystemNotFoundError
from protopane.domain.model.design_system import DesignSystem


class PackagedDesignSystemLibrary:
    """The design systems vendored with the package. Implements DesignSystemLibrary.

    Each subdirectory of protopane/design_systems_lib/ holding a DESIGN.md is one
    system, parsed on read into the canonical token set. The `_schema` helper dir and
    any directory without a DESIGN.md are skipped.
    """

    def list_design_systems(self) -> list[DesignSystem]:
        base = files("protopane").joinpath("design_systems_lib")
        systems: list[DesignSystem] = []
        for entry in base.iterdir():
            if not entry.is_dir() or entry.name == "_schema":
                continue
            preset = entry.joinpath("preset.json")
            if preset.is_file():
                systems.append(DesignSystem(**json.loads(preset.read_text(encoding="utf-8"))))
                continue
            design = entry.joinpath("DESIGN.md")
            if not design.is_file():
                continue
            text = design.read_text(encoding="utf-8")
            source = f"design-systems/{entry.name}/DESIGN.md"
            systems.append(parse_design_md(text, entry.name, source))
        return sorted(systems, key=lambda system: system.slug)

    def get_design_system(self, slug: str) -> DesignSystem:
        system = next((d for d in self.list_design_systems() if d.slug == slug), None)
        if system is None:
            raise DesignSystemNotFoundError(slug)
        return system

    def list_sources(self) -> list[dict[str, str]]:
        """The full approved identity sources, alongside the existing UI presets."""
        base = files("protopane").joinpath("design_systems_lib")
        result = []
        for folder in base.iterdir():
            source = folder.joinpath("source.json")
            if folder.is_dir() and source.is_file():
                bundle = json.loads(source.read_text(encoding="utf-8"))
                result.append({"id": bundle["id"], "name": bundle["name"]})
        return sorted(result, key=lambda item: item["id"])

    def get_source(self, slug: str) -> dict | None:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
            return None
        source = files("protopane").joinpath("design_systems_lib", slug, "source.json")
        return json.loads(source.read_text(encoding="utf-8")) if source.is_file() else None
