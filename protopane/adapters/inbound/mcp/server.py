"""MCP inbound adapter: tools mirroring the inbound use cases (streamable HTTP).

A third door into the same use cases as the SPA and REST: a screen saved through
an MCP tool is the screen the API and the UI read back, because every door calls
the identical use case behind the container. Domain-data responses reuse the
HTTP DTO mappers. The four delete tools return {"deleted": "<slug>"}, naming
the removed project, scheme, screen or template.

A write answers with what it wrote, not the project around it: an agent's tool
result has a budget, and a project of tens of screens is past it. `get_project`
and `export_project` are the reads that return the project whole. The design-system
library is past it too, so `list_design_systems` names each system and
`get_design_system` reads one whole.

The design chat has no tool on purpose: an MCP client is itself the authoring
agent, so it drives these project tools directly. The reference it authors from
is the `get_guide` tool, and the `bootstrap-project` prompt renders the guide's
build flow with a brief.
"""

from __future__ import annotations

import os
import re

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from protopane.adapters.inbound.http.mappers.block_mapper import block_to_dto
from protopane.adapters.inbound.http.mappers.design_system_mapper import design_system_to_dto
from protopane.adapters.inbound.http.mappers.project_mapper import (
    export_to_dto,
    project_to_dto,
    saved_theme_to_dto,
    scheme_to_dto,
    screen_to_dto,
    summary_to_dto,
)
from protopane.adapters.inbound.http.mappers.template_mapper import (
    template_summary_to_dto,
    template_to_dto,
)
from protopane.adapters.inbound.mcp.guide import render_flow, render_guide
from protopane.container import Container
from protopane.domain.exceptions.scheme_not_found_error import SchemeNotFoundError
from protopane.domain.exceptions.screen_not_found_error import ScreenNotFoundError
from protopane.domain.model.project import Project
from protopane.domain.model.project_summary import ProjectSummary

__all__ = ["build_mcp_server"]

_INSTRUCTIONS = (
    "Visual prototyping hub for the design phase: each customer engagement is a "
    "project holding shadcn design tokens (the theme) and screens (HTML bodies "
    "written in token-backed utility classes). Reads return persisted state; "
    "writes persist through the same use cases as the UI and the REST API. When "
    "authoring screens, compose token-backed utilities (bg-primary, text-foreground, "
    "border, rounded-md) and never inline hex colors: the tokens are the brand, and "
    "only token-backed markup reskins live and survives handoff. Call get_guide "
    "before the first write: it is the long-form reference (what a project, theme, "
    "scheme, screen and template are; the closed token set and each token's role; "
    "the markup rules the write gate enforces; the phone layout rules; the block "
    "vocabulary and each phone block's behaviour; how palette variants are offered "
    "as schemes inside one project)."
)

_ALLOWED_HOSTS_ENV = "PROTOPANE_MCP_ALLOWED_HOSTS"
_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
# The fields of a design system `list_design_systems` answers with, per system.
_DESIGN_SYSTEM_SUMMARY = {"slug", "name", "category"}


def _transport_security() -> TransportSecuritySettings | None:
    """DNS-rebinding protection for the transport.

    The SDK default admits localhost only, which is right for the local run.
    A deployment serves on a public hostname, so the chart supplies it via
    $PROTOPANE_MCP_ALLOWED_HOSTS (comma-separated Host header values).
    """
    raw = os.environ.get(_ALLOWED_HOSTS_ENV)
    if not raw:
        return None
    hosts = [h.strip() for h in raw.split(",") if h.strip()]
    return TransportSecuritySettings(allowed_hosts=hosts)


def _summary(project: Project) -> dict[str, object]:
    """A project-level write's answer: the entry `list_projects` returns for the project."""
    return summary_to_dto(
        ProjectSummary(
            slug=project.slug,
            name=project.name,
            screen_count=len(project.screens),
            archived=project.archived,
        )
    ).model_dump()


