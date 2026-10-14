"""The read-only design-system library: parsing, the token-discipline gate, and the doors."""

from __future__ import annotations

import asyncio
import base64
import colorsys
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest_intent import intent

from protopane.adapters.inbound.http.mappers.design_system_mapper import design_system_to_dto
from protopane.adapters.inbound.mcp.server import build_mcp_server
from protopane.adapters.outbound.design_systems.design_md_parser import parse_design_md
from protopane.adapters.outbound.design_systems.packaged_design_system_library import (
    PackagedDesignSystemLibrary,
)
from protopane.container import Container
from protopane.domain.constants import DEFAULT_THEME_TOKENS
from protopane.domain.exceptions import DesignSystemNotFoundError
from protopane.domain.token_discipline import lint_theme_tokens

_CANONICAL_KEYS = set(DEFAULT_THEME_TOKENS)

# A known-good sample in the upstream DESIGN.md shape: an H1 title, a Category
# blockquote, a "## 2." swatch section, and a "## 3." typography section.
_SAMPLE = """# Design System Inspired by Acme

> Category: Testing
> A fixed sample for the parser.

## 1. Visual Theme & Atmosphere

Acme is a clean, light system built on a white canvas with one blue brand accent.

## 2. Color Palette & Roles

### Background Surfaces
- **Canvas** (`#ffffff`): The page background and marketing canvas.
- **Panel** (`#f4f4f5`): Card and panel surface, an elevated surface for containers.

### Text & Content
- **Primary Text** (`#0a0a0a`): The default text color, a near-black ink.
- **Secondary Text** (`#6b7280`): Secondary text for metadata, placeholders, and helpers.

### Brand & Accent
- **Brand** (`#2563eb`): Primary action, brand accent, the CTA background fill.
- **Danger** (`#dc2626`): Error and destructive action, a danger red for warnings.

### Border & Divider
- **Divider** (`#e5e7eb`): The border and divider line.

## 3. Typography Rules

### Font Family
- **Primary**: `Inter Variable`, with fallbacks: `system-ui`.
"""


# The corpus's two terser notations: a bold name and a colon before a backticked value,
# and a table row, the name sometimes a backticked custom property.
_COLON_SAMPLE = """# Design System Inspired by Colon

## 2. Color

- **Primary:** `#3B82F6` - Token from style foundations.
- **Secondary:** `#8B5CF6` - Token from style foundations.
- **Danger:** `#DC2626` - Token from style foundations.
- **Surface:** `#FFFFFF` - Token from style foundations.
- **Text:** `#111827` - Token from style foundations.

## 3. Typography
"""

_TABLE_SAMPLE = """# Design System Inspired by Table

## 2. Colors

| Token | Value | Usage |
|---|---|---|
| Background | `#0A0A0A` | Primary canvas |
| Surface | `#111316` | Panels and cards |
| Border | `#1E2328` | Panel separation |
| Primary | `#00FF41` | Active readouts |
| `--fg` | `#E8F0FE` | Primary text |

## 3. Typography
"""

# A system that names only its page and its text, as the cinematic ones do.
_BARE_SAMPLE = """# Design System Inspired by Bare

## 2. Color Palette & Roles

- **Space Black** (`#000000`): Page background, the void.
- **Spectral White** (`#f0f0fa`): Text color, near-white.

## 3. Typography
"""


