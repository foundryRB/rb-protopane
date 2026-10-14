"""The Software Engineering stage, alive.

`render_page()` draws the deck shell's own stage, its elements and their CSS, for markup
a page or a deck owns: the Press page frames and the deck layout's stage slot. Almost
nothing else on the Foundry lets us add markup: a gethomepage install, a Keycloak theme
and ArgoCD each take a stylesheet and nothing else. So `render_field()` and
`render_stage()` rebuild the same stage out of PSEUDO-ELEMENTS on elements that are
already on the page -- `html::before`, `body::after` and friends -- one per layer.

Layer order, bottom to top, as the shell draws it: gradient, glows, grids and
scanlines, particles, vignette. Pseudo-elements of html and body paint in that
document order among themselves, so handing the hooks over in order is the whole
z-ordering story; every layer is `position: fixed` and `pointer-events: none`, so
the stage never scrolls, never takes a click, and never enters layout.

Fidelity of the pseudo-element rebuild to the shell, and where it deliberately differs:
  - the three glows keep their colours, sizes and 26s/34s/41s tempos, but are sized
    in vw/vh instead of the deck's fixed 980x552 canvas, so they scale to a browser
  - a pseudo-element carries one transform, so glow A rides its own hook and glows
    B and C share the next: two independent drifts rather than three
  - the eighteen motes become two box-shadow fields of nine, each field on its own
    period and phase (a box-shadow list is one element, so a field rises together)
  - motion is transform/opacity only, so every animated layer is composited

Reduced motion and print stop all of it, exactly as the theme does: the resting
state IS the static composition, so those readers get today's look.

    python design-systems/rb-software-engineering/brand/stage_css.py   # writes stage-preview.html
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

BASE_GRADIENT = "linear-gradient(160deg, #0b0d12 0%, #070910 55%, #04050a 100%)"

GLOW_A = "radial-gradient(closest-side, rgba(78, 224, 160,  0.30) 0%, rgba(0, 168, 107,  0.10) 55%, rgba(0, 168, 107,  0) 100%)"
GLOW_B = "radial-gradient(closest-side, rgba(27, 36, 54, 0.85) 0%, rgba(27, 36, 54, 0) 100%)"
GLOW_C = "radial-gradient(closest-side, rgba(0, 168, 107,  0.16) 0%, rgba(0, 168, 107,  0) 100%)"

# vignette first: background layers paint first-listed on top.
# The grid is the shell's own 160px/40px, not the theme's 122.5/30.625: those are
# the same grid scaled down to a 980px slide canvas, and a browser is not one.
STATIC_LAYERS = """radial-gradient(72% 72% at 50% 42%, rgba(0, 0, 0, 0) 55%, rgba(0, 0, 0, 0.55) 100%) 0 0 / cover no-repeat,
    repeating-linear-gradient(rgba(255, 255, 255, 0.022) 0 1px, transparent 1px 4px) 0 0 / auto,
    linear-gradient(to right, rgba(0, 168, 107,  0.13) 1px, transparent 1px) 0 0 / 160px 160px,
    linear-gradient(to bottom, rgba(0, 168, 107,  0.13) 1px, transparent 1px) 0 0 / 160px 160px,
    linear-gradient(to right, rgba(0, 168, 107,  0.07) 1px, transparent 1px) 0 0 / 40px 40px,
    linear-gradient(to bottom, rgba(0, 168, 107,  0.07) 1px, transparent 1px) 0 0 / 40px 40px"""


def _motes(seed: int, count: int = 9, band: int = 0, rgb: str = "255, 107, 107") -> str:
    """One box-shadow field: `count` motes over the lower half, sized and tinted as the theme's.

    The x spread is stratified -- one mote per vertical band, jittered inside it -- because
    uniform sampling clumps, and a clump reads as a blemish rather than as dust. The two
    fields interleave: field 0 takes the odd bands, field 1 the even ones.
    """
    rng = random.Random(seed)
    step = 96 / (count * 2)
    shadows = []
    for i in range(count):
        centre = 3 + step * (2 * i + band)
        x = round(min(96, max(2, centre + rng.uniform(-step * 0.4, step * 0.4))), 1)
        y = round(rng.uniform(58, 99), 1)       # vh: the lower half, where the theme's motes sit
        spread = round(rng.uniform(0, 0.6), 2)  # base dot is 2px, so 2..3.2px like the theme
        alpha = round(rng.uniform(0.43, 0.75), 2)
        shadows.append(f"{x}vw {y}vh 0 {spread}px rgba({rgb}, {alpha})")
    return ",\n    ".join(shadows)


# ── One recipe for every surface that mounts an ambient element ──────────────────────────────────
# The apps, briefs and docs all mount one fixed ambient element and may fill it with a field of
# their own. This identity is CSS alone over that same element, so adopting it never edits a
# component or deletes a rule: the block is APPENDED, after everything else.
#   dark   the stage: gradient + grids + scanlines + vignette on the element, the three glows on
#          ::before (one drift), the motes on ::after
#   light  NOT nothing, and NOT a green wash (red at 8-13% over #F2F2F2 is pink - the operator's eye,
#          2026-09-18): paper, the identity's own faint light grid (its `--grid: rgba(0,122,77,.07)`),
#          solid green motes rising, and a slow NEUTRAL light drifting for depth.
LIGHT_GRID = """linear-gradient(to right, rgba(0, 122, 77,  0.07) 1px, transparent 1px) 0 0 / 160px 160px,
    linear-gradient(to bottom, rgba(0, 122, 77,  0.07) 1px, transparent 1px) 0 0 / 160px 160px,
    linear-gradient(to right, rgba(0, 122, 77,  0.035) 1px, transparent 1px) 0 0 / 40px 40px,
    linear-gradient(to bottom, rgba(0, 122, 77,  0.035) 1px, transparent 1px) 0 0 / 40px 40px"""
LIGHT_GLOW_A = "radial-gradient(closest-side, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0) 100%)"
LIGHT_GLOW_B = "radial-gradient(closest-side, rgba(37, 40, 43, 0.055) 0%, rgba(37, 40, 43, 0) 100%)"


def _light_rules(scope: str, host: str, paper: str) -> str:
    """The light appearance over the ambient element, under `scope` (a selector prefix and its space)."""
    before, after = f"{host}::before", f"{host}::after"
    return f"""{scope}{host} {{
  background:
    {LIGHT_GRID},
    {paper} !important;
}}
{scope}{before} {{
  background:
    {LIGHT_GLOW_A} 8vw 0vh / 70vw 80vh no-repeat,
    {LIGHT_GLOW_B} 58vw 46vh / 80vw 90vh no-repeat !important;
  animation-duration: 48s !important;
}}
{scope}{after} {{
  box-shadow:
    {_motes(11, rgb="0, 168, 107")},
    {_motes(23, band=1, rgb="0, 168, 107")};
}}
"""


def render_field(host: str = ".app-atmosphere", light: str = ':root[data-theme="light"]',
                 dark: str = "", paper: str = "#f2f2f2", note: str = "") -> str:
    """The identity over the ambient element, both appearances, CSS only.

    `light` is the selector prefix under which the surface is in its light appearance
    (`:root[data-theme="light"]`, `:root:not(.dark)`, ...); `dark` optionally scopes the dark rules
    the same way (leave empty when dark is the default). A surface whose light appearance is ALSO
    reached through the OS preference passes that case through `light` as a second call.
    """
    d = (dark + " ") if dark else ""
    scope = light + " "
    before, after = f"{host}::before", f"{host}::after"
    out = [f"""/* ── The Software Engineering stage over the shell's ambient element ─────────────
   Dark: gradient, grids, vignette, three drifting glows, rising motes. Light: paper, the faint
   light grid, solid green motes, a slow neutral light - alive, and never a green wash.
   Source: design-systems/rb-software-engineering/brand/stage_css.py render_field(). {note}
   Appended after the shell's own rules, which stay as they are. Reduced motion and print stop it. */
{host} > * {{ display: none !important; }}                      /* the shell's own streams, blobs, particles */
{d}{host} {{
  position: fixed; inset: 0; z-index: -1; overflow: hidden; pointer-events: none; opacity: 1;
  background:
    {STATIC_LAYERS},
    {BASE_GRADIENT} !important;
}}
{d}{before}, {d}{after} {{ content: "" !important; display: block !important; position: fixed; pointer-events: none; z-index: -1;
  filter: none !important; border-radius: 0; mask: none; }}
{d}{before} {{
  inset: -25vh -25vw; width: auto; height: auto;
  background:
    {GLOW_A} 4vw -5vh / 81vw 95vh no-repeat,
    {GLOW_B} 61vw 50vh / 94vw 105vh no-repeat,
    {GLOW_C} 61vw 3vh / 69vw 75vh no-repeat !important;
  will-change: transform;
  animation: rb-drift-a 26s linear infinite !important;
}}
{d}{after} {{
  inset: 0 auto auto 0; width: 2px; height: 2px; border-radius: 50%; background: none !important;
  box-shadow:
    {_motes(11)},
    {_motes(23, band=1)};
  opacity: 0;
  will-change: transform, opacity;
  animation: rb-rise 15s linear -4s infinite !important;
}}
{_light_rules(scope, host, paper)}@keyframes rb-drift-a {{ 0%, 100% {{ transform: translate(0, 0); }} 33.33% {{ transform: translate(8.6vw, 8.7vh); }} 66.67% {{ transform: translate(-3.9vw, 5.1vh); }} }}
@keyframes rb-rise {{
  0%   {{ transform: translateY(0); opacity: 0; }}
  25%  {{ opacity: 1; }}
  70%  {{ opacity: 1; }}
  100% {{ transform: translateY(-130px); opacity: 0; }}
}}
@media print {{ {host} {{ display: none !important; }} }}
@media (prefers-reduced-motion: reduce) {{ {before}, {after} {{ animation: none !important; }} {after} {{ opacity: .8; }} }}
"""]
    return "\n".join(out)


# ── The shell's own stage, for markup the page owns ─────────────────────────────────────────────
# The deck shell draws its stage on a 980 x 551.25 slide canvas. Every measure below is the
# shell's, divided by that canvas: positions and sizes in % of the stage's box, drifts and the grid
# in container units of it. So the same stage fills a slide canvas or a browser window, and on a
# slide it is the shell's to the pixel.
CANVAS = (980, 551.25)

# name, (left, top, width, height) in canvas px, period in s, two drift waypoints in canvas px,
# the dark paint, the light paint (None: the glow sits out the light appearance)
SHELL_GLOWS = (
    ("glow-a", (-207, -166, 796, 524), 26, ((84, 48), (-38, 28)), GLOW_A, LIGHT_GLOW_A),
    ("glow-b", (353, 138, 918, 578), 34, ((-69, -41), (46, -21)), GLOW_B, LIGHT_GLOW_B),
    ("glow-c", (352, -124, 674, 414), 41, ((-54, 62), (31, 34)), GLOW_C, None),
)

# In light, the neutral light drifts slower than glow A does in the dark; the others keep their tempo.
LIGHT_TEMPO = {"glow-a": 48}

# left, top, diameter in canvas px; period and phase in s; peak opacity
SHELL_MOTES = (
    (90, 475, 2.8, 13, -1.4, .69), (186, 511, 2.1, 17, -6.2, .5), (269, 426, 3.2, 11.5, -3.1, .75),
    (372, 531, 2.3, 15.5, -9, .56), (437, 451, 2.6, 19, -2.2, .63), (511, 500, 2, 12.5, -7.7, .48),
    (568, 416, 3.1, 16, -4.5, .73), (642, 522, 2.4, 14, -11.3, .53), (701, 462, 2.1, 18.5, -.9, .6),
    (769, 505, 2.9, 12, -5.6, .7), (833, 431, 2.3, 20, -8.4, .55), (898, 526, 2.6, 15, -3.7, .65),
    (49, 411, 2, 21, -10.1, .45), (229, 551, 2.8, 13.8, -12.6, .63), (475, 546, 2.1, 17.6, -2.8, .5),
    (735, 559, 2.4, 16.4, -6.9, .58), (942, 482, 2.3, 19.6, -14.2, .54), (329, 475, 2, 22, -1.7, .43),
)
MOTE_RISE = 130  # canvas px
SHELL_SCALE = CANVAS[0] / 1280  # the shell's 160px and 40px grids were drawn 1280 wide

SHELL_GRID = ("repeating-linear-gradient(rgba(255,255,255,.022) 0 1px,transparent 1px 4px),"
              "linear-gradient(to right,rgba(0,168,107,.13) 1px,transparent 1px),"
              "linear-gradient(to bottom,rgba(0,168,107,.13) 1px,transparent 1px),"
              "linear-gradient(to right,rgba(0,168,107,.07) 1px,transparent 1px),"
              "linear-gradient(to bottom,rgba(0,168,107,.07) 1px,transparent 1px)")
SHELL_LIGHT_GRID = ("linear-gradient(to right,rgba(0,122,77,.07) 1px,transparent 1px),"
                    "linear-gradient(to bottom,rgba(0,122,77,.07) 1px,transparent 1px),"
                    "linear-gradient(to right,rgba(0,122,77,.035) 1px,transparent 1px),"
                    "linear-gradient(to bottom,rgba(0,122,77,.035) 1px,transparent 1px)")


def _n(value: float, places: int = 2) -> str:
    """A measure as CSS writes it: `places` decimals at most, no trailing zeros."""
    return f"{round(value, places):g}"


def _x(px: float, places: int = 2) -> str:
    return _n(px / CANVAS[0] * 100, places)


def _y(px: float) -> str:
    return _n(px / CANVAS[1] * 100)


def _shell_light(scope: str) -> str:
    """The light appearance of the shell's stage, under `scope` (a selector prefix and its space)."""
    cell, fine = f"{_x(160 * SHELL_SCALE, 3)}cqw", f"{_x(40 * SHELL_SCALE, 3)}cqw"
    rules = [f'{scope}[data-stage="field"]{{background:none}}',
             f'{scope}[data-stage="grid"]{{background-image:{SHELL_LIGHT_GRID};'
             f"background-size:{cell} {cell},{cell} {cell},{fine} {fine},{fine} {fine}}}",
             f'{scope}[data-stage="motes"]>span{{background:#00a86b}}',
             f'{scope}[data-stage="vignette"]{{display:none}}']
    for name, _, _, _, _, light in SHELL_GLOWS:
        tempo = f";animation-duration:{LIGHT_TEMPO[name]}s" if name in LIGHT_TEMPO else ""
        rules.append(f'{scope}[data-stage="{name}"]{{background:{light.replace(", ", ",")}{tempo}}}' if light
                     else f'{scope}[data-stage="{name}"]{{display:none}}')
    return "\n".join(rules) + "\n"


