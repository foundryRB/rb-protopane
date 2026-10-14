"""Design-chat route: streams the agent's turn as server-sent events.

Mounted only when the composition wires the design agent (the `agent` extra plus
an explicit opt-in). The MCP door deliberately has no counterpart: an MCP client
is itself the authoring agent and drives the project tools directly.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from protopane.adapters.inbound.http.dtos.chat_request import ChatRequest
from protopane.application.ports.design_agent import ChatTurn
from protopane.container import Container

__all__ = ["build_chat_router"]


def build_chat_router(container: Container) -> APIRouter:
    """Wire the in-page design chat to the container's design agent."""
    router = APIRouter(prefix="/api")
    agent = container.design_agent
    if agent is None:  # pragma: no cover - the factory mounts this router only when wired
        raise RuntimeError("the chat router requires the design-agent capability")

    @router.post("/projects/{slug}/chat")
    async def chat(slug: str, body: ChatRequest) -> StreamingResponse:
        history = [
            ChatTurn(role=turn.role, content=turn.content)  # type: ignore[arg-type]
            for turn in body.history
            if turn.role in ("user", "assistant")
        ]

        async def stream() -> AsyncIterator[bytes]:
            async for event in agent.stream(slug, body.message, history):
                payload = json.dumps({"kind": event.kind, "text": event.text})
                yield f"data: {payload}\n\n".encode()
            yield b"event: done\ndata: {}\n\n"

        return StreamingResponse(stream(), media_type="text/event-stream")

    return router