def build_mcp_server(container: Container) -> FastMCP:
    """Build the MCP server over the container's wired use cases."""
    server = FastMCP(
        "protopane",
        instructions=_INSTRUCTIONS,
        streamable_http_path="/",
        stateless_http=True,
        transport_security=_transport_security(),
    )

    @server.tool()
    def get_guide() -> str:
        """Return the long-form reference for authoring on this door, as Markdown:
        what a project, theme, scheme, screen and template are; the closed token set
        and each token's role; the markup rules the write gate enforces; the block
        vocabulary; how palette variants are offered. Read it before the first write."""
        return render_guide(container.list_blocks())

    @server.tool()
    def list_projects(include_archived: bool = False) -> list[dict[str, object]]:
        """List projects (slug, name, screen count, archived flag). Archived projects
        are parked out of this listing by default; pass include_archived to see them."""
        return [
            summary_to_dto(s).model_dump() for s in container.list_projects(include_archived)
        ]

    @server.tool()
    def create_project(name: str, template: str | None = None) -> dict[str, object]:
        """Create a project (optionally from a template slug); returns the new project
        whole (theme, starter screens) with its slug."""
        return project_to_dto(container.create_project(name, template)).model_dump()

    @server.tool()
    def get_project(slug: str) -> dict[str, object]:
        """Return one project whole: its theme tokens, all screens, and any saved schemes."""
        return project_to_dto(container.get_project(slug)).model_dump()

    @server.tool()
    def delete_project(slug: str) -> dict[str, object]:
        """Delete a project and everything it holds; returns the deleted slug."""
        container.delete_project(slug)
        return {"deleted": slug}

    @server.tool()
    def rename_project(
        slug: str, new_slug: str | None = None, new_name: str | None = None
    ) -> dict[str, object]:
        """Rename a project's display name (new_name) and/or its slug (new_slug).

        The slug is the project's identity: renaming it detaches the project from
        whatever joins on the old slug (use this to stop a stale prototype from
        answering for a live repo). An occupied or malformed target slug is
        refused with the reason.

        Returns the project's `list_projects` entry (slug, name, screen count,
        archived flag), under the new slug when one was given.
        """
        return _summary(container.rename_project(slug, new_slug, new_name))

    @server.tool()
    def archive_project(slug: str) -> dict[str, object]:
        """Archive a project: it keeps all its data but drops out of the default
        listing, parked visibly instead of deleted (list with include_archived).
        Returns the project's `list_projects` entry, marked archived."""
        return _summary(container.archive_project(slug))

    @server.tool()
    def unarchive_project(slug: str) -> dict[str, object]:
        """Revive an archived project into the default listing; returns its
        `list_projects` entry."""
        return _summary(container.unarchive_project(slug))

    @server.tool()
    def save_theme(
        slug: str, tokens: dict[str, str], design_system: str | None = None
    ) -> dict[str, object]:
        """Replace the project's design tokens (full shadcn token set, HSL triples).

        When seeding from a packaged design system, pass its library slug as
        `design_system`: the project records that provenance with the system's
        guidance snapshotted verbatim, and the handoff export carries it. Omit it
        for hand-tunes - the recorded provenance survives.

        Returns the saved `tokens` and the `design_system` provenance the project
        now records (slug, name, guidance; null for a hand-authored theme).
        """
        return saved_theme_to_dto(container.save_theme(slug, tokens, design_system)).model_dump()

    @server.tool()
    def save_scheme(
        slug: str, scheme_slug: str, name: str, tokens: dict[str, str]
    ) -> dict[str, object]:
        """Upsert a named palette scheme by slug: a full canonical token set the editor
        re-applies in one click. Use this for design-session palette variants (never a
        sibling project per palette). Gated like the live theme: a partial or off-token
        set is rejected with the violation report. Returns the saved scheme (slug,
        name, tokens).
        """
        saved = container.save_scheme(slug, scheme_slug, name, tokens).scheme(scheme_slug)
        if saved is None:
            raise SchemeNotFoundError(slug, scheme_slug)
        return scheme_to_dto(saved).model_dump()

    @server.tool()
    def delete_scheme(slug: str, scheme_slug: str) -> dict[str, object]:
        """Delete one named scheme by slug (an unknown scheme slug is an error);
        returns the deleted scheme slug."""
        container.delete_scheme(slug, scheme_slug)
        return {"deleted": scheme_slug}

    @server.tool()
    def save_screen(
        slug: str, screen_slug: str, name: str, html: str, css: str = ""
    ) -> dict[str, object]:
        """Upsert one screen by slug: an HTML body in token-backed utility classes.

        The save is gated by token discipline: markup carrying literal colors
        (hex, rgb(), numeric hsl()) is rejected with the violation report.
        Returns the saved screen (slug, name, html, css).
        """
        saved = container.save_screen(slug, screen_slug, name, html, css).screen(screen_slug)
        if saved is None:
            raise ScreenNotFoundError(slug, screen_slug)
        return screen_to_dto(saved).model_dump()

    @server.tool()
    def delete_screen(slug: str, screen_slug: str) -> dict[str, object]:
        """Delete one screen by slug (a project keeps at least one screen); returns
        the deleted screen slug."""
        container.delete_screen(slug, screen_slug)
        return {"deleted": screen_slug}

    @server.tool()
    def export_project(slug: str) -> dict[str, object]:
        """Export the handoff bundle: the theme as a :root CSS block plus screen bodies."""
        return export_to_dto(container.export_project(slug)).model_dump()

    @server.tool()
    def list_templates() -> list[dict[str, object]]:
        """List the starting templates (built-in and saved)."""
        return [template_summary_to_dto(t).model_dump() for t in container.list_templates()]

    @server.tool()
    def get_template(slug: str) -> dict[str, object]:
        """Return one template's HTML body."""
        return template_to_dto(container.get_template(slug)).model_dump()

    @server.tool()
    def save_template(name: str, html: str) -> dict[str, object]:
        """Save an HTML body as a reusable starting template (gated by token discipline);
        returns the saved template."""
        return template_to_dto(container.save_template(name, html)).model_dump()

    @server.tool()
    def delete_template(slug: str) -> dict[str, object]:
        """Delete a saved template (the built-in set cannot be deleted); returns the
        deleted slug."""
        container.delete_template(slug)
        return {"deleted": slug}

    @server.tool()
    def list_blocks() -> list[dict[str, object]]:
        """List the palette blocks (label, category, token-backed HTML) screens are
        assembled from; compose from these so every element has a real-component
        counterpart at handoff."""
        return [block_to_dto(b).model_dump() for b in container.list_blocks()]

    @server.tool()
    def list_design_systems() -> list[dict[str, object]]:
        """List the vendored design systems, read-only reference palettes to seed a
        project's theme or a scheme from: each system's slug, name and category.
        get_design_system reads one system's tokens and guidance."""
        return [
            design_system_to_dto(d).model_dump(include=_DESIGN_SYSTEM_SUMMARY)
            for d in container.list_design_systems()
        ]

    @server.tool()
    def get_design_system(slug: str) -> dict[str, object]:
        """Return one vendored design system by slug: its slug, name, category, the
        19-key shadcn token set, the non-color guidance, and its source. An unknown
        slug is refused with the reason."""
        return design_system_to_dto(container.get_design_system(slug)).model_dump()

    @server.prompt(
        name="bootstrap-project",
        title="Bootstrap a client prototype",
        description=(
            "Stand up a themed, populated prototype from a brief: create the "
            "project, refine the brand tokens, author the first screens, offer "
            "palette variants, and hand back the editor link."
        ),
    )
    def bootstrap_project(
        name: str, brief: str, template: str | None = None, primary: str | None = None
    ) -> str:
        """The guide's build flow as a runbook, parametrized with the brief and the
        instance's live facts."""
        if template is not None:
            container.get_template(template)  # unknown template -> prompt error
        if primary is not None and not _HEX_RE.match(primary):
            raise ValueError(f"primary must be #RRGGBB hex, got: {primary}")
        available = ", ".join(t.slug for t in container.list_templates())
        create_args = f"name='{name}'" + (f", template='{template}'" if template else "")
        return (
            "Build a client prototype in this protopane instance from the brief "
            f"below (templates available on this instance: {available}). Read "
            "get_guide first: it holds the token set, the markup rules the write gate "
            "enforces, and the blocks these steps compose from.\n\n"
            f"Brief: {brief}\n\n"
            + render_flow(f"`{create_args}`", primary)
            + "\nHand back the editor link. The result is a throwaway design reference "
            "for the eventual real frontend build, not a maintained artifact."
        )

    return server
