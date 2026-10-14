# Fonts

The identity ships no brand webfont: text uses the system font stacks declared in `../../identity.json`.

| File | What |
|---|---|
| `JetBrainsMono-600.woff2` | JetBrains Mono 600 (OFL), the lockup's mono line and identifiers |

`docs-faces.css` holds the `@font-face` rule for it, for a docs site to copy above its theme. `../build_lockup.py` writes `../lockup-light.svg` and `../lockup-dark.svg` with live text, so it needs no font files.
