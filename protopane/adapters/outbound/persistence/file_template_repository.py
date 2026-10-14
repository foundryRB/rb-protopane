from __future__ import annotations

import json
from pathlib import Path

from protopane.adapters.outbound.persistence._atomic import atomic_write_text
from protopane.adapters.outbound.persistence.builtin_templates import builtin_templates
from protopane.domain.exceptions import BuiltinTemplateError, TemplateNotFoundError
from protopane.domain.model.template import Template
from protopane.logging import get_logger

logger = get_logger(__name__)


class FileTemplateRepository:
    """Built-in templates from the package, plus user templates saved as <root>/<slug>.json."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)
        self._builtin = {t.slug: t for t in builtin_templates()}

    def list_templates(self) -> list[Template]:
        user: list[Template] = []
        for file in sorted(self._root.glob("*.json")):
            try:
                user.append(self._read(file))
            except (json.JSONDecodeError, OSError, KeyError) as exc:
                logger.warning("skipping unreadable template at %s: %s", file, exc)
        return list(self._builtin.values()) + user

    def get(self, slug: str) -> Template:
        file = self._root / f"{slug}.json"
        if file.is_file():
            return self._read(file)
        if slug in self._builtin:
            return self._builtin[slug]
        raise TemplateNotFoundError(slug)

    def save(self, template: Template) -> None:
        payload = {"slug": template.slug, "name": template.name, "html": template.html}
        file = self._root / f"{template.slug}.json"
        atomic_write_text(file, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        logger.info("saved template %s", template.slug)

    def delete(self, slug: str) -> None:
        file = self._root / f"{slug}.json"
        if file.is_file():
            file.unlink()
            logger.info("deleted template %s", slug)
            return
        if slug in self._builtin:
            raise BuiltinTemplateError(slug)
        raise TemplateNotFoundError(slug)

    @staticmethod
    def _read(file: Path) -> Template:
        data = json.loads(file.read_text(encoding="utf-8"))
        return Template(slug=data["slug"], name=data["name"], html=data["html"], builtin=False)
