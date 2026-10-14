---
title: Architecture
id: DOC-PROTOPANE-002
type: Reference
status: Active
updated: "2026-10-09"
summary: How protopane's layers fit together and how a request flows through them.
---

protopane is a hexagonal (ports and adapters) FastAPI backend plus a React SPA. The backend owns project state; the SPA is the visual editor, and MCP agents are a third client over the same core.

## Layers

```text
domain        Project, Theme, Scheme, Screen, ProjectExport, Template, Block, DesignSystem,
              exceptions   (no outward imports)
application   ports (ProjectRepository, TemplateRepository, BlockLibrary, DesignSystemLibrary,
              ProjectChangeNotifier, EventPublisher, DesignAgent)
              + use cases (list/create/get/delete/rename/archive/unarchive project, save-theme,
              save-scheme, delete-scheme, save-screen, delete-screen, export, templates,
              list-blocks, list/get design-system)
adapters      inbound/http (FastAPI routers, DTOs, mappers)  ·  inbound/mcp (tools mirroring the use cases)
              outbound/persistence (file repositories)  ·  outbound/blocks  ·  outbound/design_systems
              outbound/events (the bus publisher)  ·  outbound/notify  ·  outbound/agent (optional)
container     composition root: builds the adapters, wires the use cases, decides capabilities
```

The dependency rule points inward: `domain` depends on nothing, `application` defines the port Protocols, and the adapters implement and call them through the `Container`.

## Request flow

Every door drives the same use case, so a write is identical whether it arrives from the SPA, a REST call, or an MCP tool:

```text
Browser (React SPA, GrapesJS canvas)      MCP agent (streamable HTTP at /mcp)
  -> /api/projects/{slug}/theme             -> save_theme tool
       (HTTP route, DTO)                         (same DTO mappers)
                    \                       /
                     -> SaveTheme use case
                     -> ProjectRepository.save  (FileProjectRepository)
                     -> projects/{slug}/project.json
```

## Token discipline

Every write is gated in the use cases by token discipline: screen and template markup carrying a literal color (hex, `rgb()`, numeric `hsl()`) is rejected with a violation report, and a theme save must carry exactly the canonical token set with well-formed values. Because the gate lives in the use case, it holds identically on the UI, the REST API, and MCP: only token-backed markup, which reskins live and survives handoff, ever persists. The block vocabulary the screens are assembled from is served by the instance (`GET /api/blocks` and the `list_blocks` tool), so every door builds from the same set.

## MCP door

The MCP server mounts at `/mcp` on the same FastAPI app (streamable HTTP, stateless), behind the fail-closed HTTP Basic gate (the machine door keeps Basic even when the chart's oauth2-proxy fronts the human surfaces, `PROTOPANE_AUTH_SCOPE=mcp`). `get_guide` serves the door's own reference; every other tool mirrors an inbound use case one-to-one. Tools returning domain data serialize through the HTTP DTO mappers; `delete_project`, `delete_scheme`, `delete_screen` and `delete_template` return `{"deleted": "<slug>"}`, naming the removed item:

| Tool | Does |
|---|---|
| `get_guide` | The long-form reference an agent authors from: the model, the closed token set and each token's role, the markup rules the write gate enforces, the phone layout rules, the block vocabulary with each phone block's behaviour, and how palette variants are offered. The server's instructions name it. |
| `list_projects` / `get_project` | The project list (optionally with archived), one project's full state. |
| `create_project` / `delete_project` / `rename_project` | The project lifecycle, optionally seeding from a template. |
| `archive_project` / `unarchive_project` | Park a client's prototype and bring it back, state intact. |
| `save_theme` | Persist the full canonical token set (token discipline gates it). |
| `save_scheme` / `delete_scheme` | Named colour-scheme variants beside the theme. |
| `save_screen` / `delete_screen` | Screen markup (token discipline gates it). |
| `export_project` | The handoff: the `:root` CSS block and the screen markup. |
| `list_templates` / `get_template` / `save_template` / `delete_template` | The reusable starting points. |
| `list_blocks` | The block vocabulary every door builds screens from. |
| `list_design_systems` / `get_design_system` | The vendored read-only reference palettes to seed a theme or scheme from: the listing names each system (slug, name, category), and a read by slug returns one whole (its full shadcn token set and non-color guidance). |

A write answers with what it wrote: `save_screen` returns the saved screen, `save_scheme` the saved scheme, `save_theme` the saved tokens and the recorded design-system provenance, each delete the slug it removed, and `rename_project`, `archive_project` and `unarchive_project` the project's `list_projects` entry. `get_project` and `export_project` are the reads that return the project whole.

The `bootstrap-project` prompt renders the guide's build flow (create, theme from the brief and optional primary colour, author the first screens, offer palette variants as schemes, export and hand back the editor link) as a runbook the connected agent executes. Connect with:

```bash
claude mcp add --scope user --transport http protopane https://protopane.<zone>/mcp --header "Authorization: Basic <credential>"
```

## Persistence

Each project is one JSON document at `<PROTOPANE_PROJECTS_DIR>/<slug>/project.json`, holding the slug, name, theme tokens, colour schemes, screens (each a GrapesJS html + css export), and the archived flag. The default `PROTOPANE_PROJECTS_DIR` is `projects/`; in the container it is `/data/projects` on a persistent volume.

## Frontend

The SPA hosts a project list and a per-project editor. The editor embeds GrapesJS with a self-hosted Tailwind runtime injected into the canvas iframe, so dropped shadcn markup renders themed and offline. Theme tokens are applied to the canvas as inline CSS variables; saving persists the tokens and the current screen markup back through `/api`.

## Intent

Correctness is pinned by CSD intent claims in the root `intent.yaml`: backend claims (`INT-PP-Bnn`) attested by `pytest-intent`, end-to-end claims (`INT-PP-Enn`) attested by `playwright-intent`, audited cross-runtime by `csd-intent`.