def render_page() -> tuple[str, str]:
    """The deck shell's own stage for markup the page owns: the element that opens <body> (or a
    deck's stage slot) and its CSS. Dark: the near-black field, three slow glows, two green grids and
    scanlines, eighteen rising motes, a vignette. Light, the system preference or an explicit
    data-theme="light": the paper (the page's own ground shows through), the faint grids, solid red
    motes and a slow neutral light. Print hides it, reduced motion stops it, and a page that marks
    itself html[data-hidden="true"] pauses it."""
    motes = "".join("<span></span>" for _ in SHELL_MOTES)
    glows = "".join(f'<span data-stage="{name}"></span>' for name, *_ in SHELL_GLOWS)
    markup = (f'<div data-stage="field" aria-hidden="true">{glows}<span data-stage="grid"></span>'
              f'<span data-stage="motes">{motes}</span><span data-stage="vignette"></span></div>')

    cell, fine = f"{_x(160 * SHELL_SCALE, 3)}cqw", f"{_x(40 * SHELL_SCALE, 3)}cqw"
    out = ["""/* -- The Software Engineering stage, the deck shell's own --------------------------------------------
   Sized on its own box (positions in %, drifts and the grid in container units), so the same stage
   fills a slide canvas or a browser window. Source: design-systems/rb-software-engineering/
   brand/stage_css.py render_page(). Print hides it, reduced motion stops it, a hidden page pauses it. */""",
           '[data-stage="field"]{position:fixed;inset:0;z-index:-1;overflow:hidden;pointer-events:none;'
           f"container-type:size;background:{BASE_GRADIENT.replace(', ', ',')}}}",
           '[data-stage="field"] [data-stage]{position:absolute;display:block}',
           '[data-stage^="glow"]{border-radius:50%;will-change:transform;'
           "animation-timing-function:linear;animation-iteration-count:infinite}"]
    for name, (left, top, width, height), period, (one, two), dark, _ in SHELL_GLOWS:
        out.append(f'[data-stage="{name}"]{{left:{_x(left)}%;top:{_y(top)}%;width:{_x(width)}%;'
                   f"height:{_y(height)}%;background:{dark.replace(', ', ',')};"
                   f"animation-name:rb-{name};animation-duration:{period}s}}")
        out.append(f"@keyframes rb-{name}{{0%,100%{{transform:translate(0,0)}}"
                   f"33.33%{{transform:translate({_x(one[0])}cqw,{_y(one[1])}cqh)}}"
                   f"66.67%{{transform:translate({_x(two[0])}cqw,{_y(two[1])}cqh)}}}}")
    out.append(f'[data-stage="grid"]{{inset:0;background-image:{SHELL_GRID};'
               f"background-size:auto,{cell} {cell},{cell} {cell},{fine} {fine},{fine} {fine}}}")
    out.append('[data-stage="motes"]{inset:0}')
    out.append('[data-stage="motes"]>span{position:absolute;border-radius:50%;background:#4ee0a0;opacity:0;'
               "will-change:transform,opacity;animation:rb-mote linear infinite}")
    out.append(f"@keyframes rb-mote{{0%{{transform:translateY(0);opacity:0}}25%{{opacity:var(--mote)}}"
               f"70%{{opacity:var(--mote)}}100%{{transform:translateY(-{_y(MOTE_RISE)}cqh);opacity:0}}}}")
    for i, (left, top, size, period, phase, peak) in enumerate(SHELL_MOTES, start=1):
        out.append(f'[data-stage="motes"]>span:nth-child({i}){{left:{_x(left)}%;top:{_y(top)}%;'
                   f"width:{_n(size)}px;height:{_n(size)}px;animation-duration:{_n(period)}s;"
                   f"animation-delay:{_n(phase)}s;--mote:{_n(peak)}}}")
    out.append('[data-stage="vignette"]{inset:0;background:radial-gradient(72% 72% at 50% 42%,'
               "rgba(0,0,0,0) 55%,rgba(0,0,0,.55) 100%)}")
    css = "\n".join(out) + "\n"
    css += _shell_light(':root[data-theme="light"] ')
    css += "@media (prefers-color-scheme: light) {\n" + _shell_light(':root:not([data-theme="dark"]) ') + "}\n"
    css += ('@media print{[data-stage="field"]{display:none!important}}\n'
            "@media (prefers-reduced-motion: reduce){[data-stage],[data-stage] span{animation:none!important}}\n"
            'html[data-hidden="true"] [data-stage],html[data-hidden="true"] [data-stage] span'
            "{animation-play-state:paused!important}\n")
    return markup, css


