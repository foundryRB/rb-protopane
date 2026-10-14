# syntax=docker/dockerfile:1

# Stage 1: build the React SPA (the canvas builder + project hub).
FROM node:22-slim AS web
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
# The e2e-only deps (@playwright/test, playwright, playwright-intent) are not needed
# for the build. Drop them so npm install resolves with just the build dependencies.
RUN node -e "const p=require('./package.json'); for (const k of ['@psa-department-of-engineering/playwright-intent','@playwright/test','playwright']) delete (p.devDependencies||{})[k]; require('fs').writeFileSync('package.json', JSON.stringify(p,null,2));" \
    && npm install
COPY frontend ./
RUN npm run build

# Stage 2: runtime. Python serves the API and the built SPA from a single image.
FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PROTOPANE_HOST=0.0.0.0 \
    PROTOPANE_PORT=8800 \
    PROTOPANE_PROJECTS_DIR=/data/projects \
    PROTOPANE_FRONTEND_DIST=/app/frontend/dist
# Optionally bundle claude-agent-sdk (the local design chat). Off by default so the
# published hub image stays lean and agent-free; docker-compose sets it true. The SDK
# ships a self-contained native claude binary, so no Node runtime is needed here.
ARG INCLUDE_AGENT=false
COPY pyproject.toml ./
COPY protopane ./protopane
RUN if [ "$INCLUDE_AGENT" = "true" ]; then \
        pip install --no-cache-dir -e ".[agent]"; \
    else \
        pip install --no-cache-dir -e .; \
    fi
COPY --from=web /app/frontend/dist ./frontend/dist
RUN mkdir -p /data/projects
EXPOSE 8800
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8800/api/health').read()" || exit 1
CMD ["python", "-m", "uvicorn", \
     "protopane.adapters.inbound.http.app:create_app", \
     "--factory", "--host", "0.0.0.0", "--port", "8800"]
