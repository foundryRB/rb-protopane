"""Save-screen request body."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["SaveScreenRequest"]


class SaveScreenRequest(BaseModel):
    name: str
    html: str
    css: str
