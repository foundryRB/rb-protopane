import { expect } from '@playwright/test';
import { intent } from '@psa-department-of-engineering/playwright-intent';

import { createProject, openEditor } from './helpers';

intent('INT-PP-E12', 'creating a project from a template opens it with that content', async ({ page }) => {
    await page.goto('/');
    await page.getByPlaceholder('New project name').fill(`e2e-tpl-${Date.now()}`);
    await page.getByLabel('Template', { exact: true }).selectOption('landing');
    await page.getByRole('button', { name: 'New project' }).click();

    await expect(page.locator('.gjs-editor')).toBeVisible({ timeout: 20_000 });
    // The landing template's distinctive heading proves the project started from it.
    await expect(
        page.frameLocator('iframe.gjs-frame').getByText('Ship a branded UI in minutes')
    ).toBeVisible({
        timeout: 20_000,
    });
});

intent(
    'INT-PP-E28',
    'in the Mobile canvas the landing, dashboard and analytics templates show their nav and do not scroll sideways',
    async ({ page }) => {
        const navs: [string, string[]][] = [
            ['landing', ['Features', 'Pricing', 'Docs']],
            ['dashboard', ['Overview', 'Customers', 'Settings']],
            ['analytics', ['Traffic', 'Conversion', 'Retention']],
        ];
        for (const [template, links] of navs) {
            const res = await page.request.post('/api/projects', {
                data: { name: `e2e-phone-${template}-${Date.now()}`, template },
            });
            expect(res.ok()).toBeTruthy();
            const { slug } = (await res.json()) as { slug: string };
            await openEditor(page, slug);
            const frame = page.locator('iframe.gjs-frame');
            await page.getByRole('button', { name: 'Mobile' }).click();
            await expect
                .poll(() => frame.evaluate((el) => Math.round(el.getBoundingClientRect().width)))
                .toBe(390);

            const canvas = page.frameLocator('iframe.gjs-frame');
            // The canvas's Tailwind runtime has styled the header before the nav is judged.
            await expect(canvas.locator('header').first()).toHaveCSS('display', 'flex');
            const nav = canvas.locator('header nav').first();
            for (const link of links) {
                await expect(
                    nav.getByText(link, { exact: true }),
                    `${template}: ${link}`,
                ).toBeVisible();
            }
            const overflow = await frame.evaluate((el) => {
                const doc = (el as HTMLIFrameElement).contentDocument as Document;
                return [doc.documentElement, doc.body].map(
                    (box) => box.scrollWidth - box.clientWidth,
                );
            });
            expect(overflow, `${template} scrolls sideways`).toEqual([0, 0]);
        }
    },
);

intent('INT-PP-E13', 'saving a screen as a template makes it available on the hub', async ({ page }) => {
    const unique = `Tpl ${Date.now()}`;
    const slug = await createProject(page, unique);
    await openEditor(page, slug);

    await page.getByRole('button', { name: 'Save as template' }).click();
    await expect(page.getByRole('button', { name: 'Saved as template' })).toBeVisible();

    await page.goto('/');
    const option = page.getByLabel('Template', { exact: true }).locator('option', { hasText: unique });
    await expect(option).toHaveCount(1);
});
