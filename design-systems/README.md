# Design systems

The home of this installation's approved identities: semantic colours, typography, original marks and guidance. ProtoPane is the design hub, so the identities it serves live beside it.

## Source ownership

| Concern | Edit here |
|---|---|
| Palette and typography | `<identity>/identity.json` |
| Brand guidance and original artwork | `<identity>/DESIGN.md` and `<identity>/assets/` |
| The packaged presets ProtoPane serves | generated: `protopane/design_systems_lib/<slug>/preset.json` |
| The same roles as plain CSS variables | generated: `<identity>/generated/<mode>/tokens.css` |
| The mark, the ambient ground, the docs look: what a token cannot express | `<identity>/brand/` (its README lists each piece and who takes it) |
| The identity's own faces, inlined for a page that fetches nothing | generated: `<identity>/generated/faces.css`, from `<identity>/brand/fonts/<Family>-<weight>.woff2` for each family that heads a stack |
| The identity's stage for a page that owns its markup | generated: `<identity>/generated/stage.html` (the ambient element that opens `<body>`) and `stage.css`, from `render_page()` in `<identity>/brand/stage_css.py` |
| The identity's mark, one snippet a template stamps into its masthead slot | generated: `<identity>/generated/mark.html`, from `<identity>/brand/mark.html` |

Run `python design-systems/generate.py` after changing a palette or its guidance (then `python design-systems/apply_tokens.py <app stylesheet> --identity <id>` for each app shell that wears it); `--check` verifies the projections and the asset manifest, and runs in the test suite. Each identity yields two presets, `<id>` (Dark) and `<id>-light`.

## Consumers outside this repository

A preset is a projection for a shadcn token set: it keeps ten of an identity's sixteen roles and converts hex to HSL. Anything that needs the rest (link, good, warn, bad, mono) reads `identity.json` itself, through its own `--palette` argument, at maintenance time:

- the playbook's Press templates: `python scripts/sync_press_palette.py --palette <here>/design-systems/<id>/identity.json`
- the library's shared style: `python scripts/sync_library_style.py --palette <same file>`
- a slide theme's palette block, in the slides app's `slidev-themes/<theme>/style.css`

The Press templates and the library's style embed `generated/faces.css` from beside that `identity.json` when it exists, so their self-contained pages wear the identity's own face. The plan page embeds `generated/stage.html` and `stage.css` the same way, so a plan stands on its identity's stage. `generated/mark.html` is for a template's masthead slot, stamped as it is: the slot sets the mark's size (its `font-size`) and its place, and the snippet carries the rest, its proportions in `em` and its colours and artwork under `light-dark()`, which reads the slot's `color-scheme`: one mark follows both appearances, a slot on a dark ground in either (a deck's close on the brand field) sets `color-scheme: dark`, and an artifact read offline fetches nothing for it.

Updating an identity means regenerating here, then refreshing and releasing each consumer. Artifacts already produced keep their appearance until deliberately regenerated.

## Each installation carries its own

An installation's copy of this repository carries the identities that installation uses, and no others: a copy made for another organization removes the identities that are not its own (the folder here and its two preset folders under `protopane/design_systems_lib/`), and sets each remaining `identity.json`'s `source` to its own library page.

## Brand assets

Original marks keep their geometry; `asset-manifest.json` records each by digest, so a changed or missing asset is a review rather than a silent drift. Licensed fonts are not here: the consuming installation supplies them privately, in its own copy's `<identity>/brand/fonts/`, and themes fall back to system faces when they are absent.

## Source delivery

Authenticated `GET /api/identity-sources` lists approved identity IDs and names.
`GET /api/identity-sources/{id}` returns `{id, name, files}`; each file has a relative
`path`, `encoding: "base64"`, and its byte-exact `content`. The bundle carries
`identity.json`, guidance, generated pieces and assets. Brand recipe code stays in
the hub. `generate.py` projects these bundles into the existing package library,
so both the installed Python package and production image serve the same source.
Consumers fetch a bundle when making work and retain the materialized identity in
that work; an already published artifact keeps its appearance.
