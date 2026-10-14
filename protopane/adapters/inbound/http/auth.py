from __future__ import annotations

import base64
import os
import secrets

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import RequestResponseEndpoint

from protopane.logging import get_logger

logger = get_logger(__name__)

# The health probe must answer without credentials so liveness/readiness work.
_EXEMPT_PATHS = frozenset({"/api/health"})
_MCP_PREFIX = "/mcp"


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _auth_scope() -> str:
    """Which surfaces the Basic gate covers (PROTOPANE_AUTH_SCOPE).

    "all" (default): every surface (SPA, /api, /mcp), the stand-alone posture.
    "mcp": the /mcp and full identity source machine doors, because an OIDC reverse proxy
    (oauth2-proxy) fronts the SPA and /api for humans, who cannot complete an
    interactive login on a machine-to-machine channel. The chart sets this only
    when that proxy is present, so the human surfaces are never truly open.
    """
    scope = (os.environ.get("PROTOPANE_AUTH_SCOPE") or "all").strip().lower()
    return scope if scope in {"all", "mcp"} else "all"


def _gated(path: str, scope: str) -> bool:
    """Whether a path is subject to the Basic gate under the active scope."""
    if path in _EXEMPT_PATHS:
        return False
    if path == "/api/identity-sources" or path.startswith("/api/identity-sources/"):
        return True
    if scope == "mcp":
        return path == _MCP_PREFIX or path.startswith(_MCP_PREFIX + "/")
    return True


def install_auth(app: FastAPI) -> None:
    """Gate protopane's routes behind HTTP Basic auth, fail closed.

    Enforced when PROTOPANE_AUTH_USER and PROTOPANE_AUTH_PASSWORD are both set;
    turned off only by an explicit PROTOPANE_AUTH_DISABLED=true (local dev and
    tests). With neither set, gated routes answer 503: a misconfigured instance
    is closed, never silently open. PROTOPANE_AUTH_SCOPE picks the covered
    surfaces (see _auth_scope): "all" gates every door (SPA, /api, /mcp) when
    protopane stands alone, "mcp" gates the /mcp and identity source machine doors when an OIDC
    reverse proxy fronts the human surfaces. The health endpoint stays exempt so
    orchestration probes keep working.
    """
    user = os.environ.get("PROTOPANE_AUTH_USER", "")
    password = os.environ.get("PROTOPANE_AUTH_PASSWORD", "")
    disabled = _truthy(os.environ.get("PROTOPANE_AUTH_DISABLED"))
    scope = _auth_scope()
    configured = bool(user and password)

    if disabled:
        logger.warning("protopane auth is DISABLED; do not expose this instance publicly")
    elif configured:
        logger.info("protopane auth is ENABLED (HTTP Basic, scope=%s)", scope)
    else:
        logger.error(
            "protopane auth is NOT CONFIGURED: set PROTOPANE_AUTH_USER and "
            "PROTOPANE_AUTH_PASSWORD, or PROTOPANE_AUTH_DISABLED=true for local dev; "
            "gated routes answer 503 until then"
        )

    @app.middleware("http")
    async def _basic_auth(request: Request, call_next: RequestResponseEndpoint) -> Response:
        if disabled or not _gated(request.url.path, scope):
            return await call_next(request)
        if not configured:
            return JSONResponse(
                status_code=503,
                content={"detail": "authentication is not configured"},
            )
        if _is_authorized(request, user, password):
            return await call_next(request)
        return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="protopane"'})


def _is_authorized(request: Request, user: str, password: str) -> bool:
    """Constant-time check of an HTTP Basic Authorization header against the configured pair."""
    scheme, _, encoded = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "basic" or not encoded:
        return False
    try:
        decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return False
    got_user, separator, got_password = decoded.partition(":")
    if not separator:
        return False
    user_ok = secrets.compare_digest(got_user, user)
    password_ok = secrets.compare_digest(got_password, password)
    return user_ok and password_ok
