import { defineConfig, devices } from '@playwright/test';

// Backend command is overridable so CI / non-Windows can point at their interpreter.
const backendCmd =
    process.env.PROTOPANE_BACKEND_CMD ?? '..\\.venv\\Scripts\\python.exe -m protopane';

/**
 * Playwright config for protopane's e2e intent tests. Starts (or reuses) both the
 * FastAPI backend on :8000 and the Vite dev server on :5180 (which proxies /api).
 */
export default defineConfig({
    testDir: './e2e',
    timeout: 40_000,
    fullyParallel: false,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: 1,
    reporter: [['list']],
    use: {
        baseURL: 'http://localhost:5180',
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
    },
    projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
    webServer: [
        {
            command: backendCmd,
            url: 'http://127.0.0.1:8800/api/health',
            reuseExistingServer: !process.env.CI,
            timeout: 60_000,
            env: {
                PROTOPANE_HOST: '127.0.0.1',
                PROTOPANE_PORT: '8800',
                PROTOPANE_PROJECTS_DIR: '.e2e-projects',
                PROTOPANE_FRONTEND_DIST: 'no-dist',
                // The e2e suite exercises the UI workflow, not auth; auth itself is
                // covered by the backend tests. Run the dev backend open.
                PROTOPANE_AUTH_DISABLED: 'true',
            },
        },
        {
            command: 'npm run dev -- --port 5180 --strictPort',
            url: 'http://localhost:5180',
            reuseExistingServer: !process.env.CI,
            timeout: 30_000,
        },
    ],
});
