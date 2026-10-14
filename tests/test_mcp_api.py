"""MCP integration tests: a real server exercised through the protocol client."""

from __future__ import annotations

import re
import socket
import threading
import time
from pathlib import Path
from types import TracebackType
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import uvicorn
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.exceptions import McpError
from mcp.types import CallToolResult, TextContent
from pytest_intent import intent

from protopane.adapters.inbound.mcp.guide import CANVAS_WEBFONTS, render_guide
from protopane.adapters.outbound.blocks.packaged_blocks import PACKAGED_BLOCKS

EXPECTED_TOOLS = {
    "list_projects",
    "create_project",
    "get_project",
    "delete_project",
    "rename_project",
    "archive_project",
    "unarchive_project",
    "save_theme",
    "save_scheme",
    "delete_scheme",
    "save_screen",
    "delete_screen",
    "export_project",
    "list_templates",
    "get_template",
    "save_template",
    "delete_template",
    "list_blocks",
}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def mcp_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated dirs, auth disabled, no SPA dist (overridable per test)."""
    monkeypatch.setenv("PROTOPANE_PROJECTS_DIR", str(tmp_path / "projects"))
    monkeypatch.setenv("PROTOPANE_TEMPLATES_DIR", str(tmp_path / "templates"))
    monkeypatch.setenv("PROTOPANE_FRONTEND_DIST", str(tmp_path / "no-dist"))
    monkeypatch.setenv("PROTOPANE_AUTH_DISABLED", "true")
    monkeypatch.delenv("PROTOPANE_MCP_ALLOWED_HOSTS", raising=False)
    return tmp_path


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class _Server:
    """Uvicorn on an ephemeral port, running the app for the test's duration."""

    def __init__(self) -> None:
        from protopane.adapters.inbound.http.app import create_app

        port = _free_port()
        config = uvicorn.Config(create_app(), host="127.0.0.1", port=port, log_level="warning")
        self.base_url = f"http://127.0.0.1:{port}"
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    def __enter__(self) -> _Server:
        self._thread.start()
        deadline = time.monotonic() + 15
        while not self._server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("test server failed to start")
            time.sleep(0.05)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=10)