LAYERS = ("glow_a", "glow_bc", "motes_1", "motes_2", "statics")


def render_stage(hooks: list[str] | dict[str, str], host: str | None = None, note: str = "") -> str:
    """CSS for the stage over `hooks`.

    A list is read as selectors in paint order: five paint the full stage (glow A,
    glows B+C, motes, motes, statics); four fold both glows onto one drift; three
    fold the two mote fields into one.

    A dict assigns layers to hooks by name (`glow_a`, `glow_bc`, `motes_1`,
    `motes_2`, `statics`; only `glow_a`, `motes_1` and `statics` are required) --
    which a surface needs when its own paint order is not the order its hooks come
    in. Pass `host` to have the base gradient painted on an element too (a surface
    whose own background would otherwise cover the layers).
    """
    if isinstance(hooks, dict):
        unknown = set(hooks) - set(LAYERS)
        if unknown:
            raise ValueError(f"unknown stage layers: {sorted(unknown)}")
        missing = {"glow_a", "motes_1", "statics"} - set(hooks)
        if missing:
            raise ValueError(f"the stage needs at least {sorted(missing)}")
        glow_a, glow_bc, motes_1, motes_2, statics = (hooks.get(k) for k in LAYERS)
    elif len(hooks) < 3:
        raise ValueError(f"the stage needs at least 3 hooks, got {len(hooks)}")
    elif len(hooks) >= 5:
        glow_a, glow_bc, motes_1, motes_2, statics = hooks[0], hooks[1], hooks[2], hooks[3], hooks[4]
    elif len(hooks) == 4:
        glow_a, glow_bc, motes_1, motes_2, statics = hooks[0], None, hooks[1], hooks[2], hooks[3]
    else:
        glow_a, glow_bc, motes_1, motes_2, statics = hooks[0], None, hooks[1], None, hooks[2]

    out = [f"""/* ── The Software Engineering stage, alive ──────────────────────────────────────
   The deck shell's stage (gradient, drifting glows, green grids, rising motes,
   vignette) rebuilt on pseudo-elements, since this surface takes a stylesheet and
   no markup. Source: design-systems/rb-software-engineering/brand/stage_css.py. {note}
   Reduced motion and print stop every loop; the resting state is the static stage. */"""]

    if host:
        out.append(f"{host} {{ background: {BASE_GRADIENT} fixed !important; }}")

    used = [h for h in (glow_a, glow_bc, motes_1, motes_2, statics) if h]
    all_hooks = ", ".join(used)

    # A layer sits at z-index -1 so it clears its host's background but stays under its
    # content. That only holds while the host establishes a stacking context: without one
    # the layer escapes to the nearest ancestor that does -- usually the root -- and paints
    # BEHIND its own host's background, i.e. invisibly. html is the root context already;
    # every other host has to be told.
    #
    # `isolation: isolate` and nothing else: it makes a stacking context whatever the host's
    # position is, and touches no layout. Adding `position: relative` here would be worse
    # than useless -- gethomepage's wallpaper element is `position: fixed`, and relative
    # would drop it back into the flow.
    hosts = []
    for hook in used:
        element = hook.split("::")[0].strip()
        # the root element is a stacking context already, however it is qualified
        if element not in hosts and not element.startswith(("html", ":root")):
            hosts.append(element)
    if hosts:
        out.append(f"{', '.join(hosts)} {{ isolation: isolate; }}")
    out.append(f"""{all_hooks} {{
  content: "";
  position: fixed;
  inset: 0;
  z-index: -1;
  pointer-events: none;
}}""")

    # Glows. One transform per element, so glow A rides alone and B+C share a drift.
    # A glow layer is inset NEGATIVELY, 25vw/25vh oversized on every side: a background
    # is clipped to its element, and the drift (8.7vh at most) would otherwise walk the
    # element's own edge into view as a hard rectangle across the glow. The positions
    # below are therefore the on-screen ones plus that 25vw/25vh margin.
    oversize = "  inset: -25vh -25vw;\n"
    if glow_bc:
        out.append(f"""{glow_a} {{
{oversize}  background: {GLOW_A} 4vw -5vh / 81vw 95vh no-repeat;
  will-change: transform;
  animation: rb-drift-a 26s linear infinite;
}}
{glow_bc} {{
{oversize}  background:
    {GLOW_B} 61vw 50vh / 94vw 105vh no-repeat,
    {GLOW_C} 61vw 3vh / 69vw 75vh no-repeat;
  will-change: transform;
  animation: rb-drift-b 34s linear infinite;
}}""")
    else:
        out.append(f"""{glow_a} {{
{oversize}  background:
    {GLOW_A} 4vw -5vh / 81vw 95vh no-repeat,
    {GLOW_B} 61vw 50vh / 94vw 105vh no-repeat,
    {GLOW_C} 61vw 3vh / 69vw 75vh no-repeat;
  will-change: transform;
  animation: rb-drift-a 26s linear infinite;
}}""")

    out.append("@keyframes rb-drift-a { 0%, 100% { transform: translate(0, 0); } 33.33% { transform: translate(8.6vw, 8.7vh); } 66.67% { transform: translate(-3.9vw, 5.1vh); } }")
    if glow_bc:
        out.append("@keyframes rb-drift-b { 0%, 100% { transform: translate(0, 0); } 33.33% { transform: translate(-7vw, -7.4vh); } 66.67% { transform: translate(4.7vw, -3.8vh); } }")

    # Motes: a field is one element, so its nine rise together; the fields differ in
    # period and phase, which is what keeps the whole from reading as a single pulse.
    fields = [(motes_1, 13, 0, 11, 0), (motes_2, 17.5, -6.4, 23, 1)]
    for hook, duration, delay, seed, band in fields:
        if not hook:
            continue
        out.append(f"""{hook} {{
  width: 2px;
  height: 2px;
  inset: 0 auto auto 0;
  border-radius: 50%;
  box-shadow:
    {_motes(seed, band=band)};
  opacity: 0;
  will-change: transform, opacity;
  animation: rb-rise {duration}s linear {delay}s infinite;
}}""")

    out.append(f"""{statics} {{
  background:
    {STATIC_LAYERS};
}}
@keyframes rb-rise {{
  0%   {{ transform: translateY(0); opacity: 0; }}
  25%  {{ opacity: 1; }}
  70%  {{ opacity: 1; }}
  100% {{ transform: translateY(-130px); opacity: 0; }}
}}
/* Every loop is CSS, so these two queries are the whole of the off switch. */
@media print {{
  {all_hooks} {{ animation: none !important; }}
}}
@media (prefers-reduced-motion: reduce) {{
  {all_hooks} {{ animation: none !important; }}
}}""")

    return "\n".join(out) + "\n"


