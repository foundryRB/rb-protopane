"""Project each approved identity into the files that consume it. Run with --check in CI.

An identity is design-systems/<id>/identity.json: the approved semantic colours and
typography, in Dark and Light. This writes, for every identity and mode:

  protopane/design_systems_lib/<slug>/preset.json   the packaged preset this app serves
  design-systems/<id>/generated/<mode>/tokens.css   the same roles as plain CSS variables

and, for an identity whose brand/fonts/ holds its own faces:

  design-systems/<id>/generated/faces.css           those faces as @font-face rules, inlined

and, for an identity whose brand/stage_css.py draws a stage for a page (render_page):

  design-systems/<id>/generated/stage.html          the ambient element that opens a page's <body>
  design-systems/<id>/generated/stage.css           its paint, both appearances, motion stopped
                                                    for reduced motion and print

and, for an identity whose brand/mark.html carries its mark:

  design-systems/<id>/generated/mark.html           the mark as one self-contained snippet a
                                                    template stamps into its masthead slot

Consumers outside this repository (the Press templates, the library's shared style, a
slide theme's palette block) read identity.json itself, through their own --palette
argument: they need roles a preset does not carry (link, good, warn, mono). Beside it they
find generated/faces.css, generated/stage.{html,css} and generated/mark.html, which a page
that may fetch nothing embeds as they are.
"""
from __future__ import annotations

import argparse
import base64
import colorsys
import hashlib
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIB = ROOT.parent / "protopane" / "design_systems_lib"

# The shadcn token each preset carries, and the identity role it takes its value from.
MAPPING = {
    "background": "canvas", "foreground": "ink", "card": "surface",
    "card-foreground": "ink", "primary": "brand", "primary-foreground": "action-ink",
    "secondary": "raised", "secondary-foreground": "ink", "muted": "raised",
    "muted-foreground": "muted", "accent": "raised", "accent-foreground": "ink",
    "destructive": "bad", "destructive-foreground": "canvas", "border": "line",
    "input": "line", "ring": "focus",
}  # fmt: skip


def identities() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(ROOT.glob("*/identity.json"))]


