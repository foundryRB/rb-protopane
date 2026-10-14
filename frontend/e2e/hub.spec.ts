import { expect } from '@playwright/test';
import { intent } from '@psa-department-of-engineering/playwright-intent';

import { canvasButton, createProject, openEditor } from './helpers';

intent('INT-PP-E07', 'creating a project from the hub opens it and lists it', async ({ page }) => {
    await page.goto('/');
    const name = `e2e-new-${Date.now()}`;
    await page.getByPlaceholder('New project name').fill(name);
    await page.getByRole('button', { name: 'New project' }).click();

    await expect(page.locator('.gjs-editor')).toBeVisible({ timeout: 20_000 });

    await page.goto('/');
    await expect(page.getByText(name)).toBeVisible();
});

intent('INT-PP-E08', 'a theme set on a project persists across reload', async ({ page }) => {
    const slug = await createProject(page, `e2e-theme-${Date.now()}`);
    await openEditor(page, slug);
    const primary = canvasButton(page, 'Primary');
    await expect(primary).toBeVisible({ timeout: 20_000 });
    const original = await primary.evaluate((el) => getComputedStyle(el).backgroundColor);

    await page.getByRole('button', { name: 'Violet' }).click();
    await page.waitForTimeout(400);
    await page.getByRole('button', { name: 'Save', exact: true }).click();
    await page.waitForTimeout(600);

    await page.reload();
    const reloaded = canvasButton(page, 'Primary');
    await expect(reloaded).toBeVisible({ timeout: 20_000 });
    const persisted = await reloaded.evaluate((el) => getComputedStyle(el).backgroundColor);
    // If the saved theme did not persist, the reload would show the original default.
    expect(persisted).not.toBe(original);
});

intent('INT-PP-E09', 'editing and saving a screen persists across reload', async ({ page }) => {
    const slug = await createProject(page, `e2e-screen-${Date.now()}`);
    await openEditor(page, slug);
    // Wait for the starter screen to finish loading so it doesn't overwrite our edit.
    await expect(page.frameLocator('iframe.gjs-frame').getByText('Welcome')).toBeVisible({
        timeout: 20_000,
    });
    const marker = `Edited-${Date.now()}`;
    await page.evaluate((text) => {
        const w = window as unknown as {
            __protopaneEditor?: { setComponents: (html: string) => void };
        };
        w.__protopaneEditor?.setComponents(`<h1>${text}</h1>`);
    }, marker);

    await page.getByRole('button', { name: 'Save', exact: true }).click();
    await page.waitForTimeout(600);
    await page.reload();

    await expect(page.frameLocator('iframe.gjs-frame').getByText(marker)).toBeVisible({
        timeout: 20_000,
    });
});

intent('INT-PP-E10', 'deleting a project removes it from the hub', async ({ page }) => {
    const slug = await createProject(page, `e2e-del-${Date.now()}`);
    await page.goto('/');
    const card = page.locator(`[data-slug="${slug}"]`);
    await expect(card).toBeVisible();

    await card.getByRole('button', { name: 'Delete' }).click();
    await expect(page.locator(`[data-slug="${slug}"]`)).toHaveCount(0);
});

intent('INT-PP-E18', 'renaming a project from the hub shows the new name', async ({ page }) => {
    const slug = await createProject(page, `e2e-ren-${Date.now()}`);
    await page.goto('/');
    const card = page.locator(`[data-slug="${slug}"]`);
    await card.getByRole('button', { name: 'Rename' }).click();
    await card.getByLabel(`New name for ${slug}`).fill('Renamed Prototype');
    await card.getByRole('button', { name: 'Save name' }).click();
    await expect(card.getByText('Renamed Prototype')).toBeVisible();
});

intent('INT-PP-E19', 'archiving parks a project; unarchiving revives it', async ({ page }) => {
    const slug = await createProject(page, `e2e-arch-${Date.now()}`);
    await page.goto('/');
    const card = page.locator(`[data-slug="${slug}"]`);
    await card.getByRole('button', { name: 'Archive' }).click();

    // The card leaves the active grid for the visible archived section.
    const archivedCard = page.getByTestId('archived-projects').locator(`[data-slug="${slug}"]`);
    await expect(archivedCard).toBeVisible();

    await archivedCard.getByRole('button', { name: 'Unarchive' }).click();
    await expect(
        page.getByTestId('archived-projects').locator(`[data-slug="${slug}"]`),
    ).toHaveCount(0);
    await expect(page.locator(`[data-slug="${slug}"]`)).toBeVisible();
});

