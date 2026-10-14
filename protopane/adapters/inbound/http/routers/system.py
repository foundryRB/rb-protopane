"""System routes: the health probe, the frontend's runtime config, and the agent credential."""

from __future__ import annotations

import base64
import os

from fastapi import APIRouter, HTTPException

from protopane import __version__
from protopane.adapters.inbound.http.dtos.agent_credential_response import (
    AgentCredentialResponse,
)
from protopane.adapters.inbound.http.dtos.config_response import ConfigResponse
from protopane.adapters.inbound.http.dtos.health_response import HealthResponse
from protopane.container import Container

__all__ = ["build_system_router"]


def build_system_router(container: Container) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        """Liveness/readiness probe; exempt from auth, and skipped at the OIDC
        gate so an external observer can read which release serves without a
        credential.

        $APP_VERSION is the chart's image tag - the value promotion writes back -
        so the answer describes the pod rather than the source tree. The package
        constant is the local-dev fallback only: a hardcoded string is not
        freshness.
        """
        return HealthResponse(
            status="ok", version=os.environ.get("APP_VERSION") or __version__
        )

    @router.get("/config", response_model=ConfigResponse)
    def config() -> ConfigResponse:
        return ConfigResponse(chatEnabled=container.agent_enabled)

    @router.get("/agent-credential", response_model=AgentCredentialResponse)
    def agent_credential() -> AgentCredentialResponse:
        """The MCP HTTP Basic credential (base64 of user:password) for the in-app
        "Connect an agent" one-liner.

        Reads the same PROTOPANE_AUTH_USER / PROTOPANE_AUTH_PASSWORD pair the auth
        gate enforces. Reachable only by an already-authenticated caller: under
        scope=mcp the oauth2-proxy in front admits only a logged-in human; under
        scope=all the Basic gate covers it. Answers 503 when the credential is
        unset, mirroring the fail-closed auth posture (there is nothing to hand out).
        """
        user = os.environ.get("PROTOPANE_AUTH_USER", "")
        password = os.environ.get("PROTOPANE_AUTH_PASSWORD", "")
        if not (user and password):
            raise HTTPException(status_code=503, detail="MCP credential is not configured")
        encoded = base64.b64encode(f"{user}:{password}".encode()).decode()
        return AgentCredentialResponse(credential=encoded)

    return router
