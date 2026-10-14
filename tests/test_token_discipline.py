"""Token-discipline gate and the served block vocabulary."""

from __future__ import annotations

import re
from html.parser import HTMLParser

from fastapi.testclient import TestClient
from pytest_intent import intent

from protopane.adapters.outbound.blocks.packaged_blocks import PACKAGED_BLOCKS
from protopane.adapters.outbound.persistence.builtin_templates import builtin_templates
from protopane.domain.constants import DEFAULT_THEME_TOKENS
from protopane.domain.token_discipline import lint_markup, lint_theme_tokens


def _project(client: TestClient, name: str = "Gate Co") -> str:
    return client.post("/api/projects", json={"name": name}).json()["slug"]


_VOID = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"}
)


class _Node:
    """One element of a block's markup: its tag, attributes, children and text."""

    def __init__(self, tag: str, attrs: dict[str, str | None], parent: _Node | None) -> None:
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: list[_Node | str] = []

    @property
    def classes(self) -> list[str]:
        return (self.attrs.get("class") or "").split()

    @property
    def elements(self) -> list[_Node]:
        found: list[_Node] = []
        for child in self.children:
            if isinstance(child, _Node):
                found.extend([child, *child.elements])
        return found

    @property
    def child_elements(self) -> list[_Node]:
        return [child for child in self.children if isinstance(child, _Node)]

    def find(self, tag: str) -> list[_Node]:
        return [element for element in self.elements if element.tag == tag]

    def text(self) -> str:
        parts = [child if isinstance(child, str) else child.text() for child in self.children]
        return " ".join("".join(parts).split())

    def within(self, ancestor: _Node) -> bool:
        node = self.parent
        while node is not None and node is not ancestor:
            node = node.parent
        return node is ancestor


