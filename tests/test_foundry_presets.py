"""Approved identity values survive projection into the packaged presets and the API."""
from protopane.adapters.outbound.design_systems.packaged_design_system_library import (
    PackagedDesignSystemLibrary,
)
from protopane.domain.token_discipline import lint_theme_tokens


def test_approved_identities_have_distinct_exact_light_and_dark_palettes():
    systems = {s.slug: s for s in PackagedDesignSystemLibrary().list_design_systems()}
    for slug in ("vodafone-digital-engineering",):
        dark, light = systems[slug], systems[slug + "-light"]
        assert not lint_theme_tokens(dark.tokens)
        assert not lint_theme_tokens(light.tokens)
        assert dark.tokens["--background"] != light.tokens["--background"]
        assert dark.tokens["--primary"] == light.tokens["--primary"]
        assert dark.source.startswith("https://")
    assert systems["vodafone-digital-engineering"].tokens["--primary"] == "0.00 100.00% 45.10%"


def test_packaged_presets_are_the_current_projection_of_their_identities():
    """The identities live in this repository (design-systems/); a preset that drifted
    from its identity.json, or an identity with no preset, fails here rather than in a
    consumer."""
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    done = subprocess.run(
        [sys.executable, str(root / "design-systems/generate.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stdout + done.stderr


def test_an_identitys_own_faces_project_inlined_and_only_for_the_families_its_stacks_name(tmp_path):
    """generated/faces.css carries the faces an identity's stacks name, each inlined as a data
    URI so a page that embeds it fetches nothing; a face no stack names stays out, and an
    identity with no faces of its own projects nothing."""
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "design-systems/generate.py"
    spec = importlib.util.spec_from_file_location("generate", path)
    generate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generate)
    identity = {"modes": {
        "dark": {"sans": '"Brand", system-ui, sans-serif', "mono": "ui-monospace, monospace"},
        "light": {"sans": '"Brand", system-ui, sans-serif', "mono": "ui-monospace, monospace"},
    }}
    assert generate.faces_css(identity, tmp_path) == ""
    fonts = tmp_path / "brand" / "fonts"
    fonts.mkdir(parents=True)
    (fonts / "Brand-400.woff2").write_bytes(b"face")
    (fonts / "Other-600.woff2").write_bytes(b"unnamed")
    css = generate.faces_css(identity, tmp_path)
    assert 'font-family:"Brand"' in css and "font-weight:400" in css
    assert 'url("data:font/woff2;base64,ZmFjZQ==")' in css
    assert "Other" not in css and "http" not in css


def test_an_identitys_stage_recipe_renders_both_appearances_and_names_no_other_home():
    """The brand folder's stage recipe is code that ships CSS into other repositories: it must
    import cleanly, paint both appearances over the host it is given, stop for reduced motion and
    print, and carry no path or wording from anywhere but this repository."""
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / (
        "design-systems/vodafone-digital-engineering/brand/stage_css.py"
    )
    spec = importlib.util.spec_from_file_location("stage_css", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    css = module.render_field(host=".ambient", light=':root[data-theme="light"]')
    assert ".ambient > *" in css and ".ambient::before" in css and ".ambient::after" in css
    assert ':root[data-theme="light"] .ambient' in css
    assert "prefers-reduced-motion" in css and "@media print" in css
    assert "#e60000" not in css.lower() or "rgba(230, 0, 0" in css  # the red, never a wash in light
    assert "design-systems/vodafone-digital-engineering/brand/stage_css.py" in css
    for foreign in ("upstream", "_sync", ":/", "fork"):
        assert foreign not in css.lower(), foreign


def test_each_stage_recipe_draws_a_page_stage_behind_content_in_both_appearances():
    """render_page() is what the Press page frames and the deck layout's stage slot embed: an
    aria-hidden element and CSS that keeps it fixed behind content, stops for reduced motion and
    print, pauses on a hidden page, and follows the reader's system appearance. Its markup carries
    no class, so a frame whose own markup says `.stage` and a deck whose chrome classes are
    declared both take it unchanged."""
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "design-systems"
    pages = {}
    for identity in ("vodafone-digital-engineering",):
        recipe = root / identity / "brand/stage_css.py"
        spec = importlib.util.spec_from_file_location(f"stage_{identity}", recipe)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        markup, css = module.render_page()
        assert markup.startswith('<div data-stage="field" aria-hidden="true">'), identity
        assert "class=" not in markup, identity
        flat = css.replace(" ", "")
        assert "position:fixed" in flat and "z-index:-1" in flat, identity
        assert "prefers-reduced-motion" in css and "@media print" in css, identity
        assert 'html[data-hidden="true"] [data-stage]' in css, identity
        pages[identity] = (markup, css)
    markup, css = pages["vodafone-digital-engineering"]
    assert '@media (prefers-color-scheme: light)' in css
    assert ':root:not([data-theme="dark"]) [data-stage="field"]' in css
    # The deck shell's stage: three glows, the grid, eighteen motes and a vignette, sized on the
    # stage's own box so it fills a slide canvas and a browser window alike.
    for layer in ("glow-a", "glow-b", "glow-c", "grid", "motes", "vignette"):
        assert f'data-stage="{layer}"' in markup, layer
    assert markup.split('data-stage="motes">', 1)[1].count("<span></span>") == 18
    assert "container-type:size" in css and "cqw" in css
    assert ":nth-child(18)" in css
    assert '@media print{[data-stage="field"]{display:none!important}}' in css
    still = "{[data-stage],[data-stage] span{animation:none!important}}"
    assert "@media (prefers-reduced-motion: reduce)" + still in css

    # In light only the neutral light slows; glow B keeps the shell's 34s.
    def light_rule(glow: str) -> str:
        light = css.split("@media (prefers-color-scheme: light) {", 1)[1]
        return light.split(f'[data-stage="{glow}"]{{', 1)[1].split("}", 1)[0]

    assert "animation-duration:48s" in light_rule("glow-a")
    assert "animation-duration" not in light_rule("glow-b")


def test_the_mark_is_one_labelled_snippet_whose_artwork_follows_the_appearance():
    """brand/mark.html is what a template's mark slot takes as it is: one element the reader hears
    as the identity's name, sized by the slot's font-size, its tile red on paper and white on a
    dark ground under light-dark(), and nothing it would fetch."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    mark = (root / "design-systems/vodafone-digital-engineering/brand/mark.html").read_text("utf-8")
    assert mark.startswith('<span class="mark" role="img" aria-label="') and mark.count("\n") == 1
    assert "light-dark(#E60000,#f2f4f8)" in mark  # the tile: red on paper, white on the dark stage
    assert "width:2em;height:2em" in mark  # the slot's font-size sizes it
    for fetch in ("http", "url(", "<img", "<link"):
        assert fetch not in mark, fetch
