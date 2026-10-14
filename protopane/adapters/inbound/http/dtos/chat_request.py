"""Design-chat request body: the message plus prior turns."""

from __future__ import annotations

from pydantic import BaseModel

from protopane.adapters.inbound.http.dtos.chat_turn_dto import ChatTurnDTO

__all__ = ["ChatRequest"]


class ChatRequest(BaseModel):
    message: str
    history: list[ChatTurnDTO] = []
