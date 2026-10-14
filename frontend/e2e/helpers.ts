import { expect, type Page } from '@playwright/test';

/** Create a project via the API (proxied through Vite) and return its slug. */
export async function createProject(page: Page, name: string): Promise<string> {
    const res = await page.request.post('/api/projects', { data: { name } });
    expect(res.ok()).toBeTruthy();
    const body = (await res.json()) as { slug: string };
    return body.slug;
}

/** Open a project's editor and wait for the builder to mount. */
export async function openEditor(page: Page, slug: string): Promise<void> {
    await page.goto(`/p/${slug}`);
    await page.locator('.gjs-editor').waitFor({ state: 'visible', timeout: 20_000 });
}

export function canvasButton(page: Page, name: string) {
    return page.frameLocator('iframe.gjs-frame').getByRole('button', { name });
}
