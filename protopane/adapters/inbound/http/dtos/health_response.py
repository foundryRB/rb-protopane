"""Health probe response DTO."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["HealthResponse"]


class HealthResponse(BaseModel):
    """Liveness, and the release actually serving."""

    status: str
    version: str
