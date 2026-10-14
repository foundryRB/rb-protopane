"""Register the global exception handler on the FastAPI app."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from protopane.adapters.inbound.http.mappers.exception_mapper import DEFAULT_STATUS, STATUS_MAP
from protopane.domain.exceptions import ProtopaneError
from protopane.logging import get_logger

__all__ = ["register_exception_handler"]

logger = get_logger(__name__)


def register_exception_handler(app: FastAPI) -> None:
    """Install a single handler mapping domain errors to HTTP responses."""

    @app.exception_handler(ProtopaneError)
    async def _handle_domain_error(request: Request, exc: ProtopaneError) -> JSONResponse:
        status = STATUS_MAP.get(type(exc), DEFAULT_STATUS)
        logger.info("%s %s -> %d (%s)", request.method, request.url.path, status, exc)
        return JSONResponse(status_code=status, content={"detail": str(exc)})
