"""Render the RB lockup as self-contained SVGs.

The lockup is the RB tile, a hairline divider, "Software Engineering" over a tracked
mono "RB". The text is live, in system font stacks, so no licensed face or font
tooling is needed. Writes lockup-light.svg and lockup-dark.svg beside this file:

    python design-systems/rb-software-engineering/brand/build_lockup.py
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
SANS = "system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def lockup(dark: bool) -> str:
    ink, muted, line = ("#f2f4f8", "#a8b0bd", "#353b47") if dark else ("#25282b", "#6c7480", "#d9d9d9")
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 268 48" role="img" aria-label="Software Engineering, RB">'
        f'<rect x="2.5" y="2.5" width="43" height="43" rx="7" fill="none" stroke="{ink}" stroke-width="3.2"/>'
        f'<text x="24" y="31" text-anchor="middle" font-family="{SANS}" font-size="18" font-weight="800" fill="{ink}">RB</text>'
        f'<line x1="60" y1="8" x2="60" y2="40" stroke="{line}" stroke-width="1"/>'
        f'<text x="72" y="23" font-family="{SANS}" font-size="15" font-weight="700" letter-spacing="0.8" fill="{ink}">Software Engineering</text>'
        f'<text x="72" y="38" font-family="{MONO}" font-size="9.5" font-weight="600" letter-spacing="2.2" fill="{muted}">RB</text></svg>\n'
    )


def main() -> None:
    (HERE / "lockup-light.svg").write_text(lockup(dark=False), encoding="utf-8", newline="\n")
    (HERE / "lockup-dark.svg").write_text(lockup(dark=True), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
