from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class ChatTurn:
    """One prior turn of the design conversation, replayed for context."""

    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True)
class AgentEvent:
    """A normalized event streamed from the design agent to the HTTP layer.

    kind is "text" (assistant prose), "tool" (a tool the agent invoked, text is its
    name), "result" (the turn finished) or "error" (text is the failure message).
    """

    kind: Literal["text", "tool", "result", "error"]
    text: str


class DesignAgent(Protocol):
    """Outbound port: an AI agent that edits a project's screens and theme via tools."""

    def stream(
        self, project_slug: str, message: str, history: list[ChatTurn]
    ) -> AsyncIterator[AgentEvent]: ...
