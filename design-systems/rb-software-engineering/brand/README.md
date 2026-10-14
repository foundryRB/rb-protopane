# Brand pieces: RB Software Engineering

What an identity is besides its palette: the mark and the ground it stands on. `identity.json` (one folder up) holds the colours and type; this folder holds the pieces a stylesheet cannot express as a token.

| File | What | Who takes it |
|---|---|---|
| `lockup.html` | The lockup as inline markup (the RB tile, "Software Engineering / RB"), coloured by the host page's own `--ink`, `--line` and `--muted` | A page that carries the mark in its masthead: a library brief, the workshop frame |
| `lockup-light.svg`, `lockup-dark.svg` | The same lockup as standalone images, text outlined, for light and dark grounds | A docs site's logo, a sign-in page, anything that takes an image |
| `docs.css` | A Starlight docs site in the identity, both appearances: greys, accent and surfaces, set explicitly. Data, not generated: it is the sheet the docs sites already share | A docs site, loaded after the shared docs theme (copy it in; the installation's `@font-face` rules go above it) |
| `stage_css.py` | The ambient ground as a CSS recipe: `render_field()` paints an app's ambient element in both appearances (dark: the stage; light: paper, a faint grid, green motes and a slow neutral light, never a green wash); `render_stage()` rebuilds the same stage out of pseudo-elements for surfaces that take a stylesheet and nothing else; `render_page()` returns the deck shell's own stage (the field, three glows, the green grids and scanlines, eighteen motes, the vignette, as elements sized on their own box) and its CSS, for markup a page or a deck owns, following the reader's appearance | An app shell, a docs site, a home page, a sign-in theme; the Press page frames (plan page, flyer, workshop) and the deck layout's stage slot through `generated/stage.html` and `stage.css` |
| `mark.html` | The lockup as one self-contained snippet for a template's mark slot: the RB tile, a divider, "Software Engineering" over a mono "RB". Its artwork follows the appearance under `light-dark()` (an ink tile on paper, a light one on the dark stage or the brand field), and the slot's `font-size` sets its size | The deck layout's mark slot, through `generated/mark.html` |

## Rules the pieces carry

- **One mark in a header.** The lockup replaces a product's own logo in a masthead; it never sits beside it.
- **The green is `#00a86b`** for accents and fills in both appearances; `#007a4d` (light) and `#4ee0a0` (dark) are for link text. Tints are neutral (a little of the ink over the surface), so nothing turns tinted.
- **The stage is appended, never merged.** `render_field()` returns one block that goes after a stylesheet's own rules. It hides the ambient element's children and paints the element; it edits no component and deletes no rule. Reduced motion and print stop it.

## What is not here

A brand webfont: text uses system font stacks.

## Using the recipe

```
python design-systems/rb-software-engineering/brand/stage_css.py            # writes stage-preview.html beside it
python design-systems/rb-software-engineering/brand/stage_css.py --hooks '["html::before","body::after"]'   # a stage on stdout
```

From Python, import the module by path and call `render_field(host=..., light=..., paper=...)`. The host is the ambient element's selector in the consuming page.