# The hooks each surface can spare. A surface's own pseudo-elements may already be
# taken (home's #page_wrapper carries the lockup), so these are chosen per surface.
HOOKS_FULL = ["html::before", "html::after", "body::before", "body::after"]


def main() -> None:
    # `--hooks '<json>' [--note "..."] [--host sel]` prints a stage to stdout, which is how the
    # non-Python builders (the ArgoCD sheet is a bash script) get their layers.
    if "--hooks" in sys.argv:
        import json
        args = sys.argv
        hooks = json.loads(args[args.index("--hooks") + 1])
        note = args[args.index("--note") + 1] if "--note" in args else ""
        host = args[args.index("--host") + 1] if "--host" in args else None
        # the header rule is drawn with box characters, and a Windows console defaults to
        # cp1252, which cannot encode them
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(render_stage(hooks, host=host, note=note))
        return

    css = render_stage(HOOKS_FULL, host="html", note="Preview build.")
    preview = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>rb stage</title><style>
body {{ margin: 0; min-height: 100vh; font-family: system-ui, sans-serif; color: #f2f4f8; }}
.probe {{ position: relative; padding: 120px 48px; }}
.card {{ background: rgba(255,255,255,.035); border: 1px solid rgba(255,255,255,.10);
        border-radius: 10px; padding: 20px 24px; max-width: 420px; margin-bottom: 14px; }}
h1 {{ font-size: 20px; font-weight: 700; margin: 0 0 6px; }}
p {{ color: #6c7480; font-size: 13px; margin: 0; }}
{css}
</style></head>
<body><div class="probe">
  <div class="card"><h1>RB Foundry</h1><p>The stage, alive, behind glass tiles.</p></div>
  <div class="card"><h1>Software Engineering</h1><p>Glows drift, motes rise, grids hold still.</p></div>
</div></body></html>
"""
    (HERE / "stage-preview.html").write_text(preview, encoding="utf-8", newline="\n")
    print(f"stage.css {len(css)} bytes -> stage-preview.html")


if __name__ == "__main__":
    main()