def hsl(value: str) -> str:
    rgb = [int(value.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    h, lightness, s = colorsys.rgb_to_hls(*rgb)
    return f"{h * 360:.2f} {s * 100:.2f}% {lightness * 100:.2f}%"


def tokens(identity: dict, mode: str) -> dict:
    p = identity["modes"][mode]
    out = {"--" + k: hsl(p[v]) for k, v in MAPPING.items()}
    return out | {"--radius": "0.625rem", "--font-sans": p["sans"]}


def css_tokens(identity: dict, mode: str) -> str:
    roles = "".join(f"--ds-{k}:{v};" for k, v in identity["modes"][mode].items())
    return ":root{" + f"color-scheme:{mode};" + roles + "}\n"


# A face file is named for the family it carries and its weight: Vodafone-400.woff2.
FACE_FILE = re.compile(r"^(?P<family>.+)-(?P<weight>\d{3})\.woff2$")


def faces_css(identity: dict, folder: Path) -> str:
    """The identity's own faces as @font-face rules with the font inlined, for a page that
    may issue no request. Only a family that heads one of the identity's stacks is carried:
    a face no stack names is never drawn. Empty when the identity has no faces of its own,
    and its stacks fall back to the system fonts they name."""
    heads = {
        mode[stack].split(",")[0].strip().strip("\"'")
        for mode in identity["modes"].values()
        for stack in ("sans", "mono")
    }
    rules = []
    for path in sorted((folder / "brand" / "fonts").glob("*.woff2")):
        face = FACE_FILE.match(path.name)
        if face and face["family"] in heads:
            data = base64.b64encode(path.read_bytes()).decode("ascii")
            rules.append(
                f'@font-face{{font-family:"{face["family"]}";font-style:normal;'
                f'font-weight:{face["weight"]};font-display:swap;'
                f'src:url("data:font/woff2;base64,{data}") format("woff2")}}\n'
            )
    return "".join(rules)


def page_stage(folder: Path) -> tuple[str, str] | None:
    """The identity's stage for a page that owns its markup, from its own recipe.

    None for an identity without one."""
    recipe = folder / "brand" / "stage_css.py"
    if not recipe.is_file():
        return None
    spec = importlib.util.spec_from_file_location(f"stage_{folder.name}", recipe)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    render_page = getattr(module, "render_page", None)
    return render_page() if render_page else None


def mark_html(folder: Path) -> str | None:
    """The identity's mark as inline markup, from its brand/mark.html: one snippet a template
    stamps into its masthead slot. The slot sets the size and the place; the snippet carries
    its own proportions, and its colours under light-dark(), which follows the slot's
    color-scheme, so one mark serves both appearances and a page that may fetch nothing.

    None for an identity without one."""
    source = folder / "brand" / "mark.html"
    if not source.is_file():
        return None
    return source.read_text(encoding="utf-8").strip() + "\n"


def outputs() -> dict[Path, str]:
    out = {}
    for identity in identities():
        faces = faces_css(identity, ROOT / identity["id"])
        if faces:
            out[ROOT / identity["id"] / "generated" / "faces.css"] = faces
        stage = page_stage(ROOT / identity["id"])
        if stage:
            out[ROOT / identity["id"] / "generated" / "stage.html"] = stage[0] + "\n"
            out[ROOT / identity["id"] / "generated" / "stage.css"] = stage[1]
        mark = mark_html(ROOT / identity["id"])
        if mark:
            out[ROOT / identity["id"] / "generated" / "mark.html"] = mark
        guidance = (ROOT / identity["id"] / "DESIGN.md").read_text(encoding="utf-8")
        for mode in ("dark", "light"):
            slug = identity["id"] + ("-light" if mode == "light" else "")
            preset = {
                "slug": slug,
                "name": identity["name"] + " / " + mode.title(),
                "category": "Foundry identities",
                "source": identity["source"],
                "tokens": tokens(identity, mode),
                "guidance": guidance,
            }
            out[LIB / slug / "preset.json"] = json.dumps(preset, indent=2) + "\n"
            css = ROOT / identity["id"] / "generated" / mode / "tokens.css"
            out[css] = css_tokens(identity, mode)
    # Full source bundles are mechanical package projections, owned here rather
    # than copied into a consuming engine. A consumer reads one when making work.
    for identity in identities():
        folder = ROOT / identity["id"]
        paths = {folder / "identity.json", folder / "DESIGN.md"}
        paths.update(p for part in ("generated", "assets")
                     for p in (folder / part).rglob("*") if p.is_file())
        paths.update(p for p in out if folder in p.parents)
        entries = []
        for path in sorted(paths, key=lambda path: path.relative_to(folder).as_posix()):
            data = out[path].encode("utf-8") if path in out else path.read_bytes()
            if path.suffix in (".json", ".md", ".css", ".html", ".svg", ".txt"):
                data = data.replace(b"\r\n", b"\n")
            entries.append({"path": path.relative_to(folder).as_posix(),
                            "encoding": "base64",
                            "content": base64.b64encode(data).decode("ascii")})
        out[LIB / identity["id"] / "source.json"] = json.dumps({
            "id": identity["id"], "name": identity["name"], "files": entries,
        }, indent=2) + "\n"
    return out


def manifest() -> str:
    """Original artwork, by digest: a changed or missing asset is a review, not a drift."""
    entries = {}
    for path in sorted(ROOT.glob("*/assets/*")):
        data = path.read_bytes()
        if path.suffix == ".svg":  # text: the digest must not depend on the checkout's line endings
            data = data.replace(b"\r\n", b"\n")
        key = path.relative_to(ROOT).as_posix()
        entries[key] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    return json.dumps(entries, indent=2) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    wanted = outputs() | {ROOT / "asset-manifest.json": manifest()}
    stale = []
    for path, value in wanted.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != value:
                stale.append(path.relative_to(ROOT.parent).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value, encoding="utf-8", newline="\n")
    if stale:
        raise SystemExit("Stale design-system projections: " + ", ".join(stale))
    print("Design system projections " + ("verified" if args.check else "generated"))


if __name__ == "__main__":
    main()
