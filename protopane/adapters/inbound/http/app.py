"""FastAPI application factory."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from mcp.server.fastmcp import FastMCP

from protopane import __version__
from protopane.adapters.inbound.http.auth import install_auth
from protopane.adapters.inbound.http.exception_handlers import register_exception_handler
from protopane.adapters.inbound.http.routers.blocks import build_blocks_router
from protopane.adapters.inbound.http.routers.design_systems import build_design_systems_router
from protopane.adapters.inbound.http.routers.projects import build_projects_router
from protopane.adapters.inbound.http.routers.system import build_system_router
from protopane.adapters.inbound.http.routers.templates import build_templates_router
from protopane.adapters.inbound.mcp.server import build_mcp_server
from protopane.container import Container
from protopane.logging import configure_logging

__all__ = ["create_app"]

_BUILD_HINT = (
    "<!doctype html><title>protopane</title>"
    "<h1>protopane</h1><p>The API is running, but the frontend is not built. "
    "Run <code>npm run build</code> in <code>frontend/</code> (production), or the dev "
    "server with <code>npm run dev</code> (which serves the SPA and proxies /api here).</p>"
)

_TRUTHY = {"1", "true", "yes", "on"}


def _agent_enabled() -> bool:
    """The in-page design chat is opt-in and local-only: off unless explicitly enabled."""
    return (os.environ.get("PROTOPANE_AGENT_ENABLED") or "").strip().lower() in _TRUTHY


def create_app() -> FastAPI:
    configure_logging()
    projects_dir = Path(os.environ.get("PROTOPANE_PROJECTS_DIR", "projects"))
    templates_dir = Path(os.environ.get("PROTOPANE_TEMPLATES_DIR", "templates"))
    container = Container(
        projects_dir=projects_dir,
        templates_dir=templates_dir,
        agent_enabled=_agent_enabled(),
    )

    mcp_server = build_mcp_server(container)
    app = FastAPI(title="protopane", version=__version__, lifespan=_lifespan(mcp_server))
    # Gate the whole app (SPA + /api + /mcp) behind fail-closed HTTP Basic auth,
    # except /api/health. Disabled in dev/tests via PROTOPANE_AUTH_DISABLED=true.
    install_auth(app)
    register_exception_handler(app)
    app.include_router(build_system_router(container))
    app.include_router(build_projects_router(container))
    app.include_router(build_templates_router(container))
    app.include_router(build_blocks_router(container))
    app.include_router(build_design_systems_router(container))

    if container.agent_enabled:
        # Imported lazily: the router pulls the design-agent port types, which the
        # public hub composition never wires.
        from protopane.adapters.inbound.http.routers.chat import build_chat_router

        app.include_router(build_chat_router(container))

    # The transport lives under /mcp/. The bare path must work too (clients
    # connect to https://<host>/mcp), and it cannot rely on the router's
    # implicit slash redirect: the SPA catch-all matches /mcp first. An
    # explicit 307 keeps the method and body.
    @app.api_route("/mcp", methods=["GET", "POST", "DELETE"], include_in_schema=False)
    async def _mcp_redirect() -> RedirectResponse:
        return RedirectResponse(url="/mcp/", status_code=307)

    app.mount("/mcp", mcp_server.streamable_http_app())

    _mount_frontend(app)
    return app


def _lifespan(mcp_server: FastMCP) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    """Run the MCP session manager for the app's lifetime."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with mcp_server.session_manager.run():
            yield

    return lifespan


def _mount_frontend(app: FastAPI) -> None:
    """Serve the built SPA. The production image points PROTOPANE_FRONTEND_DIST at the
    built dist; in dev Vite serves the SPA, so without a dist this returns a build hint
    rather than a bare 404. Registered after the API routes and the /mcp mount so those
    win; /api paths are never swallowed by the catch-all."""
    dist = Path(os.environ.get("PROTOPANE_FRONTEND_DIST", "frontend/dist"))
    index = dist / "index.html"
    served = dist.is_dir() and index.is_file()
    root = dist.resolve()

    @app.get("/{full_path:path}")
    async def frontend(full_path: str) -> Response:
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        if not served:
            return HTMLResponse(_BUILD_HINT, status_code=503)
        candidate = (dist / full_path).resolve()
        if full_path and candidate.is_file() and root in candidate.parents:
            return FileResponse(str(candidate))
        return FileResponse(str(index))
