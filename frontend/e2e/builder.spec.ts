import { expect, type Page } from '@playwright/test';
import { intent } from '@psa-department-of-engineering/playwright-intent';
import type { Editor } from 'grapesjs';

import { canvasButton, createProject, openEditor } from './helpers';

// The editor instance the dev build exposes to tests (EditorPage's onReady).
type EditorWindow = Window & { __protopaneEditor?: Editor };

async function setCanvas(page: Page, html: string): Promise<void> {
    await page.evaluate((markup) => {
        (window as EditorWindow).__protopaneEditor?.setComponents(markup);
    }, html);
}

// Style one canvas element the way the Style Manager's controls do: select the element, let
// the Style Manager follow the selection and the device (it does so on the next tick), then
// add the style to its target, which is the rule for the device selected at that moment.
async function styleElement(page: Page, selector: string, style: Record<string, string>) {
    await page.evaluate(
        async ({ selector, style }) => {
            const editor = (window as EditorWindow).__protopaneEditor;
            const target = editor?.getWrapper()?.find(selector)[0];
            if (!editor || !target) throw new Error(`no canvas element matches ${selector}`);
            editor.select(target);
            await new Promise((resolve) => setTimeout(resolve));
            editor.StyleManager.addStyleTargets(style, {});
        },
        { selector, style },
    );
}

// Every style rule in the editor's getCss(), by selector: the media condition of each rule
// carrying that selector, '' for an unconditioned one.
async function ruleConditions(page: Page): Promise<Record<string, string[]>> {
    return page.evaluate(() => {
        const sheet = new CSSStyleSheet();
        sheet.replaceSync((window as EditorWindow).__protopaneEditor?.getCss() ?? '');
        const conditions: Record<string, string[]> = {};
        const record = (rule: CSSRule, condition: string) => {
            if (rule instanceof CSSStyleRule) {
                (conditions[rule.selectorText] ??= []).push(condition);
            }
        };
        for (const rule of Array.from(sheet.cssRules)) {
            if (rule instanceof CSSMediaRule) {
                for (const inner of Array.from(rule.cssRules)) record(inner, rule.conditionText);
            } else {
                record(rule, '');
            }
        }
        return conditions;
    });
}

intent(
    'INT-PP-E01',
    'opening a project mounts the builder and theme panel cleanly',
    async ({ page }) => {
        const errors: string[] = [];
        page.on('pageerror', (e) => errors.push(e.message));
        page.on('console', (m) => {
            if (m.type() === 'error') errors.push(m.text());
        });
        const slug = await createProject(page, `e2e-b01-${Date.now()}`);
        await openEditor(page, slug);
        await expect(page.getByText('Schemes', { exact: true })).toBeVisible();
        expect(errors, errors.join('\n')).toHaveLength(0);
    },
);

intent(
    'INT-PP-E02',
    'the canvas renders the screen with theme tokens applied',
    async ({ page }) => {
        const slug = await createProject(page, `e2e-b02-${Date.now()}`);
        await openEditor(page, slug);
        const primary = canvasButton(page, 'Primary');
        await expect(primary).toBeVisible({ timeout: 20_000 });
        const bg = await primary.evaluate((el) => getComputedStyle(el).backgroundColor);
        expect(bg).not.toBe('rgba(0, 0, 0, 0)');
        expect(bg).not.toBe('transparent');
    },
);

intent('INT-PP-E06', 'the block palette exposes shadcn component blocks', async ({ page }) => {
    const slug = await createProject(page, `e2e-b06-${Date.now()}`);
    await openEditor(page, slug);
    for (const name of ['Button', 'Card', 'Input', 'Badge']) {
        await expect(page.getByText(name, { exact: true }).first()).toBeVisible();
    }
});

intent(
    'INT-PP-E25',
    'the device switcher resizes the canvas, and it is the only one on the page',
    async ({ page }) => {
        const slug = await createProject(page, `e2e-b25-${Date.now()}`);
        await openEditor(page, slug);
        const frame = page.locator('iframe.gjs-frame');
        const width = () => frame.evaluate((el) => Math.round(el.getBoundingClientRect().width));
        await page.getByRole('button', { name: 'Tablet' }).click();
        await expect.poll(width).toBe(768);
        await page.getByRole('button', { name: 'Mobile' }).click();
        await expect.poll(width).toBe(390);
        // The switcher's three controls are the only device controls on the page: the
        // webpage preset's device panel is removed at init, since its phone icon selects
        // a device this editor does not define.
        const controls = page.getByRole('button', { name: /^(Desktop|Tablet|Mobile)$/ });
        await expect(controls).toHaveCount(3);
        await expect(page.locator('.gjs-pn-devices-c')).toHaveCount(0);
    },
);

