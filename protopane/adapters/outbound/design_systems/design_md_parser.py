"""Parse an open-design DESIGN.md into a canonical shadcn DesignSystem.

The upstream corpus documents each system as prose plus a "## 2. Color Palette &
Roles" section of named swatches. This pure function distils that section into the
19-key shadcn token set every protopane door speaks, keyword-scoring each swatch
against each role and coercing every color to the canonical `H S% L%` triple, while
keeping the non-color guidance (sections 1 and 3 onward) verbatim.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from protopane.domain.model.design_system import DesignSystem

__all__ = ["parse_design_md"]

_ENTRY_RE = re.compile(r"^-\s*\*\*(.+?)\*\*\s*\(([^)]*)\)\s*:?\s*(.*)$")
# The corpus's two other swatch notations: a bold name and a colon before a backticked
# value (`- **Primary:** `#3B82F6` - use`), and a table row (`| Background | `#0A0A0A` | use |`,
# the name sometimes a backticked custom property such as `--bg-base`).
_COLON_ENTRY_RE = re.compile(r"^-\s*\*\*(.+?):?\*\*:?\s*`([^`]*)`[^\w`]*(.*)$")
_ROW_RE = re.compile(r"^\|\s*`?([^|`]+?)`?\s*\|\s*`?(#[0-9a-fA-F]{3,6})`?\s*\|(.*)$")
_NOTATIONS = (_ENTRY_RE, _COLON_ENTRY_RE, _ROW_RE)
_HEX_RE = re.compile(r"#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}\b")
_SECTION_2 = re.compile(r"^##\s+2\.", re.MULTILINE)
_SECTION_3 = re.compile(r"^##\s+3\.", re.MULTILINE)
_SECTION_ANY = re.compile(r"^##\s+\d", re.MULTILINE)
_H1_RE = re.compile(r"^#\s+(.*)$", re.MULTILINE)
_CATEGORY_RE = re.compile(r"^>\s*Category:\s*(.+)$", re.MULTILINE)
_PRIMARY_FONT_RE = re.compile(r"Primary[^`\n]*`([^`]+)`")
_FONT_DISALLOWED = re.compile(r"[^A-Za-z0-9 ,'\"-]")
_WHITESPACE = re.compile(r"\s+")

_RADIUS = "0.625rem"
_DEFAULT_FONT = "Inter, system-ui, sans-serif"

# Keyword sets, one per assignable role. A keyword carrying a space scores 2, a bare
# keyword scores 1. Keys match the assignable base-token names (no `--` prefix).
_KEYWORDS: dict[str, list[str]] = {
    "background": [
        "page background",
        "marketing",
        "canvas",
        "main light surface",
        "background",
        "base surface",
    ],
    "card": ["card", "panel", "elevated surface", "container", "supporting surface", "surface"],
    "primary": ["primary action", "action fill", "brand accent", "cta", "brand", "action"],
    "secondary": ["secondary surface", "utility layer", "secondary"],
    "muted": ["muted", "subtle surface", "hover state", "tertiary surface"],
    "accent": ["accent", "selection", "highlight", "link", "interactive"],
    "destructive": ["error", "destructive", "danger", "warning", "red"],
    "border": ["border", "divider", "outline", "stroke", "line"],
    "foreground": ["primary text", "default text", "near-black ink", "ink", "foreground"],
    "muted-foreground": [
        "secondary text",
        "tertiary text",
        "secondary copy",
        "helper",
        "metadata",
        "placeholder",
        "de-emphasized",
        "neutral gray",
    ],
    "input": ["input", "field outline", "form", "field"],
    "ring": ["focus", "selection signal", "ring", "selected-state"],
}

# Word-boundary patterns so a keyword scores only as a whole word: "ink" must not
# match inside "link", "line" not inside "underline", "action" not inside "interaction".
_KEYWORD_PATTERNS: dict[str, list[tuple[re.Pattern[str], int]]] = {
    token: [(re.compile(rf"\b{re.escape(kw)}\b"), 2 if " " in kw else 1) for kw in keywords]
    for token, keywords in _KEYWORDS.items()
}

_SURFACE_TOKENS = frozenset({"card", "secondary", "muted"})
_TEXT_TOKENS = frozenset({"foreground", "muted-foreground"})

# Roles claim their swatch greedily in this order (background is chosen first,
# separately, to anchor the mode): brand fills, then the text roles, then structural
# roles, then the surfaces last. Text before surfaces is what lets `muted-foreground`
# claim the mid gray ink before a surface token can (step e), and keeps a text gray
# out of `card`/`secondary`/`muted`.
_ASSIGN_ORDER = [
    "primary",
    "accent",
    "destructive",
    "foreground",
    "muted-foreground",
    "border",
    "input",
    "ring",
    "card",
    "secondary",
    "muted",
]

# The terse notations name the role itself (`Primary`, `Surface`, `Text`, `--border`): a
# swatch named exactly for a role takes it ahead of any keyword score, where the role's
# readability rule allows it. A `Surface` with no `Background` beside it is the page.
_ROLE_NAMES: dict[str, str] = {
    "background": "background",
    "bg": "background",
    "bg primary": "background",
    "surface": "card",
    "text": "foreground",
    "text primary": "foreground",
    "fg": "foreground",
    "foreground": "foreground",
    "primary": "primary",
    "secondary": "secondary",
    "accent": "accent",
    "border": "border",
    "danger": "destructive",
    "error": "destructive",
    "destructive": "destructive",
}

_Rgb = tuple[int, int, int]


class _Entry(NamedTuple):
    name: str
    rgb: _Rgb
    text: str
    lum: float


def parse_design_md(text: str, slug: str, source: str) -> DesignSystem:
    """Distil one DESIGN.md into a DesignSystem with the full canonical token set."""
    entries = _entries(_color_section(text))
    base = _assign(entries)
    tokens = _finalize(base)
    tokens["--radius"] = _RADIUS
    tokens["--font-sans"] = _font(text)
    return DesignSystem(
        slug=slug,
        name=_name(text, slug),
        category=_category(text),
        tokens=tokens,
        guidance=_guidance(text),
        source=source,
    )


def _color_section(text: str) -> str:
    sec2, sec3 = _SECTION_2.search(text), _SECTION_3.search(text)
    if sec2 and sec3 and sec2.start() < sec3.start():
        return text[sec2.end() : sec3.start()]
    return ""


def _entries(section: str) -> list[_Entry]:
    out: list[_Entry] = []
    for line in section.splitlines():
        stripped = line.strip()
        match = next((m for rx in _NOTATIONS if (m := rx.match(stripped))), None)
        if match is None:
            continue
        rgb = _parse_hex(match.group(2))
        if rgb is None:
            continue
        name, desc = match.group(1).strip(), match.group(3).replace("|", " ").strip()
        if name.startswith("--"):
            name = name[2:].replace("-", " ")
        out.append(
            _Entry(name=name, rgb=rgb, text=f"{name} {desc}".lower(), lum=_luminance(rgb))
        )
    return out


def _parse_hex(value: str) -> _Rgb | None:
    match = _HEX_RE.search(value)
    if match is None:
        return None
    digits = match.group(0)[1:]
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    return int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16)


def _luminance(rgb: _Rgb) -> float:
    r, g, b = rgb
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def _is_dark(rgb: _Rgb) -> bool:
    return _luminance(rgb) < 0.5


def _score(text: str, token: str) -> int:
    return sum(weight for pattern, weight in _KEYWORD_PATTERNS[token] if pattern.search(text))


def _allowed(token: str, entry: _Entry, mode: str) -> bool:
    if token in _SURFACE_TOKENS:
        return entry.lum >= 0.42 if mode == "light" else entry.lum <= 0.58
    if token in _TEXT_TOKENS:
        return entry.lum < 0.5 if mode == "light" else entry.lum > 0.5
    if token == "destructive":
        r, g, b = entry.rgb
        return r > g + 25 and r > b + 25
    return True


def _assign(entries: list[_Entry]) -> dict[str, _Rgb | None]:
    """Score every swatch against every role and hand each role its best free swatch."""
    base: dict[str, _Rgb | None] = dict.fromkeys(_KEYWORDS)
    if not entries:
        return base

    used: set[int] = set()
    named: dict[str, int] = {}
    for i, entry in enumerate(entries):
        role = _ROLE_NAMES.get(entry.name.lower().removeprefix("color ").strip())
        if role is not None:
            named.setdefault(role, i)

    # Background anchors the mode: the swatch named for it, else the highest-scoring
    # background swatch, else a lone `Surface`, else the darkest by luminance when no
    # swatch names the background at all.
    bg_scored = [(_score(e.text, "background"), i) for i, e in enumerate(entries)]
    best_bg = max(score for score, _ in bg_scored)
    if "background" in named:
        bg_i = named.pop("background")
    elif best_bg > 0:
        bg_i = max(range(len(entries)), key=lambda i: (_score(entries[i].text, "background"), -i))
    elif "card" in named:
        bg_i = named.pop("card")
    else:
        bg_i = min(range(len(entries)), key=lambda i: (entries[i].lum, i))
    base["background"] = entries[bg_i].rgb
    used.add(bg_i)
    mode = "light" if entries[bg_i].lum >= 0.5 else "dark"
    for role, i in named.items():
        if i not in used and _allowed(role, entries[i], mode):
            base[role] = entries[i].rgb
            used.add(i)

    for token in _ASSIGN_ORDER:
        if base[token] is not None:
            continue
        prefer_gray = token == "muted-foreground"
        # Rank free, allowed, positive-scoring swatches by (mid-gray, score, earliest).
        # muted-foreground alone prefers a genuine mid gray so it reads as one (step e).
        ranked: list[tuple[int, int, int]] = []
        for i, entry in enumerate(entries):
            if i in used or not _allowed(token, entry, mode):
                continue
            score = _score(entry.text, token)
            if score <= 0:
                continue
            gray = 1 if (prefer_gray and 0.30 < entry.lum < 0.70) else 0
            ranked.append((gray, score, -i))
        if not ranked:
            continue
        best_i = -max(ranked)[2]
        base[token] = entries[best_i].rgb
        used.add(best_i)
    return base


def _is_neutral(rgb: _Rgb) -> bool:
    return max(rgb) - min(rgb) <= 40


def _mix(rgb: _Rgb, toward: _Rgb, share: float) -> _Rgb:
    r, g, b = (round(a + (t - a) * share) for a, t in zip(rgb, toward, strict=True))
    return r, g, b


def _contrast(rgb: _Rgb) -> _Rgb:
    return (250, 250, 250) if _is_dark(rgb) else (10, 10, 10)


def _finalize(base: dict[str, _Rgb | None]) -> dict[str, str]:
    """Fill any unassigned role from a coherent fallback, then emit HSL triples."""
    bg = base["background"] or (255, 255, 255)
    dark = _is_dark(bg)
    fg = base["foreground"] or ((250, 250, 250) if dark else (10, 10, 10))
    primary = base["primary"] or fg
    card = base["card"] or bg

    secondary = base["secondary"] or base["muted"] or card
    # A saturated secondary is a brand colour, not a surface: it never becomes the muted
    # surface, nor through it every border.
    muted = base["muted"] or (secondary if _is_neutral(secondary) else None) or card
    accent = base["accent"] or primary
    border = base["border"] or muted or card
    input_ = base["input"] or border or card
    ring = base["ring"] or accent or primary
    destructive = base["destructive"] or (220, 38, 38)
    muted_fg = base["muted-foreground"] or fg
    # A system that names none of these leaves them on the background, where a hairline or
    # an input's edge cannot be seen: step them toward the text instead.
    if muted == bg:
        muted = _mix(bg, fg, 0.06)
    if border == bg:
        border = _mix(bg, fg, 0.18)
    if input_ == bg:
        input_ = border

    colors: dict[str, _Rgb] = {
        "--background": bg,
        "--foreground": fg,
        "--card": card,
        "--card-foreground": fg,
        "--primary": primary,
        "--primary-foreground": _contrast(primary),
        "--secondary": secondary,
        "--secondary-foreground": fg,
        "--muted": muted,
        "--muted-foreground": muted_fg,
        "--accent": accent,
        "--accent-foreground": _contrast(accent),
        "--destructive": destructive,
        "--destructive-foreground": _contrast(destructive),
        "--border": border,
        "--input": input_,
        "--ring": ring,
    }
    return {token: _hsl_triple(rgb) for token, rgb in colors.items()}


def _hsl_triple(rgb: _Rgb) -> str:
    r, g, b = (channel / 255 for channel in rgb)
    high, low = max(r, g, b), min(r, g, b)
    lightness = (high + low) / 2
    if high == low:
        hue = saturation = 0.0
    else:
        delta = high - low
        saturation = delta / (2 - high - low) if lightness > 0.5 else delta / (high + low)
        if high == r:
            hue = (g - b) / delta + (6 if g < b else 0)
        elif high == g:
            hue = (b - r) / delta + 2
        else:
            hue = (r - g) / delta + 4
        hue /= 6
    return f"{round(hue * 360)} {round(saturation * 100)}% {round(lightness * 100)}%"


def _name(text: str, slug: str) -> str:
    match = _H1_RE.search(text)
    if match is not None:
        title = match.group(1).strip()
        marker = "Inspired by "
        if marker in title:
            return title.split(marker, 1)[1].strip()
        if title:
            return title
    return slug.replace("-", " ").title()


def _category(text: str) -> str:
    match = _CATEGORY_RE.search(text)
    return match.group(1).strip() if match is not None else ""


def _font(text: str) -> str:
    sec3 = _SECTION_3.search(text)
    if sec3 is not None:
        rest = text[sec3.end() :]
        following = _SECTION_ANY.search(rest)
        scope = rest[: following.start()] if following is not None else rest
    else:
        scope = text
    match = _PRIMARY_FONT_RE.search(scope)
    if match is None:
        return _DEFAULT_FONT
    font = re.sub(r"(?i)variable", "", match.group(1))
    font = _FONT_DISALLOWED.sub("", font)
    font = _WHITESPACE.sub(" ", font).strip().strip(",").strip()
    if not font:
        return _DEFAULT_FONT
    if "," not in font:
        font = f"{font}, system-ui, sans-serif"
    return font


def _guidance(text: str) -> str:
    sec2, sec3 = _SECTION_2.search(text), _SECTION_3.search(text)
    if sec2 and sec3 and sec2.start() < sec3.start():
        return (text[: sec2.start()] + text[sec3.start() :]).strip()
    return text.strip()
