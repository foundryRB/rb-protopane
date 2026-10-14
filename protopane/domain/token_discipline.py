"""Token discipline: the invariant that makes prototypes portable.

Screens are themed exclusively through the design tokens, so markup and styles
carry no literal colors: a literal never reskins with the brand and breaks at
handoff. These checks are pure domain rules shared by every door (UI, REST,
MCP) through the save use cases.
"""

from __future__ import annotations

import re

from protopane.domain.constants import DEFAULT_THEME_TOKENS

__all__ = ["lint_markup", "lint_theme_tokens"]

# A color literal: hex, rgb()/rgba(), or a numeric hsl()/hsla(). The token-backed
# form hsl(var(--token) / <alpha>) is the one legitimate hsl() and is not matched
# because its first argument is `var`, not a number. A `#` introduced by `&` is an
# HTML numeric character reference (e.g. &#10007; -> ✗), not a color, so it is
# excluded; the hexadecimal form &#x2717; already fails to match because `x` is
# not a hex digit.
_COLOR_LITERAL = re.compile(
    r"(?<!&)#[0-9a-fA-F]{3,8}\b|rgba?\s*\(|hsla?\s*\(\s*[0-9.]",
)

# Canonical token value shapes: an `H S% L%` triple for colors, a CSS length for
# --radius, a font-family stack for --font-sans (family names, quotes, commas).
_HSL_TRIPLE = re.compile(r"^\d+(\.\d+)?\s+\d+(\.\d+)?%\s+\d+(\.\d+)?%$")
_CSS_LENGTH = re.compile(r"^\d+(\.\d+)?(rem|em|px)$")
_FONT_STACK = re.compile(r"^[A-Za-z0-9 ,'\"-]+$")

_CANONICAL_TOKENS = frozenset(DEFAULT_THEME_TOKENS)


def _literals(text: str) -> list[str]:
    return [m.group(0) for m in _COLOR_LITERAL.finditer(text)]


def _html_violation(hit: str) -> str:
    literal = hit.rstrip("(").strip()
    if literal.startswith("#"):
        return (
            f"html carries the color literal '{literal}': a '#' followed by three to eight "
            "hex digits reads as a hex color wherever it sits, demo content included, and "
            "every decimal digit is a hex digit; color with a token-backed utility class "
            "(bg-primary, text-foreground, border), and write a reference such as an order "
            "number without the '#' ('Order 4821') or with a letter from g to z straight "
            "after it ('#ORD-4821')"
        )
    return (
        f"html carries the color literal '{literal}'; "
        "use a token-backed utility class instead (bg-primary, text-foreground, border)"
    )


def lint_markup(html: str, css: str) -> list[str]:
    """Report every color literal in a screen's markup and stylesheet."""
    violations: list[str] = [_html_violation(hit) for hit in _literals(html)]
    violations.extend(
        f"css carries the color literal '{hit.rstrip('(').strip()}'; "
        "use hsl(var(--token)) so the rule reskins with the theme"
        for hit in _literals(css)
    )
    return violations


def lint_theme_tokens(tokens: dict[str, str]) -> list[str]:
    """Report every deviation from the canonical token set.

    The theme replaces the project's whole token set, so a save must carry every
    canonical token (a partial set would silently drop brand values), no unknown
    keys (a typo would silently style nothing), and well-formed values.
    """
    violations: list[str] = [
        f"unknown token '{key}'; the canonical set is the shadcn tokens"
        for key in sorted(set(tokens) - _CANONICAL_TOKENS)
    ]
    violations.extend(
        f"missing token '{key}'; send the full token set"
        for key in sorted(_CANONICAL_TOKENS - set(tokens))
    )
    for key in sorted(_CANONICAL_TOKENS & set(tokens)):
        value = tokens[key].strip()
        if key == "--radius":
            if not _CSS_LENGTH.match(value):
                violations.append(
                    f"token '{key}' must be a CSS length such as '0.5rem', got '{value}'"
                )
        elif key == "--font-sans":
            if not value or not _FONT_STACK.match(value):
                violations.append(
                    f"token '{key}' must be a font-family stack such as "
                    f"'Georgia, serif', got '{value}'"
                )
        elif not _HSL_TRIPLE.match(value):
            violations.append(
                f"token '{key}' must be an 'H S% L%' triple such as '217 91% 60%', got '{value}'"
            )
    return violations
