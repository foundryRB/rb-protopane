import { expect } from '@playwright/test';
import { intent } from '@psa-department-of-engineering/playwright-intent';

import { canvasButton, createProject, openEditor } from './helpers';

// The canonical 19-key shadcn set every theme carries; the fixture systems override
// only their accent colours so the save path (token discipline) accepts them.
const BASE_TOKENS: Record<string, string> = {
    '--background': '0 0% 100%',
    '--foreground': '222 47% 11%',
    '--card': '0 0% 100%',
    '--card-foreground': '222 47% 11%',
    '--primary': '217 91% 60%',
    '--primary-foreground': '0 0% 100%',
    '--secondary': '210 40% 96%',
    '--secondary-foreground': '222 47% 11%',
    '--muted': '210 40% 96%',
    '--muted-foreground': '215 16% 47%',
    '--accent': '210 40% 94%',
    '--accent-foreground': '222 47% 11%',
    '--destructive': '0 72% 51%',
    '--destructive-foreground': '0 0% 100%',
    '--border': '214 32% 88%',
    '--input': '214 32% 88%',
    '--ring': '217 91% 60%',
    '--radius': '0.5rem',
    '--font-sans': "ui-sans-serif, system-ui, 'Segoe UI', Roboto, sans-serif",
};

// Two fixtures with distinctive primaries, so "Apply as theme" is a visible reskin.
const SYSTEMS = [
    {
        slug: 'playwright-emerald',
        name: 'Playwright Emerald',
        category: 'Test Fixture',
        tokens: {
            ...BASE_TOKENS,
            '--primary': '152 76% 40%',
            '--ring': '152 76% 40%',
            '--accent': '152 55% 92%',
        },
        guidance: '## Voice\nCalm, botanical, precise.',
        source: 'e2e/fixture/emerald',
    },
    {
        slug: 'playwright-grape',
        name: 'Playwright Grape',
        category: 'Test Fixture',
        tokens: {
            ...BASE_TOKENS,
            '--primary': '280 80% 55%',
            '--ring': '280 80% 55%',
            '--accent': '280 60% 93%',
        },
        guidance: '## Voice\nBold, vivid, expressive.',
        source: 'e2e/fixture/grape',
    },
];

intent(
    'INT-PP-E20',
    'the design-systems gallery renders swatches and applies a system as the theme',
    async ({ page }) => {
        // Mock the library so the gallery is deterministic regardless of what is vendored.
        await page.route('**/api/design-systems', (route) => route.fulfill({ json: SYSTEMS }));

        const slug = await createProject(page, `e2e-ds-${Date.now()}`);
        await openEditor(page, slug);

        // Baseline: the canvas Primary swatch before any system is applied.
        const primary = canvasButton(page, 'Primary');
        await expect(primary).toBeVisible({ timeout: 20_000 });
        const before = await primary.evaluate((el) => getComputedStyle(el).backgroundColor);

        // Open the gallery from the theme panel.
        await page.getByRole('button', { name: 'Browse design systems' }).click();
        const dialog = page.getByRole('dialog', { name: 'Design systems' });
        await expect(dialog).toBeVisible();

        // Every system renders, each with colour swatches drawn from its tokens.
        await expect(dialog.getByText('Playwright Emerald')).toBeVisible();
        await expect(dialog.getByText('Playwright Grape')).toBeVisible();
        expect(await dialog.locator('[data-swatch]').count()).toBeGreaterThan(0);

        // The search box filters the list by name.
        await dialog.getByPlaceholder('Search design systems').fill('Emerald');
        await expect(dialog.getByText('Playwright Grape')).toHaveCount(0);
        await expect(dialog.getByText('Playwright Emerald')).toBeVisible();

        // Applying a system as the theme reskins the canvas primary colour.
        await dialog
            .locator('[data-system="playwright-emerald"]')
            .getByRole('button', { name: 'Apply as theme' })
            .click();
        await page.waitForTimeout(500);

        const after = await primary.evaluate((el) => getComputedStyle(el).backgroundColor);
        expect(after).not.toBe(before);
    },
);
