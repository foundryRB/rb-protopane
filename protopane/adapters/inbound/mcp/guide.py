"""The door's guide: the long-form reference an agent authors a prototype from.

The token table renders from the canonical token set the theme gate enforces, and
the block list, with the phone behaviour of each phone block in it, from the
vocabulary `list_blocks` serves, so both say what the instance holds today. The
build flow is one source, rendered here and in the `bootstrap-project` prompt.
"""

from __future__ import annotations

from protopane.domain.constants import DEFAULT_THEME_TOKENS
from protopane.domain.model.block import Block

__all__ = ["CANVAS_WEBFONTS", "render_flow", "render_guide"]

# The families the editor canvas loads as webfonts: the list its font sheet
# requests (FONT_CSS in frontend/src/Editor.tsx), held to it by a test.
CANVAS_WEBFONTS: tuple[str, ...] = (
    "Baloo 2",
    "Fredoka",
    "Nunito",
    "Playfair Display",
    "Poppins",
    "Space Grotesk",
)

# What each canonical token paints. Keyed by token, rendered in canonical order.
_TOKEN_ROLES: dict[str, str] = {
    "--background": "Page surface",
    "--foreground": "Primary text on the page surface",
    "--card": "Card and panel surface",
    "--card-foreground": "Text on a card",
    "--primary": "Brand action colour: primary buttons, links, highlights",
    "--primary-foreground": "Text and icons on the primary colour",
    "--secondary": "Secondary surfaces and secondary buttons",
    "--secondary-foreground": "Text on a secondary surface",
    "--muted": "Low-emphasis surfaces: table headers, placeholders",
    "--muted-foreground": "Captions, hints and other low-emphasis text",
    "--accent": "Hover and selected surfaces",
    "--accent-foreground": "Text on an accent surface",
    "--destructive": "Dangerous actions and errors",
    "--destructive-foreground": "Text on the destructive colour",
    "--border": "Hairlines and dividers (`border-border`, `bg-border`)",
    "--input": "Form field borders",
    "--ring": "Focus rings; usually the primary colour",
    "--radius": "Corner radius, a CSS length",
    "--font-sans": "The typeface: a font-family stack ending in a generic family",
}

_INTRO = """\
# Protopane guide

Protopane is the visual prototyping hub of the design phase. Each customer
engagement is one project: a brand theme plus the screens built against it.
The prototype is a design reference for the real frontend, handed off through
`export_project`: the live theme as a `:root` token block and the screen bodies.
"""

_MODEL = """\
## The model

- **Project**: one customer engagement. Its identity is a slug derived from its
  name, which `create_project` returns and every other tool takes. A project
  holds one live theme, any number of schemes, and at least one screen. It
  starts with the default theme and a starter screen, or from a template.
  `rename_project` changes its name or slug, `archive_project` parks it out of
  the default listing with its data intact, `unarchive_project` brings it back.
- **Theme**: the project's one live look, the full token set below. `save_theme`
  replaces it whole. Seeding it from a packaged design system
  (`get_design_system`) with `design_system=<slug>` records that provenance,
  which the export carries.
- **Scheme**: a named, saved full token set inside the project, which the
  editor applies in one click. Schemes are the palette variants a session
  offers the customer (`save_scheme`, `delete_scheme`).
- **Screen**: one named view, an HTML body plus optional CSS written in
  token-backed utility classes. Its identity is a slug within the project.
  `save_screen` upserts it, `delete_screen` removes it (the last screen stays).
- **Template**: a reusable starting screen, global to the instance: the
  built-in set plus any saved with `save_template`. `create_project` takes a
  template slug to start from one.
"""

_TOKENS_HEAD = """\
## The token set

The set is closed. A theme or a scheme save carries exactly these {count}
tokens: an unknown token is refused, and so is a missing one. A colour token's
value is an `H S% L%` triple with no `hsl()` wrapper, such as `217 91% 60%`;
`--radius` is a CSS length such as `0.5rem`; `--font-sans` is a font-family
stack ending in a generic family such as `sans-serif`. The editor canvas loads
{webfonts} as webfonts, offered as typography presets beside system stacks:
lead the stack with one of them or a system font: any other webfont passes the
gate, but the canvas renders the next family in the stack in its place.
The defaults are the values a new project starts with. A colour an identity needs
beyond this set (success, warning, chart ramps) has no token on the instance.

| Token | Role | Default |
|---|---|---|
"""

