"""One prior turn of the in-page design chat."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["ChatTurnDTO"]


class ChatTurnDTO(BaseModel):
    role: str
    content: str