async def _tool_names(base_url: str) -> set[str]:
    async with (
        streamable_http_client(f"{base_url}/mcp") as (read, write, _),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        tools = await session.list_tools()
        return {tool.name for tool in tools.tools}


class TestMcpSurface:
    @intent("INT-PP-B21")
    @pytest.mark.anyio
    async def test_tools_mirror_the_wired_use_cases(self, mcp_env: Path) -> None:
        with _Server() as srv:
            names = await _tool_names(srv.base_url)
        assert names >= EXPECTED_TOOLS

    @pytest.mark.anyio
    async def test_read_tool_returns_persisted_content(self, mcp_env: Path) -> None:
        with _Server() as srv:
            async with (
                streamable_http_client(f"{srv.base_url}/mcp") as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                result = await session.call_tool("list_templates", {})
        assert not result.isError
        assert "landing" in str(result.content)

    @pytest.mark.anyio
    async def test_rejected_operation_carries_the_reason(self, mcp_env: Path) -> None:
        with _Server() as srv:
            async with (
                streamable_http_client(f"{srv.base_url}/mcp") as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                result = await session.call_tool("get_project", {"slug": "no-such-project"})
        assert result.isError
        assert "Project not found: no-such-project" in str(result.content)


class TestMcpSameDoor:
    @intent("INT-PP-B22")
    @pytest.mark.anyio
    async def test_off_token_markup_is_rejected_on_the_mcp_door_too(self, mcp_env: Path) -> None:
        """The token-discipline gate lives in the use case, so MCP saves hit it."""
        with _Server() as srv:
            async with (
                streamable_http_client(f"{srv.base_url}/mcp") as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                await session.call_tool("create_project", {"name": "Gate Co"})
                result = await session.call_tool(
                    "save_screen",
                    {
                        "slug": "gate-co",
                        "screen_slug": "home",
                        "name": "Home",
                        "html": '<div style="background:#1e40af">off-brand</div>',
                    },
                )
        assert result.isError
        assert "#1e40af" in str(result.content)

    @intent("INT-PP-B20")
    @pytest.mark.anyio
    async def test_mcp_write_is_read_back_by_the_http_api(self, mcp_env: Path) -> None:
        """A screen saved through the MCP door is the screen the REST API reads back."""
        with _Server() as srv:
            async with (
                streamable_http_client(f"{srv.base_url}/mcp") as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                created = await session.call_tool("create_project", {"name": "Mcp Co"})
                assert not created.isError
                saved = await session.call_tool(
                    "save_screen",
                    {
                        "slug": "mcp-co",
                        "screen_slug": "pricing",
                        "name": "Pricing",
                        "html": '<section class="p-8">Saved via MCP</section>',
                    },
                )
                assert not saved.isError
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{srv.base_url}/api/projects/mcp-co")
        assert res.status_code == 200
        screens = {s["slug"]: s for s in res.json()["screens"]}
        assert screens["pricing"]["html"] == '<section class="p-8">Saved via MCP</section>'

    @intent("INT-PP-B29")
    @pytest.mark.anyio
    async def test_mcp_rename_detaches_the_old_slug(self, mcp_env: Path) -> None:
        """A slug renamed through the MCP door stops answering at the old slug on
        every other door: the stale-prototype detach the tool exists for."""
        with _Server() as srv:
            async with (
                streamable_http_client(f"{srv.base_url}/mcp") as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                created = await session.call_tool("create_project", {"name": "Live Repo"})
                assert not created.isError
                renamed = await session.call_tool(
                    "rename_project",
                    {"slug": "live-repo", "new_slug": "live-repo-v1-design"},
                )
                assert not renamed.isError
            async with httpx.AsyncClient() as client:
                old = await client.get(f"{srv.base_url}/api/projects/live-repo")
                new = await client.get(f"{srv.base_url}/api/projects/live-repo-v1-design")
        assert old.status_code == 404
        assert new.status_code == 200

    @intent("INT-PP-B27")
    @pytest.mark.anyio
    async def test_named_schemes_save_read_and_delete_through_mcp(self, mcp_env: Path) -> None:
        """Schemes are a full-token-set project operation on the MCP door too: a canonical
        set saves and is enumerable via get_project, a non-canonical set is refused with the
        report, and deleting one removes it, all through the same use cases as the HTTP API."""
        with _Server() as srv:
            async with httpx.AsyncClient() as client:
                async with (
                    streamable_http_client(f"{srv.base_url}/mcp") as (read, write, _),
                    ClientSession(read, write) as session,
                ):
                    await session.initialize()
                    created = await session.call_tool("create_project", {"name": "Scheme Co"})
                    assert not created.isError
                    # The canonical set to save as a scheme is the project's own default theme.
                    tokens = (
                        await client.get(f"{srv.base_url}/api/projects/scheme-co")
                    ).json()["theme"]["tokens"]

                    saved = await session.call_tool(
                        "save_scheme",
                        {
                            "slug": "scheme-co",
                            "scheme_slug": "candy",
                            "name": "Candy",
                            "tokens": tokens,
                        },
                    )
                    assert not saved.isError

                    # A partial / non-canonical set is refused with the report, like the theme.
                    bad = await session.call_tool(
                        "save_scheme",
                        {
                            "slug": "scheme-co",
                            "scheme_slug": "broken",
                            "name": "Broken",
                            "tokens": {"--primary": "10 20% 30%"},
                        },
                    )
                    assert bad.isError
                    assert "Theme rejected" in str(bad.content)

                    # get_project enumerates the saved scheme so an agent can list it.
                    fetched = await session.call_tool("get_project", {"slug": "scheme-co"})
                    assert not fetched.isError
                    assert "candy" in str(fetched.content)

                    # Deleting removes it; deleting an unknown scheme is an error.
                    deleted = await session.call_tool(
                        "delete_scheme", {"slug": "scheme-co", "scheme_slug": "candy"}
                    )
                    assert not deleted.isError
                    missing = await session.call_tool(
                        "delete_scheme", {"slug": "scheme-co", "scheme_slug": "candy"}
                    )
                    assert missing.isError
                    assert "Scheme not found" in str(missing.content)

                # The scheme write took the shared path: the HTTP door agrees it is gone.
                remaining = (
                    await client.get(f"{srv.base_url}/api/projects/scheme-co")
                ).json()["schemes"]
        assert remaining == []


def _answer(result: CallToolResult) -> dict[str, object]:
    """A successful tool call's structured answer."""
    assert not result.isError, result.content
    assert result.structuredContent is not None
    return result.structuredContent


def _slugs(records: object) -> set[object]:
    """The slugs of the records an answer lists."""
    assert isinstance(records, list)
    return {record["slug"] for record in records}


class TestMcpWriteAnswers:
    """A write answers with what it wrote; the project whole is a read's answer."""

    @intent("INT-PP-B37")
    @pytest.mark.anyio
    async def test_per_item_writes_answer_with_the_item_they_wrote(self, mcp_env: Path) -> None:
        bulk = '<section class="p-8">' + "elsewhere " * 2000 + "</section>"
        with _Server() as srv:
            async with (
                streamable_http_client(f"{srv.base_url}/mcp") as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                _answer(await session.call_tool("create_project", {"name": "Answer Co"}))
                project = {"slug": "answer-co"}
                _answer(
                    await session.call_tool(
                        "save_screen",
                        {**project, "screen_slug": "bulky", "name": "Bulky", "html": bulk},
                    )
                )

                screen = _answer(
                    await session.call_tool(
                        "save_screen",
                        {
                            **project,
                            "screen_slug": "pricing",
                            "name": "Pricing",
                            "html": '<section class="p-8">Pricing</section>',
                        },
                    )
                )
                assert screen == {
                    "slug": "pricing",
                    "name": "Pricing",
                    "html": '<section class="p-8">Pricing</section>',
                    "css": "",
                }

                whole = _answer(await session.call_tool("get_project", project))
                theme = whole["theme"]
                assert isinstance(theme, dict)
                tokens = theme["tokens"]

                scheme = _answer(
                    await session.call_tool(
                        "save_scheme",
                        {**project, "scheme_slug": "candy", "name": "Candy", "tokens": tokens},
                    )
                )
                assert scheme == {"slug": "candy", "name": "Candy", "tokens": tokens}

                hand = _answer(await session.call_tool("save_theme", {**project, "tokens": tokens}))
                assert hand == {"tokens": tokens, "design_system": None}
                seeded = _answer(
                    await session.call_tool(
                        "save_theme", {**project, "tokens": tokens, "design_system": "shadcn"}
                    )
                )
                assert set(seeded) == {"tokens", "design_system"}
                assert seeded["tokens"] == tokens
                provenance = seeded["design_system"]
                assert isinstance(provenance, dict)
                assert provenance["slug"] == "shadcn"
                assert provenance["guidance"]
                tuned = _answer(
                    await session.call_tool("save_theme", {**project, "tokens": tokens})
                )
                assert tuned["design_system"] == seeded["design_system"]

                removed_scheme = _answer(
                    await session.call_tool("delete_scheme", {**project, "scheme_slug": "candy"})
                )
                assert removed_scheme == {"deleted": "candy"}

                # The reads still return the project whole, the bulky screen included.
                whole = _answer(await session.call_tool("get_project", project))
                assert _slugs(whole["screens"]) >= {"bulky", "pricing"}
                exported = _answer(await session.call_tool("export_project", project))
                assert _slugs(exported["screens"]) >= {"bulky", "pricing"}

                removed_screen = _answer(
                    await session.call_tool("delete_screen", {**project, "screen_slug": "bulky"})
                )
                assert removed_screen == {"deleted": "bulky"}
        # No write answer carried the other screen's body.
        for answer in (screen, scheme, hand, seeded, tuned, removed_scheme, removed_screen):
            assert "elsewhere" not in str(answer)

    @intent("INT-PP-B37")
    @pytest.mark.anyio
    async def test_project_level_writes_answer_with_the_listing_entry(self, mcp_env: Path) -> None:
        with _Server() as srv:
            async with (
                streamable_http_client(f"{srv.base_url}/mcp") as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()

                async def entry(slug: str) -> dict[str, object]:
                    listing = _answer(
                        await session.call_tool("list_projects", {"include_archived": True})
                    )
                    projects = listing["result"]
                    assert isinstance(projects, list)
                    return next(p for p in projects if p["slug"] == slug)

                _answer(await session.call_tool("create_project", {"name": "Entry Co"}))
                renamed = _answer(
                    await session.call_tool(
                        "rename_project",
                        {"slug": "entry-co", "new_slug": "entry-co-v2", "new_name": "Entry Two"},
                    )
                )
                assert renamed == await entry("entry-co-v2")
                assert renamed == {
                    "slug": "entry-co-v2",
                    "name": "Entry Two",
                    "screen_count": 1,
                    "archived": False,
                }

                archived = _answer(
                    await session.call_tool("archive_project", {"slug": "entry-co-v2"})
                )
                assert archived == await entry("entry-co-v2")
                assert archived["archived"] is True

                revived = _answer(
                    await session.call_tool("unarchive_project", {"slug": "entry-co-v2"})
                )
                assert revived == await entry("entry-co-v2")
                assert revived["archived"] is False


class TestMcpDesignSystemReads:
    """The listing names each system; the read of one by slug returns it whole."""

    @intent("INT-PP-B34")
    @pytest.mark.anyio
    async def test_the_listing_names_each_system_and_a_read_returns_one_whole(
        self, mcp_env: Path
    ) -> None:
        with _Server() as srv:
            async with (
                streamable_http_client(f"{srv.base_url}/mcp") as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                listing = _answer(await session.call_tool("list_design_systems", {}))
                system = _answer(await session.call_tool("get_design_system", {"slug": "shadcn"}))
                missing = await session.call_tool("get_design_system", {"slug": "no-such-system"})
            async with httpx.AsyncClient() as client:
                library = (await client.get(f"{srv.base_url}/api/design-systems")).json()

        # The HTTP listing is the library whole; the MCP listing names each system.
        assert listing["result"] == [
            {"slug": d["slug"], "name": d["name"], "category": d["category"]} for d in library
        ]
        assert system == next(d for d in library if d["slug"] == "shadcn")
        assert set(system) == {"slug", "name", "category", "tokens", "guidance", "source"}
        assert system["guidance"]
        assert missing.isError
        assert "Design system not found: no-such-system" in str(missing.content)


class TestMcpGuide:
    @intent("INT-PP-B38")
    @pytest.mark.anyio
    async def test_the_instructions_lead_to_the_guide(self, mcp_env: Path) -> None:
        """An agent with only this door connected reads the instructions, and they name
        the guide: the model, the token set, the markup rules, the blocks, the variants."""
        with _Server() as srv:
            async with (
                streamable_http_client(f"{srv.base_url}/mcp") as (read, write, _),
                ClientSession(read, write) as session,
            ):
                init = await session.initialize()
                result = await session.call_tool("get_guide", {})
        assert "get_guide" in (init.instructions or "")
        assert "phone layout rules" in (init.instructions or "")
        assert not result.isError
        guide = str(result.content[0].text)
        for section in (
            "## The model",
            "## The token set",
            "## Markup rules",
            "## Phone layout",
            "## Blocks",
            "## Offering variants",
        ):
            assert section in guide
        assert "| `--primary` |" in guide
        assert "(`sh-button`)" in guide
        assert "- `sh-bottom-bar`: " in guide

    @intent("INT-PP-B38")
    def test_the_guide_states_the_phone_rules_and_documents_the_phone_blocks(self) -> None:
        """The phone section carries the phone line, the rule shape, the navigation,
        table and form rules and what static markup expresses; each served phone
        block is documented in the rule shape, and every block the guide names is
        one the instance serves."""
        guide = render_guide(PACKAGED_BLOCKS)
        markup = guide[guide.index("## Markup rules") : guide.index("## Phone layout")]
        phone = " ".join(guide[guide.index("## Phone layout") : guide.index("## Blocks")].split())
        blocks = guide[guide.index("## Blocks") : guide.index("## Offering variants")]
        assert "`sm:grid-cols-2`" in markup
        assert "md:grid-cols-2" not in guide
        for rule in (
            # The phone line.
            "The phone line is 640px. Unprefixed utilities are the phone layout; `sm:` is 640px",
            "Every multi-column grid carries a breakpoint prefix",
            # The rule shape, and navigation.
            "Every phone rule is a value, a condition and a default",
            "Navigation is never hidden without a named replacement",
            "closed on load",
            "the primary action stays outside any menu",
            "| Four or fewer |",
            "| More than five, or browse-mostly |",
            # Tables and forms.
            "**Tables**: rows compared across columns",
            "scrolls sideways",
            "one term and description list per record",
            "never stacked with CSS",
            "**Forms**: one column, labels above fields",
            "16px below 640px (`text-base sm:text-sm`)",
            "`inputmode`",
            # What static markup expresses, and what it shows closed.
            "`<details>`",
            "`<dialog>`",
            "`popover`",
            "a pinned bar",
            "a draggable sheet, a priority-plus menu, a component tree switched by width",
            "is shown closed, its trigger visible",
        ):
            assert rule in phone, rule
        assert "what changes, at which width, the rule that picks it, and its default state" in (
            " ".join(blocks.split())
        )
        phone_blocks = {
            "sh-navbar",
            "sh-bottom-bar",
            "sh-sheet-menu",
            "sh-table",
            "sh-stacked-rows",
            "sh-form",
            "sh-action-bar",
        }
        documented = dict(re.findall(r"^- `(sh-[\w-]+)`: (.*)$", blocks, re.MULTILINE))
        assert set(documented) == phone_blocks
        for slug, text in documented.items():
            # At which width, the rule that picks it (`; for ...`), its default state.
            assert re.search(r"640px|320px|every width|any width", text), slug
            assert "; for " in text, slug
            assert re.search(r"on load|shown", text), slug
        served = {b.slug for b in PACKAGED_BLOCKS}
        assert set(re.findall(r"`(sh-[\w-]+)`", guide)) <= served
        # A block the instance does not serve is not documented.
        without = render_guide([b for b in PACKAGED_BLOCKS if b.slug != "sh-bottom-bar"])
        assert "- `sh-bottom-bar`: " not in without

    @intent("INT-PP-B38")
    def test_the_guide_names_the_webfonts_the_canvas_loads(self) -> None:
        """The families the guide offers for --font-sans are the ones the editor
        canvas's font sheet requests, so an agent names a typeface that renders."""
        editor = Path(__file__).resolve().parents[1] / "frontend/src/Editor.tsx"
        [sheet] = re.findall(
            r"https://fonts\.googleapis\.com/css2\?[^'\"]+", editor.read_text("utf-8")
        )
        families = parse_qs(urlparse(sheet).query)["family"]
        requested = [family.split(":")[0] for family in families]
        assert sorted(requested) == sorted(CANVAS_WEBFONTS)
        guide = render_guide([])
        for family in requested:
            assert family in guide


class TestMcpPrompts:
    @intent("INT-PP-B38")
    @pytest.mark.anyio
    async def test_bootstrap_project_prompt_carries_the_runbook(self, mcp_env: Path) -> None:
        """The prompt is the invocable form of the guide's build flow: the steps after
        the parametrized create and theme are the guide's own text."""
        with _Server() as srv:
            async with (
                streamable_http_client(f"{srv.base_url}/mcp") as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                prompts = await session.list_prompts()
                names = {prompt.name for prompt in prompts.prompts}
                result = await session.get_prompt(
                    "bootstrap-project",
                    {"name": "Acme", "brief": "A landing page", "template": "landing"},
                )
                branded = await session.get_prompt(
                    "bootstrap-project",
                    {"name": "Acme", "brief": "A landing page", "primary": "#F97815"},
                )
                guide = str((await session.call_tool("get_guide", {})).content[0].text)
        assert "bootstrap-project" in names
        content = result.messages[0].content
        branded_content = branded.messages[0].content
        assert isinstance(content, TextContent)
        assert isinstance(branded_content, TextContent)
        text = content.text
        assert "create_project" in text
        assert "save_theme" in text
        assert "landing" in text
        assert "Convert `#F97815` to an `H S% L%` triple for `--primary`" in branded_content.text
        shared = guide[guide.index("3. `list_blocks`") : guide.index("/p/<slug>`.")]
        assert "placeholder" in shared
        assert "`save_scheme` once per palette variant" in shared
        assert shared in text
        assert shared in branded_content.text

    @pytest.mark.anyio
    async def test_bootstrap_project_prompt_rejects_unknown_templates(
        self, mcp_env: Path
    ) -> None:
        with _Server() as srv:
            async with (
                streamable_http_client(f"{srv.base_url}/mcp") as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                with pytest.raises(McpError):
                    await session.get_prompt(
                        "bootstrap-project",
                        {"name": "Acme", "brief": "x", "template": "no-such-template"},
                    )


class TestMcpDeploymentSurface:
    @pytest.mark.anyio
    async def test_bare_mcp_path_works_with_the_spa_catchall(
        self, mcp_env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Clients connect to /mcp (no slash); the SPA catch-all must not swallow it."""
        dist = mcp_env / "dist"
        dist.mkdir()
        (dist / "index.html").write_text("<html>spa</html>", encoding="utf-8")
        monkeypatch.setenv("PROTOPANE_FRONTEND_DIST", str(dist))
        with _Server() as srv:
            names = await _tool_names(srv.base_url)
        assert "get_project" in names

    @pytest.mark.anyio
    async def test_allowed_hosts_gate_the_transport(
        self, mcp_env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A deployment allows its public hostname; other Host values answer 421."""
        initialize = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "probe", "version": "0"},
            },
        }
        headers = {"Accept": "application/json, text/event-stream"}
        monkeypatch.setenv("PROTOPANE_MCP_ALLOWED_HOSTS", "protopane.example.test")
        with _Server() as srv:
            async with httpx.AsyncClient() as client:
                wrong_host = await client.post(
                    f"{srv.base_url}/mcp/", json=initialize, headers=headers
                )
                right_host = await client.post(
                    f"{srv.base_url}/mcp/",
                    json=initialize,
                    headers={**headers, "Host": "protopane.example.test"},
                )
        assert wrong_host.status_code == 421
        assert right_host.status_code == 200
