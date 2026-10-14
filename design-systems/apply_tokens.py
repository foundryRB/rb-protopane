"""Set an app's shadcn token blocks to an identity's approved values.

    python design-systems/apply_tokens.py <index.css> --identity <id>
                                          [--dark <selector>] [--light <selector>] [--check]

The values come from the packaged presets this repository generates from the identity
(protopane/design_systems_lib/<id>/preset.json for Dark, <id>-light for Light), so nothing here
invents a colour. Only variables the stylesheet ALREADY declares inside its two token blocks are
rewritten; `--brand` follows `--primary`, `--brand-ink` its foreground, `--font-sans` the
identity's face. The rest of the file is the app's own and is left alone.

Default selectors are shadcn's layout: `:root` inside `@layer base` is Light, `.dark` is Dark.
An app that is dark by default declares, for example:

    --dark ":root" --light ':root[data-theme="light"]'

`--check` writes nothing and exits non-zero when the stylesheet is stale.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "protopane" / "design_systems_lib"


def fmt(value: str) -> str:
    """'230.00 42.86% 2.75%' -> '230 43% 2.7%': the precision a stylesheet is written in."""
    hue, saturation, lightness = value.replace("%", "").split()
    text = f"{float(hue):.0f} {float(saturation):.0f}% {float(lightness):.1f}%"
    return text.replace(".0%", "%")


def block(text: str, opener: str, tokens: dict) -> tuple[str, int]:
    found = re.search(re.escape(opener) + r"\s*\{", text)
    if not found:
        raise SystemExit(f"no `{opener} {{` block in the stylesheet")
    end = text.index("}", found.end())
    body = text[found.end() : end]
    tokens = dict(tokens)
    tokens["--brand"] = tokens["--primary"]
    tokens["--brand-ink"] = tokens["--primary-foreground"]
    written = 0
    for name, value in tokens.items():
        if name in ("--radius", "--font-sans"):
            continue
        pattern = rf"({re.escape(name)}:\s*)[^;]+;"
        body, count = re.subn(pattern, lambda m, v=value: f"{m.group(1)}{fmt(v)};", body)
        written += count
    return text[: found.end()] + body + text[end:], written


def apply(text: str, identity: str, light: str | None, dark: str) -> tuple[str, dict]:
    report = {}
    for mode, selector in (("light", light), ("dark", dark)):
        preset = LIB / (identity + ("-light" if mode == "light" else "")) / "preset.json"
        tokens = json.loads(preset.read_text(encoding="utf-8"))["tokens"]
        if selector is None:  # shadcn Light: the first `:root {` inside @layer base
            base = re.search(r"@layer base\s*\{\s*:root\s*\{", text)
            if not base:
                raise SystemExit("no `:root {` inside `@layer base` (pass --light)")
            tail, report[mode] = block(text[base.start() :], ":root", tokens)
            text = text[: base.start()] + tail
        else:
            text, report[mode] = block(text, selector, tokens)
        face = tokens.get("--font-sans")
        if face:
            text = re.sub(r"(--font-sans:\s*)[^;]+;", lambda m, f=face: m.group(1) + f + ";", text)
    return text, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("stylesheet", type=Path)
    parser.add_argument("--identity", required=True, help="an identity id under design-systems/")
    parser.add_argument("--light", default=None, help="selector of the Light token block")
    parser.add_argument("--dark", default=".dark", help="selector of the Dark token block")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    # newline="" both ways: the stylesheet keeps whichever line endings its checkout gave it
    with open(args.stylesheet, encoding="utf-8", newline="") as handle:
        before = handle.read()
    after, report = apply(before, args.identity, args.light, args.dark)
    if args.check:
        if after != before:
            raise SystemExit(f"Stale identity tokens: {args.stylesheet}")
        print(f"{args.stylesheet.name}: identity tokens verified")
        return
    with open(args.stylesheet, "w", encoding="utf-8", newline="") as handle:
        handle.write(after)
    print(f"{args.stylesheet.name}: light {report['light']} values, dark {report['dark']} values")


if __name__ == "__main__":
    main()
