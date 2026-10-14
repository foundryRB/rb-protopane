"""Save-scheme request body (the scheme slug is the path parameter)."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["SaveSchemeRequest"]


class SaveSchemeRequest(BaseModel):
    name: str
    tokens: dict[str, str]
