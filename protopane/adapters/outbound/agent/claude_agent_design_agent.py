from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    SdkMcpTool,
    TextBlock,
    ToolPermissionContext,
    ToolUseBlock,
    create_sdk_mcp_server,
    tool,
)

from protopane.application.ports.design_agent import AgentEvent, ChatTurn
from protopane.application.use_cases.get_project import GetProject
from protopane.application.use_cases.save_screen import SaveScreen
from protopane.application.use_cases.save_theme import SaveTheme

_TOOL_PREFIX = "mcp__protopane__"

_SYSTEM_PROMPT = """You are protopane's design assistant, editing a throwaway UI prototype for \
project "{slug}" on a live canvas.

Workflow:
- Call get_project first to read the current screen HTML/CSS and theme tokens.
- Make changes by calling update_screen (a full HTML replacement, optional CSS) and set_theme \
(brand tokens). The canvas updates the moment you save.
- After editing, tell the user in one or two sentences what you changed.

Markup rules:
- Use only Tailwind utility classes backed by the design tokens: bg-primary, \
text-primary-foreground, bg-card, text-card-foreground, text-foreground, text-muted-foreground, \
bg-background, bg-secondary, bg-accent, bg-destructive, border, rounded-md, rounded-lg, etc.
- NEVER hardcode a hex colour or a pixel radius; theming must flow through the tokens.
- Build from this block vocabulary so the markup maps to real components: Button, Button \
(outline), Card, Input, Badge, Heading, Text, Section, 2 columns, 3 columns.
- Keep structure semantic (section, h1, button).

Theme tokens are shadcn HSL triples with no hsl() wrapper, e.g. "217 91% 60%". Apply a brand by \
replacing the whole token set so every surface stays coherent."""


async def _allow_only_protopane(
    tool_name: str, tool_input: dict, context: ToolPermissionContext
) -> PermissionResultAllow | PermissionResultDeny:
    """Hard allowlist: the agent may only touch protopane's own tools, nothing else."""
    if tool_name.startswith(_TOOL_PREFIX):
        return PermissionResultAllow()
    return PermissionResultDeny(message="Only protopane design tools are permitted here.")


def _format_prompt(history: list[ChatTurn], message: str) -> str:
    if not history:
        return message
    transcript = "\n".join(f"{turn.role}: {turn.content}" for turn in history)
    return f"{transcript}\nuser: {message}"


class ClaudeAgentDesignAgent:
    """DesignAgent backed by the Claude Agent SDK, billed to the operator's subscription.

    Each turn builds an in-process MCP server whose tools call protopane's own save use
    cases, so the agent's edits flow through the change notifier and the open editor reloads.
    """

    def __init__(
        self, get_project: GetProject, save_screen: SaveScreen, save_theme: SaveTheme
    ) -> None:
        self._get_project = get_project
        self._save_screen = save_screen
        self._save_theme = save_theme

    def _build_tools(self, slug: str) -> list[SdkMcpTool]:
        get_project = self._get_project
        save_screen = self._save_screen
        save_theme = self._save_theme

        @tool("get_project", "Read the current screen HTML/CSS and theme tokens being edited.", {})
        async def get_project_tool(args: dict) -> dict:
            project = await asyncio.to_thread(get_project, slug)
            screen = project.screens[0] if project.screens else None
            payload = {
                "theme_tokens": dict(project.theme.tokens),
                "screen": (
                    {
                        "slug": screen.slug,
                        "name": screen.name,
                        "html": screen.html,
                        "css": screen.css,
                    }
                    if screen
                    else None
                ),
            }
            return {"content": [{"type": "text", "text": json.dumps(payload)}]}

        @tool(
            "update_screen",
            "Replace the current screen's HTML (and optional CSS). Token-backed Tailwind "
            "utility classes only; never hardcode hex colours.",
            {"html": str, "css": str},
        )
        async def update_screen_tool(args: dict) -> dict:
            project = await asyncio.to_thread(get_project, slug)
            screen = project.screens[0] if project.screens else None
            screen_slug = screen.slug if screen else "home"
            name = screen.name if screen else "Home"
            css = args.get("css") or (screen.css if screen else "")
            await asyncio.to_thread(save_screen, slug, screen_slug, name, args["html"], css)
            return {"content": [{"type": "text", "text": "Screen updated."}]}

        @tool(
            "set_theme",
            "Replace the project's theme tokens. Values are shadcn HSL triples like '217 91% 60%'.",
            {"tokens": dict},
        )
        async def set_theme_tool(args: dict) -> dict:
            await asyncio.to_thread(save_theme, slug, dict(args["tokens"]))
            return {"content": [{"type": "text", "text": "Theme updated."}]}

        return [get_project_tool, update_screen_tool, set_theme_tool]

    async def stream(
        self, project_slug: str, message: str, history: list[ChatTurn]
    ) -> AsyncIterator[AgentEvent]:
        server = create_sdk_mcp_server(
            name="protopane", version="1.0.0", tools=self._build_tools(project_slug)
        )
        options = ClaudeAgentOptions(
            mcp_servers={"protopane": server},
            allowed_tools=[
                f"{_TOOL_PREFIX}get_project",
                f"{_TOOL_PREFIX}update_screen",
                f"{_TOOL_PREFIX}set_theme",
            ],
            system_prompt=_SYSTEM_PROMPT.format(slug=project_slug),
            permission_mode="default",
            can_use_tool=_allow_only_protopane,
            max_turns=12,
        )
        try:
            # ClaudeSDKClient runs in streaming mode, which is required for the can_use_tool gate.
            async with ClaudeSDKClient(options=options) as client:
                await client.query(_format_prompt(history, message))
                async for msg in client.receive_response():
                    if isinstance(msg, AssistantMessage):
                        for block in msg.content:
                            if isinstance(block, TextBlock):
                                yield AgentEvent("text", block.text)
                            elif isinstance(block, ToolUseBlock):
                                yield AgentEvent("tool", block.name.removeprefix(_TOOL_PREFIX))
                    elif isinstance(msg, ResultMessage):
                        yield AgentEvent("result", "")
        except Exception as exc:
            yield AgentEvent("error", str(exc))
