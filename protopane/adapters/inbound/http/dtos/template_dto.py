"""Full template response DTO."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["TemplateDTO"]


class TemplateDTO(BaseModel):
    slug: str
    name: str
    html: str
    builtin: bool
