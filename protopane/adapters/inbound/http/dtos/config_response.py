"""Frontend runtime-config response DTO."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["ConfigResponse"]


class ConfigResponse(BaseModel):
    chatEnabled: bool
