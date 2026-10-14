"""Agent-connection credential response DTO."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["AgentCredentialResponse"]


class AgentCredentialResponse(BaseModel):
    credential: str
