from __future__ import annotations

import json
import shutil
from pathlib import Path

from protopane.adapters.outbound.persistence._atomic import atomic_write_text
from protopane.domain.exceptions import ProjectExistsError, ProjectNotFoundError
from protopane.domain.model.design_system_ref import DesignSystemRef
from protopane.domain.model.project import Project
from protopane.domain.model.project_summary import ProjectSummary
from protopane.domain.model.scheme import Scheme
from protopane.domain.model.screen import Screen
from protopane.domain.model.theme import Theme
from protopane.logging import get_logger

logger = get_logger(__name__)


class FileProjectRepository:
    """Persists each project as <root>/<slug>/project.json. Implements ProjectRepository."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def exists(self, slug: str) -> bool:
        return self._file(slug).is_file()

    def list_summaries(self) -> list[ProjectSummary]:
        summaries: list[ProjectSummary] = []
        for child in sorted(self._root.iterdir()):
            file = child / "project.json"
            if not file.is_file():
                continue
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                summaries.append(
                    ProjectSummary(
                        slug=data["slug"],
                        name=data["name"],
                        screen_count=len(data.get("screens", [])),
                        archived=bool(data.get("archived", False)),
                    )
                )
            except (json.JSONDecodeError, OSError, KeyError) as exc:
                logger.warning("skipping unreadable project at %s: %s", file, exc)
        return summaries

    def get(self, slug: str) -> Project:
        file = self._file(slug)
        if not file.is_file():
            raise ProjectNotFoundError(slug)
        logger.debug("reading project %s", slug)
        return self._to_project(json.loads(file.read_text(encoding="utf-8")))

    def save(self, project: Project) -> None:
        directory = self._dir(project.slug)
        directory.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._to_data(project), indent=2, ensure_ascii=False)
        atomic_write_text(directory / "project.json", payload + "\n")
        logger.info("saved project %s (%d screens)", project.slug, len(project.screens))

    def delete(self, slug: str) -> None:
        if not self._file(slug).is_file():
            raise ProjectNotFoundError(slug)
        shutil.rmtree(self._dir(slug))
        logger.info("deleted project %s", slug)

    def rename(self, slug: str, new_slug: str) -> None:
        if not self._file(slug).is_file():
            raise ProjectNotFoundError(slug)
        if self._dir(new_slug).exists():
            raise ProjectExistsError(new_slug)
        self._dir(slug).rename(self._dir(new_slug))
        # The moved file still carries the old slug; rewrite it so the store is
        # consistent even if the caller never saves again.
        data = json.loads(self._file(new_slug).read_text(encoding="utf-8"))
        data["slug"] = new_slug
        atomic_write_text(
            self._file(new_slug), json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        )
        logger.info("renamed project %s -> %s", slug, new_slug)

    def _dir(self, slug: str) -> Path:
        return self._root / slug

    def _file(self, slug: str) -> Path:
        return self._dir(slug) / "project.json"

    @staticmethod
    def _to_project(data: dict) -> Project:
        ref = data.get("design_system")
        return Project(
            slug=data["slug"],
            name=data["name"],
            archived=bool(data.get("archived", False)),
            theme=Theme(tokens=dict(data.get("theme", {}).get("tokens", {}))),
            screens=[
                Screen(slug=s["slug"], name=s["name"], html=s["html"], css=s["css"])
                for s in data.get("screens", [])
            ],
            schemes=[
                Scheme(slug=s["slug"], name=s["name"], tokens=dict(s.get("tokens", {})))
                for s in data.get("schemes", [])
            ],
            design_system=(
                DesignSystemRef(
                    slug=ref["slug"], name=ref["name"], guidance=ref.get("guidance", "")
                )
                if ref
                else None
            ),
        )

    @staticmethod
    def _to_data(project: Project) -> dict:
        return {
            "slug": project.slug,
            "name": project.name,
            "archived": project.archived,
            "theme": {"tokens": dict(project.theme.tokens)},
            "screens": [
                {"slug": s.slug, "name": s.name, "html": s.html, "css": s.css}
                for s in project.screens
            ],
            "schemes": [
                {"slug": s.slug, "name": s.name, "tokens": dict(s.tokens)}
                for s in project.schemes
            ],
            "design_system": (
                {
                    "slug": project.design_system.slug,
                    "name": project.design_system.name,
                    "guidance": project.design_system.guidance,
                }
                if project.design_system
                else None
            ),
        }
