"""Save-template request body."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["SaveTemplateRequest"]


class SaveTemplateRequest(BaseModel):
    name: str
    html: str