class _Markup(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__()
        self.root = _Node("#root", {}, None)
        self._open = self.root
        self.feed(html)
        self.close()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(tag, dict(attrs), self._open)
        self._open.children.append(node)
        if tag not in _VOID:
            self._open = node

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._open.children.append(_Node(tag, dict(attrs), self._open))

    def handle_endtag(self, tag: str) -> None:
        node: _Node | None = self._open
        while node is not None and node.tag != tag:
            node = node.parent
        if node is not None and node.parent is not None:
            self._open = node.parent

    def handle_data(self, data: str) -> None:
        self._open.children.append(data)


def _block(slug: str) -> _Node:
    [block] = [b for b in PACKAGED_BLOCKS if b.slug == slug]
    for markup in (block.html, block.preview or ""):
        assert "<script" not in markup.lower(), slug
        for element in _Markup(markup).root.elements:
            assert not [a for a in element.attrs if a.startswith("on")], (slug, element.tag)
    return _Markup(block.html).root


def _assert_fields(form: _Node) -> None:
    """Each field sits under its label and carries its keyboard and fill attributes."""
    fields = form.find("input")
    assert len(fields) >= 3
    for field in fields:
        label = field.parent
        assert label is not None and label.tag == "label" and "flex-col" in label.classes
        caption, control = label.child_elements
        assert caption.text() and control is field
        kind = field.attrs.get("type")
        assert kind in {"text", "email", "tel", "url", "search"}, kind
        assert field.attrs.get("enterkeyhint"), caption.text()
        if kind == "text":
            assert field.attrs.get("inputmode") or field.attrs.get("autocomplete"), caption.text()
        name_email_or_reference = (
            field.attrs.get("autocomplete") in {"name", "email"}
            or kind == "email"
            or field.attrs.get("inputmode") == "numeric"
        )
        if name_email_or_reference:
            assert field.attrs.get("spellcheck") == "false", caption.text()


def _assert_scroll_region(table: _Node, source: str) -> None:
    """A compared table sits in a focusable region, labelled by the table's caption."""
    region = table.parent
    assert region is not None and region.tag == "div", source
    assert region.attrs.get("role") == "region", source
    assert region.attrs.get("tabindex") == "0", source
    assert "overflow-x-auto" in region.classes, source
    assert "overflow-hidden" not in region.classes, source
    [caption] = table.find("caption")
    assert caption.text(), source
    assert caption.attrs.get("id"), source
    assert region.attrs.get("aria-labelledby") == caption.attrs["id"], source


def _safe_area_padded(bar: _Node) -> bool:
    """A bar at the bottom edge pads by max(<gap>, env(safe-area-inset-bottom))."""
    return any(
        c.startswith("pb-[max(") and c.endswith(",env(safe-area-inset-bottom))]")
        for c in bar.classes
    )


# A form control's tag, its class attribute, and a font-size utility with its variants.
_CONTROL = re.compile(r"<(?:input|textarea|select)\b[^>]*>")
_CLASS_ATTR = re.compile(r'\bclass="([^"]*)"')
_TEXT_SIZE = re.compile(r"^((?:[\w-]+:)*)text-(xs|sm|base|lg|[2-9]?xl)$")
_MIN_WIDTH = re.compile(r"(?:^|:)(?:sm|md|lg|xl|2xl):")


def _phone_text_sizes(control: str) -> list[str]:
    """The font sizes a control takes below 640px: every size not behind a min-width prefix."""
    attr = _CLASS_ATTR.search(control)
    sizes = [_TEXT_SIZE.match(c) for c in (attr.group(1).split() if attr else [])]
    return [m.group(2) for m in sizes if m and not _MIN_WIDTH.search(m.group(1))]


class TestScreenGate:
    @intent("INT-PP-B22")
    def test_hex_in_html_is_rejected_with_report(self, client: TestClient) -> None:
        slug = _project(client)
        res = client.put(
            f"/api/projects/{slug}/screens/home",
            json={"name": "Home", "html": '<div style="background:#1e40af">x</div>', "css": ""},
        )
        assert res.status_code == 422
        assert "#1e40af" in res.json()["detail"]
        assert "token" in res.json()["detail"]

    @intent("INT-PP-B22")
    def test_color_literal_in_css_is_rejected(self, client: TestClient) -> None:
        slug = _project(client)
        res = client.put(
            f"/api/projects/{slug}/screens/home",
            json={"name": "Home", "html": "<div>x</div>", "css": ".x { color: rgb(255,0,0); }"},
        )
        assert res.status_code == 422
        assert "rgb" in res.json()["detail"]

    @intent("INT-PP-B22")
    def test_off_token_template_is_rejected(self, client: TestClient) -> None:
        res = client.post(
            "/api/templates", json={"name": "Bad", "html": '<div style="color:#f00">x</div>'}
        )
        assert res.status_code == 422

    @intent("INT-PP-B22")
    def test_a_hex_shaped_reference_in_demo_content_is_explained(self) -> None:
        """The report says why '#4821' in text read as a color and how to write it;
        the forms it advises pass the gate, and a break after the third hex digit
        does not."""
        [report] = lint_markup("<p>Order #4821</p>", "")
        assert "'#4821'" in report
        assert "three to eight hex digits" in report
        assert "demo content" in report
        assert "'Order 4821'" in report
        assert "a letter from g to z straight after it ('#ORD-4821')" in report
        assert lint_markup("<p>Order 4821, ref #ORD-4821, ticket #T2024-0042</p>", "") == []
        for late_break in ("#482-1", "#4821-B", "#2024-0042"):
            assert lint_markup(f"<p>Ticket {late_break}</p>", ""), late_break

    def test_token_backed_markup_passes(self, client: TestClient) -> None:
        slug = _project(client)
        res = client.put(
            f"/api/projects/{slug}/screens/home",
            json={
                "name": "Home",
                "html": '<section class="p-8"><button class="bg-primary'
                ' text-primary-foreground rounded-md">Go</button></section>',
                "css": ".x { background-color: hsl(var(--primary) / 0.9); }",
            },
        )
        assert res.status_code == 200

    def test_builtin_templates_pass_their_own_gate(self, client: TestClient) -> None:
        """Every shipped template must satisfy the discipline it seeds projects with."""
        for summary in client.get("/api/templates").json():
            template = client.get(f"/api/templates/{summary['slug']}").json()
            assert lint_markup(template["html"], "") == [], summary["slug"]


class TestThemeGate:
    @intent("INT-PP-B23")
    def test_unknown_and_missing_tokens_are_rejected(self, client: TestClient) -> None:
        slug = _project(client)
        tokens = dict(DEFAULT_THEME_TOKENS)
        tokens.pop("--ring")
        tokens["--primry"] = "217 91% 60%"  # typo'd key
        res = client.put(f"/api/projects/{slug}/theme", json={"tokens": tokens})
        assert res.status_code == 422
        detail = res.json()["detail"]
        assert "--primry" in detail
        assert "--ring" in detail

    @intent("INT-PP-B23")
    def test_malformed_values_are_rejected(self, client: TestClient) -> None:
        slug = _project(client)
        tokens = {**DEFAULT_THEME_TOKENS, "--primary": "#1e40af", "--radius": "round"}
        res = client.put(f"/api/projects/{slug}/theme", json={"tokens": tokens})
        assert res.status_code == 422
        detail = res.json()["detail"]
        assert "--primary" in detail
        assert "--radius" in detail

    def test_canonical_set_passes(self, client: TestClient) -> None:
        slug = _project(client)
        res = client.put(f"/api/projects/{slug}/theme", json={"tokens": DEFAULT_THEME_TOKENS})
        assert res.status_code == 200


class TestDeletes:
    @intent("INT-PP-B24")
    def test_delete_screen_removes_and_last_is_refused(self, client: TestClient) -> None:
        slug = _project(client)
        client.put(
            f"/api/projects/{slug}/screens/about",
            json={"name": "About", "html": "<section></section>", "css": ""},
        )
        res = client.delete(f"/api/projects/{slug}/screens/about")
        assert res.status_code == 200
        assert [s["slug"] for s in res.json()["screens"]] == ["home"]
        # The remaining screen is protected.
        assert client.delete(f"/api/projects/{slug}/screens/home").status_code == 409
        assert client.delete(f"/api/projects/{slug}/screens/ghost").status_code == 404

    @intent("INT-PP-B25")
    def test_delete_template_removes_saved_but_not_builtin(self, client: TestClient) -> None:
        saved = client.post(
            "/api/templates", json={"name": "Mine", "html": "<section></section>"}
        ).json()
        assert client.delete(f"/api/templates/{saved['slug']}").status_code == 204
        assert client.get(f"/api/templates/{saved['slug']}").status_code == 404
        assert client.delete("/api/templates/landing").status_code == 409
        assert client.delete("/api/templates/ghost").status_code == 404


class TestBlockVocabulary:
    @intent("INT-PP-B26")
    def test_blocks_are_served_and_self_disciplined(self, client: TestClient) -> None:
        res = client.get("/api/blocks")
        assert res.status_code == 200
        blocks = res.json()
        slugs = {b["slug"] for b in blocks}
        assert {"sh-button", "sh-card", "sh-hero", "sh-pricing", "sh-footer"} <= slugs
        for block in blocks:
            assert lint_markup(block["html"], "") == [], block["slug"]
            if block["preview"]:
                assert lint_markup(block["preview"], "") == [], block["slug"]

    @intent("INT-PP-B39")
    def test_multi_column_grids_stack_at_phone_width(self) -> None:
        # A multi-column grid (a count above one, or an arbitrary track list) stacks
        # at phone width only behind a min-width breakpoint; `dark:` or `max-sm:` is
        # not one. The templates gate theirs behind `sm:`, and blocks follow suit.
        grid = re.compile(r"(?<![\w-])((?:[\w-]+:)*)grid-cols-(\d+|\[[^\]]*\]|none|subgrid)")
        gated = re.compile(r"(?:^|:)(?:sm|md|lg|xl|2xl):")
        for block in PACKAGED_BLOCKS:
            for markup in (block.html, block.preview or ""):
                for prefixes, value in grid.findall(markup):
                    if value in ("1", "none", "subgrid"):
                        continue
                    assert gated.search(prefixes), (block.slug, f"{prefixes}grid-cols-{value}")

    @intent("INT-PP-B43")
    def test_form_controls_are_16px_at_phone_width(self) -> None:
        # Every input, textarea and select takes text-base or larger below 640px; a
        # smaller size sits behind a min-width breakpoint (`text-base sm:text-sm`).
        # The blocks and the built-in templates are both what screens are built from.
        sources = [(b.slug, m) for b in PACKAGED_BLOCKS for m in (b.html, b.preview or "")]
        sources += [(t.slug, t.html) for t in builtin_templates()]
        controls = [(name, c.group(0)) for name, m in sources for c in _CONTROL.finditer(m)]
        assert {name for name, _ in controls} >= {"sh-input", "sh-form", "dashboard", "form"}
        for name, control in controls:
            sizes = _phone_text_sizes(control)
            assert sizes, (name, control)
            assert not {"xs", "sm"} & set(sizes), (name, control)

    def test_packaged_blocks_have_unique_slugs(self) -> None:
        slugs = [b.slug for b in PACKAGED_BLOCKS]
        assert len(slugs) == len(set(slugs))


class TestPhoneBlocks:
    @intent("INT-PP-B40")
    def test_the_navbar_wraps_and_hides_no_link(self) -> None:
        root = _block("sh-navbar")
        [header] = root.find("header")
        [nav] = root.find("nav")
        assert "flex-wrap" in header.classes
        assert "flex-wrap" in nav.classes
        assert [a.text() for a in nav.find("a")] == ["Dashboard", "Projects", "Team"]
        assert not [el.tag for el in root.elements if "hidden" in el.classes]

    @intent("INT-PP-B40")
    def test_the_bottom_bar_pins_three_to_five_destinations_below_640px(self) -> None:
        [nav] = _block("sh-bottom-bar").child_elements
        assert nav.tag == "nav"
        assert {"fixed", "bottom-0", "sm:hidden"} <= set(nav.classes)
        assert _safe_area_padded(nav)
        # Where the bar shows, the page's scroll padding clears its height, so a
        # focused control is never hidden behind it.
        [height] = [c[len("h-[") : -1] for c in nav.classes if c.startswith("h-[")]
        assert "env(safe-area-inset-bottom)" in height
        assert f"max-sm:[html:has(&)]:scroll-pb-[{height}]" in nav.classes
        items = nav.child_elements
        assert 3 <= len(items) <= 5
        for item in items:
            # Equal destinations, each an icon above a one or two word label.
            assert item.tag == "a"
            assert {"flex-1", "flex-col"} <= set(item.classes)
            assert item.child_elements[0].tag == "svg"
            assert 1 <= len(item.text().split()) <= 2

    @intent("INT-PP-B40")
    def test_the_sheet_menu_holds_the_desktop_links_closed_on_load(self) -> None:
        root = _block("sh-sheet-menu")
        [details] = root.find("details")
        assert "open" not in details.attrs
        [summary] = details.find("summary")
        assert summary.text() == "Menu"
        [desktop] = [nav for nav in root.find("nav") if not nav.within(details)]
        assert {"hidden", "sm:flex"} <= set(desktop.classes)
        links = [a.text() for a in desktop.find("a")]
        assert len(links) > 5
        assert [a.text() for a in details.find("a")] == links
        phone = details.parent
        assert phone is not None and "sm:hidden" in phone.classes
        beside = [a.text() for a in phone.find("a") if not a.within(details)]
        assert 2 <= len(beside) <= 3
        assert set(beside) <= set(links)
        [action] = root.find("button")
        assert not action.within(details)

    @intent("INT-PP-B41")
    def test_the_table_scrolls_in_a_labelled_focusable_region(self) -> None:
        [region] = _block("sh-table").child_elements
        [table] = region.child_elements
        assert table.tag == "table"
        _assert_scroll_region(table, "sh-table")

    @intent("INT-PP-B41")
    def test_every_template_table_scrolls_in_a_labelled_focusable_region(self) -> None:
        templates = {t.slug: t.html for t in builtin_templates()}
        tables = [
            (slug, table)
            for slug, html in templates.items()
            for table in _Markup(html).root.find("table")
        ]
        assert {slug for slug, _ in tables} >= {"analytics", "components", "dashboard"}
        for slug, table in tables:
            _assert_scroll_region(table, slug)
            # The label resolves to exactly one element of the screen.
            [caption] = table.find("caption")
            label = caption.attrs["id"]
            assert templates[slug].count(f'id="{label}"') == 1, slug

    @intent("INT-PP-B41")
    def test_stacked_rows_are_one_term_and_description_list_per_record(self) -> None:
        root = _block("sh-stacked-rows")
        assert root.find("table") == []
        records = root.find("li")
        assert len(records) >= 2
        for record in records:
            [terms] = record.find("dl")
            assert len(terms.find("dt")) == len(terms.find("dd")) >= 2

    @intent("INT-PP-B41")
    def test_no_block_or_template_stacks_a_table_with_css(self) -> None:
        parts = {"table", "thead", "tbody", "tfoot", "tr", "th", "td"}
        display = re.compile(
            r"^(?:[\w-]+:)*(?:block|inline-block|flex|inline-flex|grid|inline-grid|contents)$"
        )
        sources = [(b.slug, m) for b in PACKAGED_BLOCKS for m in (b.html, b.preview or "")]
        sources += [(t.slug, t.html) for t in builtin_templates()]
        for name, markup in sources:
            for element in _Markup(markup).root.elements:
                if element.tag in parts:
                    stacked = [c for c in element.classes if display.match(c)]
                    assert not stacked, (name, element.tag, stacked)

    @intent("INT-PP-B42")
    def test_the_form_sets_each_fields_keyboard_and_fill(self) -> None:
        [form] = _block("sh-form").child_elements
        assert form.tag == "form"
        _assert_fields(form)
        fields = {
            f.parent.child_elements[0].text(): f.attrs for f in form.find("input") if f.parent
        }
        assert fields["Full name"]["autocomplete"] == "name"
        assert (fields["Email"]["type"], fields["Email"]["autocomplete"]) == ("email", "email")
        assert (fields["Phone"]["type"], fields["Phone"]["autocomplete"]) == ("tel", "tel")
        assert (fields["Order number"]["type"], fields["Order number"]["inputmode"]) == (
            "text",
            "numeric",
        )

    @intent("INT-PP-B42")
    def test_the_action_bar_follows_its_form_and_clears_the_focused_field(self) -> None:
        [wrapper] = _block("sh-action-bar").child_elements
        form, bar = wrapper.child_elements
        assert (form.tag, bar.tag) == ("form", "div")
        _assert_fields(form)
        assert {"fixed", "bottom-0"} <= set(bar.classes)
        [height] = [c[len("h-[") : -1] for c in bar.classes if c.startswith("h-[")]
        assert "svh" in height
        assert _safe_area_padded(bar)
        # The content and the page's scroll padding both clear the bar's height.
        assert f"pb-[{height}]" in wrapper.classes
        assert f"[html:has(&)]:scroll-pb-[{height}]" in wrapper.classes
        [status] = [el for el in bar.elements if el.attrs.get("aria-live") == "polite"]
        assert status.attrs.get("role") == "status"
        [submit] = bar.find("button")
        assert submit.attrs.get("type") == "submit"
        assert form.attrs.get("id")
        assert submit.attrs.get("form") == form.attrs["id"]


class TestLintUnits:
    def test_lint_allows_token_backed_hsl_var(self) -> None:
        assert lint_markup("", "a { color: hsl(var(--foreground)); }") == []

    def test_lint_flags_numeric_hsl_and_short_hex(self) -> None:
        assert lint_markup('<i style="color:#abc"></i>', "b { color: hsl(20 10% 10%); }")

    def test_theme_lint_accepts_canonical(self) -> None:
        assert lint_theme_tokens(dict(DEFAULT_THEME_TOKENS)) == []

    def test_lint_allows_html_numeric_character_reference(self) -> None:
        # &#10007; (✗) is a glyph, not a color: the `#` is introduced by `&`.
        assert lint_markup('<span class="text-foreground">&#10007;</span>', "") == []

    def test_lint_still_flags_real_hex_after_entity_fix(self) -> None:
        # The entity carve-out must not blind the guard to a genuine hex literal.
        assert lint_markup('<div style="color:#fff"></div>', "") != []