intent(
    'INT-PP-E26',
    'a style set on Mobile is unconditioned; one set on Tablet or Desktop is under min-width 640px',
    async ({ page }) => {
        const slug = await createProject(page, `e2e-b26-${Date.now()}`);
        await openEditor(page, slug);
        await expect(page.frameLocator('iframe.gjs-frame').getByText('Welcome')).toBeVisible({
            timeout: 20_000,
        });
        await setCanvas(
            page,
            '<p id="on-desktop">Wide</p><p id="on-tablet">Mid</p><p id="on-mobile">Phone</p>',
        );

        // Desktop is the device the editor opens on.
        const selected = await page.evaluate(() =>
            (window as EditorWindow).__protopaneEditor?.Devices.getSelected()?.getName(),
        );
        expect(selected).toBe('Desktop');
        await styleElement(page, '#on-desktop', { 'font-size': '37px' });
        await page.getByRole('button', { name: 'Mobile' }).click();
        await styleElement(page, '#on-mobile', { 'font-size': '23px' });
        await page.getByRole('button', { name: 'Tablet' }).click();
        await styleElement(page, '#on-tablet', { 'font-size': '31px' });

        const conditions = await ruleConditions(page);
        expect(conditions['#on-mobile']).toEqual(['']);
        expect(conditions['#on-tablet']).toEqual(['(min-width: 640px)']);
        expect(conditions['#on-desktop']).toEqual(['(min-width: 640px)']);
    },
);

intent(
    'INT-PP-E27',
    'a saved style is applied in the canvas after a reload and survives the next save',
    async ({ page }) => {
        const slug = await createProject(page, `e2e-b27-${Date.now()}`);
        await openEditor(page, slug);
        const canvas = page.frameLocator('iframe.gjs-frame');
        await expect(canvas.getByText('Welcome')).toBeVisible({ timeout: 20_000 });
        await setCanvas(page, '<h1 id="kept">Kept</h1>');

        // A phone rule and a min-width rule on the same element.
        await page.getByRole('button', { name: 'Mobile' }).click();
        await styleElement(page, '#kept', { 'font-size': '23px' });
        await page.getByRole('button', { name: 'Tablet' }).click();
        await styleElement(page, '#kept', { 'font-size': '31px' });

        const save = async () => {
            await page.getByRole('button', { name: 'Save', exact: true }).click();
            await expect(page.getByRole('button', { name: 'Saved ✓' })).toBeVisible();
            const res = await page.request.get(`/api/projects/${slug}`);
            const project = (await res.json()) as { screens: { slug: string; css: string }[] };
            return project.screens.find((s) => s.slug === 'home')?.css ?? '';
        };
        const savedCss = await save();
        expect(savedCss).toContain('#kept');

        await page.reload();
        await expect(canvas.getByText('Kept')).toBeVisible({ timeout: 20_000 });
        const fontSize = () =>
            canvas.locator('#kept').evaluate((el) => getComputedStyle(el).fontSize);
        await page.getByRole('button', { name: 'Mobile' }).click();
        await expect.poll(fontSize).toBe('23px');
        await page.getByRole('button', { name: 'Tablet' }).click();
        await expect.poll(fontSize).toBe('31px');

        expect(await save()).toBe(savedCss);
    },
);

intent(
    'INT-PP-E29',
    'a style attribute in loaded markup applies at every width and survives a save and reload',
    async ({ page }) => {
        const slug = await createProject(page, `e2e-b29-${Date.now()}`);
        // The screen's markup carries its own style, the way a template or an agent writes it.
        const res = await page.request.put(`/api/projects/${slug}/screens/home`, {
            data: { name: 'Home', html: '<p style="font-size: 29px">Inline</p>', css: '' },
        });
        expect(res.ok()).toBeTruthy();

        // The editor opens on Desktop, so the markup loads while Desktop is selected.
        await openEditor(page, slug);
        const canvas = page.frameLocator('iframe.gjs-frame');
        await expect(canvas.getByText('Inline')).toBeVisible({ timeout: 20_000 });
        const fontSize = () =>
            canvas.getByText('Inline').evaluate((el) => getComputedStyle(el).fontSize);
        const width = () =>
            page
                .locator('iframe.gjs-frame')
                .evaluate((el) => Math.round(el.getBoundingClientRect().width));
        // Measure on Mobile only once the canvas is at phone width.
        const onMobile = async () => {
            await page.getByRole('button', { name: 'Mobile' }).click();
            await expect.poll(width).toBe(390);
            return fontSize();
        };
        await expect.poll(fontSize).toBe('29px');
        expect(await onMobile()).toBe('29px');

        await page.getByRole('button', { name: 'Save', exact: true }).click();
        await expect(page.getByRole('button', { name: 'Saved ✓' })).toBeVisible();
        await page.reload();
        await expect(canvas.getByText('Inline')).toBeVisible({ timeout: 20_000 });
        expect(await onMobile()).toBe('29px');
    },
);