def _luminance(hsl: str) -> float:
    """WCAG relative luminance of an ``H S% L%`` token."""
    h, sat, light = (float(part) for part in hsl.replace("%", "").split())
    channels = colorsys.hls_to_rgb(h / 360, light / 100, sat / 100)
    r, g, b = (c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(one: str, other: str) -> float:
    high, low = sorted((_luminance(one), _luminance(other)), reverse=True)
    return (high + 0.05) / (low + 0.05)


class TestDesignMdParser:
    @intent("INT-PP-B32")
    def test_parses_a_known_sample_into_the_full_canonical_token_set(self) -> None:
        ds = parse_design_md(_SAMPLE, "acme", "design-systems/acme/DESIGN.md")
        # The whole canonical vocabulary, no more and no less.
        assert set(ds.tokens) == _CANONICAL_KEYS
        assert lint_theme_tokens(ds.tokens) == []
        # Title, category, and source are lifted from the document, slug from the arg.
        assert ds.slug == "acme"
        assert ds.name == "Acme"
        assert ds.category == "Testing"
        assert ds.source == "design-systems/acme/DESIGN.md"
        # A light canvas anchors a light theme; the guidance keeps prose, drops swatches.
        assert ds.tokens["--background"] == "0 0% 100%"
        assert "## 1." in ds.guidance
        assert "## 2." not in ds.guidance
        assert "## 3." in ds.guidance
        assert ds.tokens["--font-sans"] == "Inter, system-ui, sans-serif"

    @intent("INT-PP-B32")
    def test_parses_the_colon_and_table_notations_by_the_roles_they_name(self) -> None:
        colon = parse_design_md(_COLON_SAMPLE, "colon", "x").tokens
        # a lone Surface is the page, Text the foreground, Primary the brand fill
        assert colon["--background"] == "0 0% 100%"
        assert colon["--foreground"] == "221 39% 11%"
        assert colon["--primary"] == "217 91% 60%"
        assert colon["--destructive"] == "0 72% 51%"
        # a saturated Secondary is a brand colour: it lends itself to no surface or border
        assert colon["--secondary"] == "258 90% 66%"
        assert colon["--secondary"] not in (colon["--muted"], colon["--border"], colon["--input"])

        table = parse_design_md(_TABLE_SAMPLE, "table", "x").tokens
        assert table["--background"] == "0 0% 4%"
        assert table["--card"] == "216 13% 8%"
        assert table["--border"] == "210 14% 14%"
        assert table["--primary"] == "135 100% 50%"
        assert table["--foreground"] == "218 92% 95%"

    @intent("INT-PP-B32")
    def test_muted_border_and_input_never_collapse_onto_the_background(self) -> None:
        bare = parse_design_md(_BARE_SAMPLE, "bare", "x").tokens
        assert bare["--background"] == "0 0% 0%"
        for token in ("--muted", "--border", "--input"):
            assert bare[token] != bare["--background"], token


class TestDesignSystemGate:
    @intent("INT-PP-B33")
    def test_every_vendored_system_passes_its_own_gate(self) -> None:
        """Every shipped system must clear the token discipline the live theme clears."""
        systems = PackagedDesignSystemLibrary().list_design_systems()
        assert len(systems) >= 10
        for ds in systems:
            assert set(ds.tokens) == _CANONICAL_KEYS, ds.slug
            assert lint_theme_tokens(ds.tokens) == [], ds.slug

    @intent("INT-PP-B32")
    def test_no_vendored_system_collapses_or_falls_back_to_the_default_set(self) -> None:
        # the parsed systems: the hand-authored ones carry the tokens their owners wrote
        systems = {
            ds.slug: ds.tokens
            for ds in PackagedDesignSystemLibrary().list_design_systems()
            if ds.source.endswith("/DESIGN.md")
        }
        for slug, tokens in systems.items():
            for token in ("--muted", "--border", "--input"):
                assert tokens[token] != tokens["--background"], (slug, token)
        # a page swatch named for the role sets the page: slack's main surface is light
        assert systems["slack"]["--background"] == "0 0% 100%"
        # the systems written in the terser notations seed their own look
        unseeded = parse_design_md("", "none", "x").tokens
        for slug in ("futuristic", "neon", "hud", "mission-control"):
            assert systems[slug]["--background"] != unseeded["--background"] or (
                systems[slug]["--primary"] != unseeded["--primary"]
            ), slug

    @intent("INT-PP-B32")
    def test_every_parsed_system_keeps_its_text_readable_on_its_page(self) -> None:
        """A role taken by name still clears the parser's own readability rule: the
        foreground reaches 3:1 against the background in every parsed system."""
        for ds in PackagedDesignSystemLibrary().list_design_systems():
            if ds.source.endswith("/DESIGN.md"):
                ratio = _contrast(ds.tokens["--foreground"], ds.tokens["--background"])
                assert ratio >= 3, (ds.slug, round(ratio, 2))

    def test_systems_are_sorted_by_slug_and_unique(self) -> None:
        slugs = [d.slug for d in PackagedDesignSystemLibrary().list_design_systems()]
        assert slugs == sorted(slugs)
        assert len(slugs) == len(set(slugs))

    @intent("INT-PP-B34")
    def test_one_system_is_read_by_slug_and_an_unknown_slug_is_refused(
        self, container: Container
    ) -> None:
        """The one lookup get_design_system and save_theme(design_system=...) share."""
        library = container.list_design_systems()
        assert container.get_design_system(library[-1].slug) == library[-1]
        with pytest.raises(DesignSystemNotFoundError, match="no-such-system"):
            container.get_design_system("no-such-system")


class TestDesignSystemDoors:
    @intent("INT-PP-B34")
    def test_http_reads_one_system_whole(
        self, client: TestClient, container: Container
    ) -> None:
        system = container.list_design_systems()[-1]
        response = client.get(f"/api/design-systems/{system.slug}")
        assert response.status_code == 200
        assert response.json() == design_system_to_dto(system).model_dump()

    @intent("INT-PP-B34")
    def test_http_refuses_unknown_system_with_the_reason(self, client: TestClient) -> None:
        response = client.get("/api/design-systems/no-such-system")
        assert response.status_code == 404
        assert "no-such-system" in response.json()["detail"]

    @intent("INT-PP-B34")
    def test_served_read_only_over_http(self, client: TestClient) -> None:
        res = client.get("/api/design-systems")
        assert res.status_code == 200
        systems = res.json()
        assert len(systems) >= 10
        for ds in systems:
            assert set(ds["tokens"]) == _CANONICAL_KEYS, ds["slug"]

    @intent("INT-PP-B34")
    def test_served_read_only_over_mcp(self, container: Container) -> None:
        """The listing names every system; a read by slug returns one whole."""
        server = build_mcp_server(container)
        library = container.list_design_systems()

        async def _drive() -> tuple[set[str], list[dict[str, object]], dict[str, object]]:
            tools = await server.list_tools()
            _content, listing = await server.call_tool("list_design_systems", {})
            _content, system = await server.call_tool(
                "get_design_system", {"slug": library[0].slug}
            )
            return {tool.name for tool in tools}, listing["result"], system

        names, listing, system = asyncio.run(_drive())
        assert {"list_design_systems", "get_design_system"} <= names
        assert listing == [
            {"slug": d.slug, "name": d.name, "category": d.category} for d in library
        ]
        assert system == design_system_to_dto(library[0]).model_dump()
        assert set(system["tokens"]) == _CANONICAL_KEYS


def test_full_identity_sources_keep_authoritative_bytes(client: TestClient) -> None:
    root = Path(__file__).resolve().parents[1] / "design-systems"
    listing = client.get("/api/identity-sources")
    assert listing.status_code == 200
    expected_ids = {p.parent.name for p in root.glob("*/identity.json")}
    assert {item["id"] for item in listing.json()} == expected_ids
    for item in listing.json():
        response = client.get(f"/api/identity-sources/{item['id']}")
        assert response.status_code == 200
        bundle = response.json()
        exported_paths = [entry["path"] for entry in bundle["files"]]
        assert exported_paths == sorted(exported_paths)
        paths = set(exported_paths)
        assert "identity.json" in paths and "generated/mark.html" in paths
        assert not any(path.startswith("brand/") for path in paths)
        for entry in bundle["files"]:
            expected = (root / item["id"] / entry["path"]).read_bytes()
            if Path(entry["path"]).suffix in (".json", ".md", ".css", ".html", ".svg", ".txt"):
                expected = expected.replace(b"\r\n", b"\n")
            assert base64.b64decode(entry["content"]) == expected
        identity = next(entry for entry in bundle["files"] if entry["path"] == "identity.json")
        assert "link" in json.loads(base64.b64decode(identity["content"]))["modes"]["light"]
    assert client.get("/api/identity-sources/no-such-identity").status_code == 404


def test_identity_sources_remain_a_machine_gate_under_oidc() -> None:
    from protopane.adapters.inbound.http.auth import _gated

    assert _gated("/api/identity-sources", "mcp")
    assert _gated("/api/identity-sources/vodafone-digital-engineering", "mcp")
    assert not _gated("/api/design-systems", "mcp")
