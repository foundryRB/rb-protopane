"""Domain-to-DTO mappers for projects, screens, themes, summaries, and exports."""

from __future__ import annotations

from protopane.adapters.inbound.http.dtos.design_system_ref_dto import DesignSystemRefDTO
from protopane.adapters.inbound.http.dtos.project_dto import ProjectDTO
from protopane.adapters.inbound.http.dtos.project_export_dto import ProjectExportDTO
from protopane.adapters.inbound.http.dtos.project_summary_dto import ProjectSummaryDTO
from protopane.adapters.inbound.http.dtos.saved_theme_dto import SavedThemeDTO
from protopane.adapters.inbound.http.dtos.scheme_dto import SchemeDTO
from protopane.adapters.inbound.http.dtos.screen_dto import ScreenDTO
from protopane.adapters.inbound.http.dtos.theme_dto import ThemeDTO
from protopane.domain.model.design_system_ref import DesignSystemRef
from protopane.domain.model.project import Project
from protopane.domain.model.project_export import ProjectExport
from protopane.domain.model.project_summary import ProjectSummary
from protopane.domain.model.scheme import Scheme
from protopane.domain.model.screen import Screen

__all__ = [
    "design_system_ref_to_dto",
    "screen_to_dto",
    "scheme_to_dto",
    "project_to_dto",
    "saved_theme_to_dto",
    "summary_to_dto",
    "export_to_dto",
]


def design_system_ref_to_dto(ref: DesignSystemRef | None) -> DesignSystemRefDTO | None:
    if ref is None:
        return None
    return DesignSystemRefDTO(slug=ref.slug, name=ref.name, guidance=ref.guidance)


def screen_to_dto(screen: Screen) -> ScreenDTO:
    return ScreenDTO(slug=screen.slug, name=screen.name, html=screen.html, css=screen.css)


def scheme_to_dto(scheme: Scheme) -> SchemeDTO:
    return SchemeDTO(slug=scheme.slug, name=scheme.name, tokens=dict(scheme.tokens))


def project_to_dto(project: Project) -> ProjectDTO:
    return ProjectDTO(
        slug=project.slug,
        name=project.name,
        archived=project.archived,
        theme=ThemeDTO(tokens=dict(project.theme.tokens)),
        screens=[screen_to_dto(s) for s in project.screens],
        schemes=[scheme_to_dto(s) for s in project.schemes],
        design_system=design_system_ref_to_dto(project.design_system),
    )


def saved_theme_to_dto(project: Project) -> SavedThemeDTO:
    return SavedThemeDTO(
        tokens=dict(project.theme.tokens),
        design_system=design_system_ref_to_dto(project.design_system),
    )


def summary_to_dto(summary: ProjectSummary) -> ProjectSummaryDTO:
    return ProjectSummaryDTO(
        slug=summary.slug,
        name=summary.name,
        screen_count=summary.screen_count,
        archived=summary.archived,
    )


def export_to_dto(export: ProjectExport) -> ProjectExportDTO:
    return ProjectExportDTO(
        theme_css=export.theme_css,
        screens=[screen_to_dto(s) for s in export.screens],
        design_system=design_system_ref_to_dto(export.design_system),
    )
