# protopane

The packaged design-system catalog includes RB Software Engineering in Dark and Light. Their sources live in this repository ([design-systems/](design-systems/README.md)); `python design-systems/generate.py` projects them into the packaged presets, and `--check` verifies the projection. The public HTTP and MCP library reads expose them alongside the existing reference systems. Deploy the updated package to update the live library.

A multi-project visual prototyping hub. Theme a shadcn/ui component set to a customer's brand on a live canvas, build screens by dragging blocks, and keep each client as its own project. Export the theme and markup to hand off into a real React frontend.

## Run with Docker

The frontend build and the Python runtime are produced inside the image, so Docker is the only prerequisite.

```bash
docker compose -f devops/docker-compose.yml up --build
```

The hub listens on http://localhost:8800. Client projects persist in the `protopane-data` named volume. `.env.example` documents the (optional) configuration variables; protopane needs no secrets.

## Develop without Docker

Backend (hexagonal FastAPI, port 8800):

```bash
python -m venv .venv
.venv\Scripts\activate           # POSIX: source .venv/bin/activate
pip install -e ".[dev]"
python -m protopane              # http://127.0.0.1:8800
```

Frontend (Vite dev server, proxies `/api` to the backend):

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5180
```

Test, lint, and audit:

```bash
python -m pytest                 # backend unit + integration
ruff check protopane tests       # backend lint
cd frontend && npx playwright test   # e2e (starts the backend + frontend itself)
csd-intent .                     # validate intent.yaml + cross-runtime coverage
```

Conventional Commits are enforced by a bypassable local `commit-msg` hook (committed as
`.pre-commit-config.yaml`); the convention is what semantic-release reads to cut the image
and chart version (ADR-024). Install it once per clone:

```bash
pip install pre-commit
pre-commit install --install-hooks
```

A non-conforming message is rejected; `git commit --no-verify` bypasses it when needed.

## Access control

protopane gates every route with HTTP Basic auth and fails closed: it refuses to
serve protected routes unless credentials are configured, so a misconfigured
instance is never silently exposed. The health endpoint stays open so probes work.

- Production: set `PROTOPANE_AUTH_USER` and `PROTOPANE_AUTH_PASSWORD` (injected as a
  Kubernetes Secret by the chart; see `k8s/values.yaml` `auth.existingSecret`).
- Local dev and tests: set `PROTOPANE_AUTH_DISABLED=true` to run without a prompt.

See `.env.example` for the variables.

## MCP (agents as a third client)

The backend serves MCP over streamable HTTP at `/mcp`, on the same app and behind
the same fail-closed Basic auth as everything else. Tools mirror the project and
template use cases one-to-one, `get_guide` returns the long-form reference an agent
authors from (the model, the token set, the markup rules, the blocks), and the
`bootstrap-project` prompt renders the guide's build flow (create, theme, author
screens, offer schemes, export) as a runbook the connected agent executes. Connect an agent
with:

```bash
claude mcp add --scope user --transport http protopane https://<host>/mcp --header "Authorization: Basic <credential>"
```

A deployment must allow its public hostname through the transport's DNS-rebinding
guard via `PROTOPANE_MCP_ALLOWED_HOSTS` (the chart sets it); leave it unset locally.

## Design chat (local only)

The editor can embed a Claude design agent that edits the current screen from a chat
prompt, with the canvas hot-reloading as it works. It runs through `claude-agent-sdk` on
**your** Claude subscription, so it is a local-machine capability: gated behind a feature
flag and deliberately absent from the hosted hub (the k8s chart never enables it). It is
off unless `PROTOPANE_AGENT_ENABLED=true`.

1. Mint a subscription token with `claude setup-token` (Pro/Max). On a host where you are
   already logged into Claude Code, `python -m protopane` can use that login directly.
2. For Docker, put the token in `devops/.env` (gitignored) as `CLAUDE_CODE_OAUTH_TOKEN=...`.
   The compose file enables the agent and bundles the SDK into the image. Never set
   `ANTHROPIC_API_KEY` - it silently wins over the token and bills the metered API.
3. `docker compose -f devops/docker-compose.yml up --build`. The chat rail appears in the
   editor; the hosted hub reports `chatEnabled: false` and never mounts the route.

## Backups

Client projects are plain JSON files under `PROTOPANE_PROJECTS_DIR` (the `/data`
volume in the container), one folder per project, written atomically. Back them up
by snapshotting that volume or copying the directory, and restore by copying it
back. Each project also exports a portable theme + markup bundle via
`GET /api/projects/<slug>/export`. Scheduling and off-site copies are a platform
concern (the cluster snapshots the volume), not the app's.

## Layout

- `protopane/domain` - entities and value objects (Project, Theme, Screen, Block), the token-discipline lint, exceptions; no outward imports
- `protopane/application` - the port Protocols and the use cases (list / create / get / delete / save-theme / save-screen / export / templates / blocks)
- `protopane/adapters/inbound/http` - FastAPI app factory, routers, DTOs, mappers
- `protopane/adapters/inbound/mcp` - MCP server: tools mirroring the use cases, mounted at `/mcp`
- `protopane/adapters/outbound/persistence` - the file-based project and template repositories
- `protopane/adapters/outbound/blocks` - the packaged block vocabulary served at `/api/blocks`
- `protopane/container.py` - composition root
- `frontend/` - React + Vite + Tailwind SPA embedding the GrapesJS canvas; served as static files by the backend in the built image
- `devops/` - multi-stage Dockerfile and docker-compose
- `k8s/` - Helm chart for the rb-foundry.com install
- `docs/` - Starlight documentation site
- `intent.yaml` - CSD intent claims, attested by `pytest-intent` (backend) and `playwright-intent` (e2e)

## Learn more

Architecture follows the shared `REF-CleanArchitecture`, `REF-FastAPI`, `REF-Frontend`, and `REF-Python` references. Intent testing uses `pytest-intent` + `playwright-intent`, audited by the `csd-intent` CLI.

## Commits

Every commit follows the platform's commit convention: a Conventional Commit
subject and no co-author trailer. CI derives the version from the type and
blocks release otherwise. The convention is documented on the platform
portal's GitOps delivery page, under "Commit convention"; the committed
`.pre-commit-config.yaml` checks it locally once installed (`pre-commit install`).