_MARKUP = """\
## Markup rules

`save_screen` and `save_template` refuse markup carrying a literal colour, in
the HTML and in the CSS, and answer with a report naming each hit:

- a hex colour: a `#` followed by three to eight hex digits;
- `rgb()` or `rgba()`;
- `hsl()` or `hsla()` with a numeric first argument.

Colour comes from the tokens instead. Every colour token is a Tailwind colour
named after it: `--primary` is `bg-primary`, `text-primary`, `border-primary`,
`ring-primary`, and `--card-foreground` is `text-card-foreground`; opacity
modifiers such as `hover:bg-primary/90` work. `--radius` drives `rounded-lg`
(`rounded-md` and `rounded-sm` a step smaller) and `--font-sans` is `font-sans`.
Layout, spacing and responsive utilities (`flex`, `grid`, `gap-4`, `p-8`,
`sm:grid-cols-2`) carry no colour and are free. In CSS, use a token through
`hsl(var(--primary))`, or `hsl(var(--primary) / 0.9)` with an alpha.

Demo content is markup too. The hex rule reads any `#` followed by three to
eight hex digits as a colour, wherever it sits, and every decimal digit is a hex
digit: an order number `#4821`, a ticket `#A1F3E9` or a hashtag `#cafe` is
refused, and so is `#4821-B`, since `#4821` before the hyphen already reads as
one. Write such a reference without the `#` (`Order 4821`), or with a letter
from `g` to `z` straight after the `#` (`#ORD-4821`, `#T2024-0042`). An HTML
numeric character reference such as `&#10007;` is not a colour.
"""

_PHONE = """\
## Phone layout

The phone line is 640px. Unprefixed utilities are the phone layout; `sm:` is 640px
and up, and `md:` and `lg:` widen it further. Every multi-column grid carries a
breakpoint prefix (`grid-cols-1 sm:grid-cols-3`), never a bare `grid-cols-N` above
one. The editor's Mobile device renders the canvas 390px wide.

A phone layout changes shape below the line: the navigation, tables, forms and the
primary action each take a phone form. Every phone rule is a value, a condition and
a default: "below 640px the nav renders as a bottom bar when there are three to five
sections, otherwise as a sheet menu opened by a summary labelled Menu, closed on
load". Navigation is never hidden without a named replacement, a menu that
replaces it is closed on load, and the primary action stays outside any menu:

| Top-level destinations | Below 640px |
|---|---|
| Four or fewer | Inline, wrapping onto further lines; no menu (`sh-navbar`) |
| Three to five, on an app-like screen | Bottom bar (`sh-bottom-bar`) |
| More than five, or browse-mostly | Sheet menu, two or three links beside it (`sh-sheet-menu`) |
| A deep tree | One level at a time, each with a Back link |

- **Tables**: rows compared across columns stay a `<table>` in a focusable,
  labelled region that scrolls sideways (`sh-table`); standalone records stack as
  one term and description list per record (`sh-stacked-rows`). A `<table>` is
  never stacked with CSS (`block` on its rows and cells): the stacked form is its
  own markup. A table region scrolls sideways; the page never does.
- **Forms**: one column, labels above fields. Inputs, textareas and selects are
  16px below 640px (`text-base sm:text-sm`). The keyboard comes from `type`
  (`email`, `tel`, `url`) or from `type="text"` with `inputmode` (`numeric`,
  `decimal`, `tel`, `email`, `url`, `search`), never `type="number"` for codes and
  references; `autocomplete` on identity, address and payment fields;
  `enterkeyhint` on every field; `spellcheck="false"` on names, emails and
  references (`sh-form`). A form longer than about one and a half screens keeps its
  submit in a pinned action bar (`sh-action-bar`).
- **Touch**: the phone blocks' controls (bottom bar items, sheet links, `sh-form`
  fields) are at least 44px tall below 640px (`min-h-11`, `h-11 sm:h-9`).
- **Viewport**: a full-height shell is `min-h-dvh`, never `h-screen`; a bar fixed to
  the bottom edge pads by `max(<gap>, env(safe-area-inset-bottom))`, and the content
  above it pads by the bar's height.
- **Order**: DOM order is the phone order, main content before supporting content;
  `order-*` and grid placement never reorder it.

Static markup expresses stacking, CSS-only visibility (`sm:hidden`,
`hidden sm:flex`), the scroll-region table, native disclosure (`<details>`,
`<dialog>`, `popover`), input attributes and a pinned bar. A pattern that needs
script (a draggable sheet, a priority-plus menu, a component tree switched by width)
is shown closed, its trigger visible.
"""