intent('INT-PP-E14', 'the hub surfaces the MCP connect command', async ({ page }) => {
    await page.goto('/');
    const card = page.getByTestId('connect-agent');
    await expect(card).toBeVisible();
    await expect(card.getByText('claude mcp add --scope user --transport http protopane')).toBeVisible();
    await expect(card.getByRole('button', { name: 'Copy command' })).toBeVisible();
});

intent('INT-PP-E17', 'a saved template can be deleted from the hub', async ({ page }) => {
    const unique = `TplDel ${Date.now()}`;
    const slug = await createProject(page, unique);
    await openEditor(page, slug);
    await page.getByRole('button', { name: 'Save as template' }).click();
    await expect(page.getByRole('button', { name: 'Saved as template' })).toBeVisible();

    await page.goto('/');
    // Built-ins offer no delete control; the saved one does.
    await expect(page.getByRole('button', { name: 'Delete template Landing page' })).toHaveCount(0);
    await page.getByRole('button', { name: `Delete template ${unique}`, exact: true }).click();
    await expect(page.getByRole('button', { name: `Delete template ${unique}` })).toHaveCount(0);
    const option = page.getByLabel('Template', { exact: true }).locator('option', { hasText: unique });
    await expect(option).toHaveCount(0);
});

intent('INT-PP-E15', 'deleting a page removes it; the last page is protected', async ({ page }) => {
    const slug = await createProject(page, `e2e-delpage-${Date.now()}`);
    await openEditor(page, slug);

    // A single page offers no delete control.
    await expect(page.getByRole('button', { name: /Delete page/ })).toHaveCount(0);

    await page.getByRole('button', { name: '+ Page' }).click();
    await expect(page.getByRole('button', { name: 'Page 2', exact: true })).toBeVisible();

    page.on('dialog', (dialog) => void dialog.accept());
    await page.getByRole('button', { name: 'Delete page Page 2', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Page 2', exact: true })).toHaveCount(0);
    await expect(page.getByRole('button', { name: /Delete page/ })).toHaveCount(0);
});

intent(
    'INT-PP-E21',
    'clicking Refresh pulls a server-side change without a full reload',
    async ({ page }) => {
        const slug = await createProject(page, `e2e-refresh-${Date.now()}`);
        await openEditor(page, slug);
        await expect(page.frameLocator('iframe.gjs-frame').getByText('Welcome')).toBeVisible({
            timeout: 20_000,
        });

        // Simulate a change made through a separate design session (the ticket's scenario):
        // update the screen directly via the API, bypassing this page's own save.
        const marker = `Refreshed-${Date.now()}`;
        const res = await page.request.put(`/api/projects/${slug}/screens/home`, {
            data: { name: 'Home', html: `<h1>${marker}</h1>`, css: '' },
        });
        expect(res.ok()).toBeTruthy();

        const urlBefore = page.url();
        await page.getByRole('button', { name: 'Refresh' }).click();
        await expect(page.frameLocator('iframe.gjs-frame').getByText(marker)).toBeVisible({
            timeout: 20_000,
        });
        expect(page.url()).toBe(urlBefore);
    },
);

intent(
    'INT-PP-E22',
    'refreshing with unsaved local edits confirms before discarding them',
    async ({ page }) => {
        const slug = await createProject(page, `e2e-refresh-dirty-${Date.now()}`);
        await openEditor(page, slug);
        await expect(page.frameLocator('iframe.gjs-frame').getByText('Welcome')).toBeVisible({
            timeout: 20_000,
        });

        // Edit the canvas locally, without saving.
        const localEdit = `Local-${Date.now()}`;
        await page.evaluate((text) => {
            const w = window as unknown as {
                __protopaneEditor?: { setComponents: (html: string) => void };
            };
            w.__protopaneEditor?.setComponents(`<h1>${text}</h1>`);
        }, localEdit);

        // A separate session saves a server-side change in the meantime.
        const serverMarker = `Server-${Date.now()}`;
        await page.request.put(`/api/projects/${slug}/screens/home`, {
            data: { name: 'Home', html: `<h1>${serverMarker}</h1>`, css: '' },
        });

        // Dismissing the confirm keeps the local, unsaved edit intact.
        page.once('dialog', (dialog) => void dialog.dismiss());
        await page.getByRole('button', { name: 'Refresh' }).click();
        await expect(page.frameLocator('iframe.gjs-frame').getByText(localEdit)).toBeVisible();

        // Accepting the confirm pulls the server version, discarding the local edit.
        page.once('dialog', (dialog) => void dialog.accept());
        await page.getByRole('button', { name: 'Refresh' }).click();
        await expect(page.frameLocator('iframe.gjs-frame').getByText(serverMarker)).toBeVisible({
            timeout: 20_000,
        });
    },
);

intent(
    'INT-PP-E23',
    'switching to an untouched page on a multi-page project then refreshing does not prompt for unsaved changes',
    async ({ page }) => {
        const slug = await createProject(page, `e2e-refresh-switch-${Date.now()}`);
        // A second page, persisted server-side before the editor ever loads it - the
        // "never touched" page from the finding's repro, as opposed to one created
        // in-session via + Page (which the active page becomes immediately, never
        // exercising switchTo).
        const otherMarker = `Other-${Date.now()}`;
        const res = await page.request.put(`/api/projects/${slug}/screens/other`, {
            data: { name: 'Other', html: `<section><p>${otherMarker}</p></section>`, css: '' },
        });
        expect(res.ok()).toBeTruthy();

        await openEditor(page, slug);
        await expect(page.frameLocator('iframe.gjs-frame').getByText('Welcome')).toBeVisible({
            timeout: 20_000,
        });

        // Switch to the untouched second page without editing it.
        await page.getByRole('button', { name: 'Other', exact: true }).click();
        await expect(page.frameLocator('iframe.gjs-frame').getByText(otherMarker)).toBeVisible({
            timeout: 20_000,
        });

        // No dialog should appear; fail loudly if one does (an unsaved-changes false positive).
        let dialogAppeared = false;
        page.on('dialog', (dialog) => {
            dialogAppeared = true;
            void dialog.dismiss();
        });
        await page.getByRole('button', { name: 'Refresh' }).click();
        await expect(page.getByRole('button', { name: 'Refreshing...' })).toHaveCount(0);
        expect(dialogAppeared).toBe(false);
    },
);

intent(
    'INT-PP-E24',
    'deleting the active page and landing on an untouched page then refreshing does not prompt for unsaved changes',
    async ({ page }) => {
        const slug = await createProject(page, `e2e-refresh-delete-${Date.now()}`);
        // A second page, persisted server-side before the editor ever loads it - never
        // activated, so deletePage lands the canvas on it without it ever having been
        // round-tripped through the editor before (the same gap switchTo had).
        const otherMarker = `Other-${Date.now()}`;
        const res = await page.request.put(`/api/projects/${slug}/screens/other`, {
            data: { name: 'Other', html: `<section><p>${otherMarker}</p></section>`, css: '' },
        });
        expect(res.ok()).toBeTruthy();

        await openEditor(page, slug);
        await expect(page.frameLocator('iframe.gjs-frame').getByText('Welcome')).toBeVisible({
            timeout: 20_000,
        });

        // Delete the active page (Home); deletePage lands on "Other" without ever
        // having switched to it.
        page.once('dialog', (dialog) => void dialog.accept());
        await page.getByRole('button', { name: 'Delete page Home', exact: true }).click();
        await expect(page.frameLocator('iframe.gjs-frame').getByText(otherMarker)).toBeVisible({
            timeout: 20_000,
        });

        // No dialog should appear; fail loudly if one does (an unsaved-changes false positive).
        let dialogAppeared = false;
        page.on('dialog', (dialog) => {
            dialogAppeared = true;
            void dialog.dismiss();
        });
        await page.getByRole('button', { name: 'Refresh' }).click();
        await expect(page.getByRole('button', { name: 'Refreshing...' })).toHaveCount(0);
        expect(dialogAppeared).toBe(false);
    },
);
