"""Project routes: CRUD, theme, screens, export, and the live-reload event stream."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse

from protopane.adapters.inbound.http.dtos.create_project_request import CreateProjectRequest
from protopane.adapters.inbound.http.dtos.project_dto import ProjectDTO
from protopane.adapters.inbound.http.dtos.project_export_dto import ProjectExportDTO
from protopane.adapters.inbound.http.dtos.project_summary_dto import ProjectSummaryDTO
from protopane.adapters.inbound.http.dtos.rename_project_request import RenameProjectRequest
from protopane.adapters.inbound.http.dtos.save_scheme_request import SaveSchemeRequest
from protopane.adapters.inbound.http.dtos.save_screen_request import SaveScreenRequest
from protopane.adapters.inbound.http.dtos.save_theme_request import SaveThemeRequest
from protopane.adapters.inbound.http.mappers.project_mapper import (
    export_to_dto,
    project_to_dto,
    summary_to_dto,
)
from protopane.container import Container

__all__ = ["build_projects_router"]


def build_projects_router(container: Container) -> APIRouter:
    """Wire the project routes to the container's use cases. Presentation only, no logic."""
    router = APIRouter(prefix="/api")

    @router.get("/projects", response_model=list[ProjectSummaryDTO])
    def list_projects(include_archived: bool = False) -> list[ProjectSummaryDTO]:
        return [summary_to_dto(s) for s in container.list_projects(include_archived)]

    @router.post("/projects", response_model=ProjectDTO, status_code=201)
    def create_project(body: CreateProjectRequest) -> ProjectDTO:
        return project_to_dto(container.create_project(body.name, body.template))

    @router.get("/projects/{slug}", response_model=ProjectDTO)
    def get_project(slug: str) -> ProjectDTO:
        return project_to_dto(container.get_project(slug))

    @router.delete("/projects/{slug}", status_code=204)
    def delete_project(slug: str) -> Response:
        container.delete_project(slug)
        return Response(status_code=204)

    @router.post("/projects/{slug}/rename", response_model=ProjectDTO)
    def rename_project(slug: str, body: RenameProjectRequest) -> ProjectDTO:
        return project_to_dto(container.rename_project(slug, body.new_slug, body.new_name))

    @router.post("/projects/{slug}/archive", response_model=ProjectDTO)
    def archive_project(slug: str) -> ProjectDTO:
        return project_to_dto(container.archive_project(slug))

    @router.post("/projects/{slug}/unarchive", response_model=ProjectDTO)
    def unarchive_project(slug: str) -> ProjectDTO:
        return project_to_dto(container.unarchive_project(slug))

    @router.put("/projects/{slug}/theme", response_model=ProjectDTO)
    def save_theme(slug: str, body: SaveThemeRequest) -> ProjectDTO:
        return project_to_dto(container.save_theme(slug, body.tokens, body.design_system))

    @router.put("/projects/{slug}/schemes/{scheme_slug}", response_model=ProjectDTO)
    def save_scheme(slug: str, scheme_slug: str, body: SaveSchemeRequest) -> ProjectDTO:
        return project_to_dto(container.save_scheme(slug, scheme_slug, body.name, body.tokens))

    @router.delete("/projects/{slug}/schemes/{scheme_slug}", response_model=ProjectDTO)
    def delete_scheme(slug: str, scheme_slug: str) -> ProjectDTO:
        return project_to_dto(container.delete_scheme(slug, scheme_slug))

    @router.put("/projects/{slug}/screens/{screen_slug}", response_model=ProjectDTO)
    def save_screen(slug: str, screen_slug: str, body: SaveScreenRequest) -> ProjectDTO:
        return project_to_dto(
            container.save_screen(slug, screen_slug, body.name, body.html, body.css)
        )

    @router.delete("/projects/{slug}/screens/{screen_slug}", response_model=ProjectDTO)
    def delete_screen(slug: str, screen_slug: str) -> ProjectDTO:
        return project_to_dto(container.delete_screen(slug, screen_slug))

    @router.get("/projects/{slug}/export", response_model=ProjectExportDTO)
    def export_project(slug: str) -> ProjectExportDTO:
        return export_to_dto(container.export_project(slug))

    @router.get("/projects/{slug}/events")
    async def project_events(slug: str) -> StreamingResponse:
        """Server-sent events: emit `change` whenever this project is saved (live reload)."""

        async def stream() -> AsyncIterator[bytes]:
            async with container.changes.subscribe() as queue:
                yield b": connected\n\n"
                while True:
                    try:
                        changed = await asyncio.wait_for(queue.get(), timeout=15.0)
                    except asyncio.TimeoutError:
                        yield b": ping\n\n"
                        continue
                    if changed == slug:
                        yield f"event: change\ndata: {changed}\n\n".encode()

        return StreamingResponse(stream(), media_type="text/event-stream")

    return router
