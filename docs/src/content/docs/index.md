---
title: protopane
id: DOC-PROTOPANE-001
type: Overview
status: Active
updated: "2026-08-27"
summary: What protopane is and how a client prototype flows from theme to handoff.
---

protopane is a multi-project visual prototyping hub, the workshop of the delivery lifecycle's Design phase. You theme a shadcn/ui component set to a customer's brand on a live canvas, build screens by dragging blocks, and keep each client as its own project; a design agent drives the same capabilities over MCP. The theme and markup export to hand off into a real React frontend.

## What it does

- **Theme**: change colours, radius, and dark mode on a live canvas; every component reskins as the customer watches. Vendored **design systems** (read-only reference palettes with the full shadcn token set) seed a theme, and **colour schemes** hold named variants beside it.
- **Build**: drag shadcn-styled blocks (buttons, cards, inputs, badges, layout grids) onto a free canvas.
- **Persist**: each client is a project (its theme, schemes, and screens), saved to disk and reopenable; projects **rename**, **archive**, and **unarchive** without losing state.
- **Hand off**: export the theme as a `:root` CSS block and the screen markup, both in your production Tailwind vocabulary.
- **Tell**: every persisted change publishes a fact to the platform event bus where the instance holds a grant (theme saved, scheme saved or deleted, project archived or unarchived); [Events](events/) carries the catalogue.

## Shape

- **Backend** (`protopane/`): a hexagonal FastAPI service (domain / application / adapters), file-backed, exposed under `/api`.
- **MCP door** (`protopane/adapters/inbound/mcp`): the same use cases as tools at `/mcp`, the `get_guide` reference an agent authors from, and the `bootstrap-project` prompt (the design-session runbook); see [Architecture](architecture/) for the tool list.
- **Frontend** (`frontend/`): a React + Vite + Tailwind SPA embedding the GrapesJS canvas, served as static files by the backend in the built image.
- **Run paths**: `devops/docker-compose.yml` brings up the whole solution in one container; the native dev path is documented in the repository `README.md`.

## Deployment

protopane follows the Foundry app contract (the platform's ADR-018): `devops/` for the image and local run, `k8s/` for the Helm chart, and this `docs/` site for the central docs portal, served at `protopane.<zone>` on the install that runs it. Project files persist on a `/data` volume. Deployed with the chart's OIDC gate (the default), oauth2-proxy fronts the human surfaces and fail-closed HTTP Basic narrows to the `/mcp` machine door (`PROTOPANE_AUTH_SCOPE=mcp`).