# Each phone block's phone behaviour: what changes, at which width, the rule that
# picks it, its default state. Keyed by slug; the guide renders the served ones.
_PHONE_BLOCKS: dict[str, str] = {
    "sh-navbar": (
        "brand, links and action wrap onto further lines wherever one line is too"
        " narrow, so the bar never scrolls sideways at 320px; for four or fewer"
        " destinations; every link shown inline, the action outside the nav."
    ),
    "sh-bottom-bar": (
        "fixed to the bottom edge below 640px and hidden from 640px up (`sm:hidden`),"
        " `calc(4rem + env(safe-area-inset-bottom))` tall and padded by"
        " `max(0.25rem, env(safe-area-inset-bottom))`; below 640px the page's scroll"
        " padding equals the bar's height"
        " (`max-sm:[html:has(&)]:scroll-pb-[calc(4rem+env(safe-area-inset-bottom))]`),"
        " so a focused control never sits under it; for three to five destinations on an"
        " app-like screen, sections only, never actions; every label shown, the current"
        ' destination marked `aria-current="page"`. The screen pads its content by the'
        " bar's height below 640px (`pb-[calc(4rem+env(safe-area-inset-bottom))]"
        " sm:pb-0`) and shows its nav from 640px up (`hidden sm:flex`)."
    ),
    "sh-sheet-menu": (
        "below 640px a `<details>` whose summary reads Menu holds every destination,"
        " the first two kept visible beside it; from 640px up the full nav shows inline"
        " and the menu hides; for more than five destinations or a browse-mostly site;"
        " closed on load, the primary action outside it."
    ),
    "sh-table": (
        'a `<table>` in a region with `role="region"`, `tabindex="0"` and'
        " `aria-labelledby` naming its `<caption>`, scrolling sideways"
        " (`overflow-x-auto`) at any width narrower than its columns, cells on one line"
        " (`whitespace-nowrap`) so the cut column at the edge shows the overflow, the"
        " first column sticky; for rows compared across columns; every column shown."
        " Inside a grid or flex item, that item carries `min-w-0`, so the region scrolls"
        " instead of widening the page."
    ),
    "sh-stacked-rows": (
        "one card per record, a `<dl>` of its fields and a drill-down link; for"
        " standalone records with actions; every field shown. Paired with `sh-table`"
        " for the same records, the rows show below 640px (`sm:hidden`) and the table"
        " from 640px up (`hidden sm:block`)."
    ),
    "sh-form": (
        "one column; fields 16px and 44px tall below 640px, 14px and 36px from 640px up"
        " (`text-base sm:text-sm`, `h-11 sm:h-9`), the submit full width below 640px;"
        " each field with its `type` or `inputmode`, `autocomplete`, `enterkeyhint` and"
        " `spellcheck`; for any form; empty on load."
    ),
    "sh-action-bar": (
        "a form followed in DOM order by a bar fixed to the bottom edge at every width,"
        " `max(5rem, 12svh)` tall and padded by"
        " `max(0.75rem, env(safe-area-inset-bottom))`; the page's scroll padding and"
        " the content's bottom padding equal the bar's height, so a focused field never"
        ' sits under it; its button submits the form through `form="<form id>"`, and'
        " the status line beside it is a polite live region for validation; for a form"
        " longer than about one and a half screens or an action needing constant"
        " access, never inside a sheet; the status line empty on load."
    ),
}

_PHONE_BLOCKS_HEAD = """
Phone behaviour, per block: what changes, at which width, the rule that picks it,
and its default state.

"""

_PHONE_BLOCKS_TAIL = """
An `id` in a block pairs a label or a button with its target (`sh-table`,
`sh-action-bar`): a screen holding two copies gives each its own id.
"""

