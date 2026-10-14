import { expect } from '@playwright/test';
import { intent } from '@psa-department-of-engineering/playwright-intent';

import { canvasButton, createProject, openEditor } from './helpers';

intent('INT-PP-E03', 'selecting a preset reskins the canvas primary colour', async ({ page }) => {
    const slug = await createProject(page, `e2e-t03-${Date.now()}`);
    await openEditor(page, slug);
    const primary = canvasButton(page, 'Primary');
    await expect(primary).toBeVisible({ timeout: 20_000 });
    const before = await primary.evaluate((el) => getComputedStyle(el).backgroundColor);
    const studioBefore = await page
        .locator('body')
        .evaluate((el) => getComputedStyle(el).backgroundColor);

    await page.getByRole('button', { name: 'Violet' }).click();
    await page.waitForTimeout(500);

    const after = await primary.evaluate((el) => getComputedStyle(el).backgroundColor);
    expect(after).not.toBe(before);
    expect(await page.locator('body').evaluate((el) => getComputedStyle(el).backgroundColor)).toBe(
        studioBefore,
    );
    expect(
        await page.locator('html').evaluate((el) => el.style.getPropertyValue('--primary')),
    ).toBe('');
});

intent('INT-PP-E04', 'the Primary swatch reflects the active preset', async ({ page }) => {
    const slug = await createProject(page, `e2e-t04-${Date.now()}`);
    await openEditor(page, slug);
    await page.getByRole('button', { name: 'Violet' }).click();
    await page.waitForTimeout(300);

    const swatch = page.locator('label:has-text("Primary") input[type="color"]');
    const value = (await swatch.inputValue()).toLowerCase();
    expect(value).not.toBe('#3b82f6');
});

intent('INT-PP-E05', 'toggling dark mode darkens the canvas', async ({ page }) => {
    const slug = await createProject(page, `e2e-t05-${Date.now()}`);
    await openEditor(page, slug);
    const body = page.frameLocator('iframe.gjs-frame').locator('body');
    await expect(body).toBeVisible({ timeout: 20_000 });
    const light = await body.evaluate((el) => getComputedStyle(el).backgroundColor);

    await page.getByText('Dark mode').click();
    await page.waitForTimeout(400);

    const dark = await body.evaluate((el) => getComputedStyle(el).backgroundColor);
    expect(dark).not.toBe(light);
});

intent('INT-PP-E11', 'a preset applies a full scheme the swatches reflect', async ({ page }) => {
    const slug = await createProject(page, `e2e-t11-${Date.now()}`);
    await openEditor(page, slug);
    const background = page.locator('label:has-text("Background") input[type="color"]');
    const before = await background.inputValue();

    // Slate is a full scheme that changes the background, not just the primary accent.
    await page.getByRole('button', { name: 'Slate' }).click();
    await page.waitForTimeout(300);

    const after = await background.inputValue();
    expect(after).not.toBe(before);
});

intent('INT-PP-E16', 'a typography preset changes the canvas font live', async ({ page }) => {
    const slug = await createProject(page, `e2e-t16-${Date.now()}`);
    await openEditor(page, slug);
    const body = page.frameLocator('iframe.gjs-frame').locator('body');
    await expect(body).toBeVisible({ timeout: 20_000 });
    const before = await body.evaluate((el) => getComputedStyle(el).fontFamily);

    await page.getByRole('button', { name: 'Editorial' }).click();
    await page.waitForTimeout(400);

    const after = await body.evaluate((el) => getComputedStyle(el).fontFamily);
    expect(after).not.toBe(before);
    expect(after).toContain('Georgia');
});
