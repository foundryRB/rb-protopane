"""Vendor open-design DESIGN.md files into protopane/design_systems_lib/.

Pins nexu-io/open-design at its current main commit and vendors each curated
system's DESIGN.md at that SHA, so the packaged catalogue is reproducible and
serves offline. Re-run to refresh the pin; pass --all to vendor every system in
the upstream corpus (excluding _schema). Requires the GitHub CLI (`gh`),
authenticated.
"""

from __future__ import annotations

import base64
import subprocess
import sys
from pathlib import Path

__all__ = ["main"]

_REPO = "nexu-io/open-design"

# Upstream systems this installation never vendors, whichever set is synced.
_EXCLUDED: frozenset[str] = frozenset({"vodafone"})

# The curated default set: recognisable products with real, well-formed DESIGN.md
# swatch sections. Any that 404 upstream are skipped rather than failing the run.
_CURATED: list[str] = [
    "linear-app",
    "apple",
    "cursor",
    "discord",
    "duolingo",
    "vercel",
    "notion",
    "stripe",
    "github",
    "cal",
    "clickhouse",
    "cohere",
]


def _gh(*args: str) -> bytes:
    """Run a gh command and return its stdout, raising on a non-zero exit."""
    result = subprocess.run(["gh", *args], capture_output=True, check=True)
    return result.stdout


def _main_sha() -> str:
    return _gh("api", f"repos/{_REPO}/commits/main", "--jq", ".sha").decode().strip()


def _all_slugs(sha: str) -> list[str]:
    out = _gh(
        "api",
        f"repos/{_REPO}/contents/design-systems?ref={sha}",
        "--jq",
        '.[] | select(.type == "dir") | .name',
    )
    return [name for name in out.decode().splitlines() if name and name != "_schema"]


def _fetch_design(slug: str, sha: str) -> str | None:
    """Fetch and decode design-systems/<slug>/DESIGN.md at the pinned SHA, or None on 404."""
    try:
        out = _gh(
            "api",
            f"repos/{_REPO}/contents/design-systems/{slug}/DESIGN.md?ref={sha}",
            "--jq",
            ".content",
        )
    except subprocess.CalledProcessError:
        return None
    return base64.b64decode(out.decode().replace("\n", "")).decode("utf-8")


def main() -> None:
    """Vendor the curated set (or every system with --all) at the current main SHA."""
    vendor_all = "--all" in sys.argv[1:]
    root = Path(__file__).resolve().parents[1]
    lib = root / "protopane" / "design_systems_lib"
    lib.mkdir(parents=True, exist_ok=True)

    sha = _main_sha()
    slugs = [s for s in (_all_slugs(sha) if vendor_all else _CURATED) if s not in _EXCLUDED]

    vendored = 0
    for slug in slugs:
        text = _fetch_design(slug, sha)
        if text is None:
            print(f"skip {slug} (no DESIGN.md at {sha[:7]})")
            continue
        dest = lib / slug / "DESIGN.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        vendored += 1
        print(f"vendored {slug}")

    (lib / "PINNED_SHA.txt").write_text(sha + "\n", encoding="utf-8")
    print(f"Vendored {vendored} design systems pinned at {sha}")


if __name__ == "__main__":
    main()