_BLOCKS_HEAD = """\
## Blocks

Compose screens from the instance's block vocabulary, so every element has a
real shadcn component at handoff. Keep the structure semantic, as the blocks
are (`section`, `nav`, `h1`, `button`, `a`), so the frontend build reads each
element's role from the markup as well as its look. `list_blocks` returns each
block's token-backed markup; the vocabulary by category:

"""

_VARIANTS = """\
## Offering variants

Palette or style variants are schemes inside one project, never a project per
variant. Save every option the customer compares, the current theme's look
included, with `save_scheme` as a full token set; the editor flips between them
in one click. A dark look is one more scheme: a full token set with dark surfaces
and light text that keeps the brand's `--primary` and sets a `--ring` that shows
on them. The live theme stays the one look, and the only one the export carries: to choose a
scheme, save its tokens with `save_theme`.

The instance carries a read-only library of packaged design systems, each a full
token set (it passes the gate as is) plus non-colour guidance: typography,
elevation, voice. `list_design_systems` names each one (slug, name, category);
`get_design_system` reads one by slug with its tokens and guidance. Start a theme
or a variant from one and re-hue it to the customer's brand. Seeding the theme
with `save_theme(..., design_system=<slug>)` records that system on the project
with its guidance, and the export carries it; a later hand-tune keeps the record.
"""

_FLOW_HEAD = """\
## Building a prototype

"""

_FLOW_STEPS = """\
1. `create_project` with {create}; note the returned slug.
2. {theme}
3. `list_blocks`, then author each screen the brief needs as an HTML body
   composed from the blocks and save it with `save_screen`. A new project's
   starter screen is a placeholder: save over its slug, or delete it once a
   screen of your own is saved.
4. `save_scheme` once per palette variant to offer.
5. `export_project` to read the handoff bundle; the editor for the project is
   at `<instance base URL>/p/<slug>`.
"""

_WRITES = """\
A write answers with what it wrote: the saved screen, scheme or theme, a
delete's slug, a project-level write's `list_projects` entry. `get_project` and
`export_project` read the project whole.
"""


def render_flow(create: str, primary: str | None = None) -> str:
    """The build steps, shared by the guide and the `bootstrap-project` prompt.

    `create` is what `create_project` is called with; a `primary` brand colour
    (`#RRGGBB`) folds its conversion into the theme step.
    """
    theme = (
        f"Convert `{primary}` to an `H S% L%` triple for `--primary` and `--ring`,\n"
        "   refine the rest of the token set to the brand, then `save_theme` with the\n"
        "   full set."
        if primary
        else "`save_theme` with the full token set, refined to the brand."
    )
    return _FLOW_STEPS.format(create=create, theme=theme)


def _webfont_list() -> str:
    return ", ".join(CANVAS_WEBFONTS[:-1]) + f" and {CANVAS_WEBFONTS[-1]}"


def _token_rows() -> str:
    return "".join(
        f"| `{token}` | {_TOKEN_ROLES[token]} | `{value}` |\n"
        for token, value in DEFAULT_THEME_TOKENS.items()
    )


def _block_lines(blocks: list[Block]) -> str:
    categories: dict[str, list[Block]] = {}
    for block in blocks:
        categories.setdefault(block.category, []).append(block)
    return "".join(
        f"- **{category}**: " + ", ".join(f"{b.label} (`{b.slug}`)" for b in members) + "\n"
        for category, members in categories.items()
    )


def _phone_block_lines(blocks: list[Block]) -> str:
    served = [b.slug for b in blocks if b.slug in _PHONE_BLOCKS]
    if not served:
        return ""
    return (
        _PHONE_BLOCKS_HEAD
        + "".join(f"- `{slug}`: {_PHONE_BLOCKS[slug]}\n" for slug in served)
        + _PHONE_BLOCKS_TAIL
    )


def render_guide(blocks: list[Block]) -> str:
    """The guide, with the token table and the block list read from their sources."""
    return "\n".join(
        [
            _INTRO,
            _MODEL,
            _TOKENS_HEAD.format(count=len(DEFAULT_THEME_TOKENS), webfonts=_webfont_list())
            + _token_rows(),
            _MARKUP,
            _PHONE,
            _BLOCKS_HEAD + _block_lines(blocks) + _phone_block_lines(blocks),
            _VARIANTS,
            _FLOW_HEAD
            + render_flow("the engagement's name (and a template slug to start from one)")
            + "\n"
            + _WRITES,
        ]
    )
