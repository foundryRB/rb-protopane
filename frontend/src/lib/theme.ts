import type { Editor } from 'grapesjs';

/** Convert a #rrggbb hex string to the `H S% L%` triplet shadcn tokens use. */
export function hexToHsl(hex: string): string {
    const m = hex.replace('#', '');
    const r = parseInt(m.substring(0, 2), 16) / 255;
    const g = parseInt(m.substring(2, 4), 16) / 255;
    const b = parseInt(m.substring(4, 6), 16) / 255;
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const l = (max + min) / 2;
    const d = max - min;
    let h = 0;
    let s = 0;
    if (d !== 0) {
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        if (max === r) h = (g - b) / d + (g < b ? 6 : 0);
        else if (max === g) h = (b - r) / d + 2;
        else h = (r - g) / d + 4;
        h /= 6;
    }
    return `${Math.round(h * 360)} ${Math.round(s * 100)}% ${Math.round(l * 100)}%`;
}

/** Convert a `H S% L%` triplet back to #rrggbb (for the colour-input swatches). */
export function hslToHex(hsl: string): string {
    const m = hsl.trim().match(/^(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)%\s+(\d+(?:\.\d+)?)%$/);
    if (!m) return '#000000';
    const h = Number(m[1]) / 360;
    const s = Number(m[2]) / 100;
    const l = Number(m[3]) / 100;
    const k = (n: number) => (n + h * 12) % 12;
    const a = s * Math.min(l, 1 - l);
    const f = (n: number) => l - a * Math.max(-1, Math.min(k(n) - 3, 9 - k(n), 1));
    const toHex = (x: number) =>
        Math.round(x * 255)
            .toString(16)
            .padStart(2, '0');
    return `#${toHex(f(0))}${toHex(f(8))}${toHex(f(4))}`;
}

/** Slugify a display name into the storage/identity key a scheme is saved under. */
export function slugify(name: string, fallback = 'scheme'): string {
    return (
        name
            .toLowerCase()
            .normalize('NFKD')
            .replace(/[̀-ͯ]/g, '')
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '') || fallback
    );
}

export function canvasRoot(editor: Editor | null): HTMLElement | null {
    const doc = editor?.Canvas?.getDocument?.();
    return doc ? doc.documentElement : null;
}

/** Apply the customer's token to the prototype canvas. */
export function applyToken(editor: Editor | null, name: string, value: string): void {
    canvasRoot(editor)?.style.setProperty(name, value);
}

export function applyTokens(editor: Editor | null, tokens: Record<string, string>): void {
    for (const [name, value] of Object.entries(tokens)) applyToken(editor, name, value);
}

export const COLOR_FIELDS: { name: string; label: string }[] = [
    { name: '--primary', label: 'Primary' },
    { name: '--secondary', label: 'Secondary' },
    { name: '--accent', label: 'Accent' },
    { name: '--background', label: 'Background' },
    { name: '--foreground', label: 'Text' },
    { name: '--card', label: 'Card' },
    { name: '--border', label: 'Border' },
    { name: '--destructive', label: 'Destructive' },
];

// Default prototype tokens, matching the backend's DEFAULT_THEME_TOKENS.
export const DEFAULT_TOKENS: Record<string, string> = {
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

// Dark preview for the default prototype palette.
export const DARK_TOKENS: Record<string, string> = {
    '--background': '222 47% 11%',
    '--foreground': '210 40% 98%',
    '--card': '222 45% 13%',
    '--card-foreground': '210 40% 98%',
    '--primary': '217 91% 60%',
    '--primary-foreground': '222 47% 11%',
    '--secondary': '217 33% 18%',
    '--secondary-foreground': '210 40% 98%',
    '--muted': '217 33% 17%',
    '--muted-foreground': '215 20% 65%',
    '--accent': '217 33% 21%',
    '--accent-foreground': '210 40% 98%',
    '--destructive': '0 72% 51%',
    '--destructive-foreground': '210 40% 98%',
    '--border': '217 33% 24%',
    '--input': '217 33% 24%',
    '--ring': '217 91% 60%',
    '--radius': '0.5rem',
    '--font-sans': "ui-sans-serif, system-ui, 'Segoe UI', Roboto, sans-serif",
};

// Typography presets. The system stacks are offline-safe defaults; the webfont
// families are curated Google-hosted fonts (loaded into the canvas and the
// chrome) so the customer sees real brand type in the session. The exported
// theme records whichever family they pick; the frontend build self-hosts it
// (e.g. via Fontsource), so the pick survives handoff without the CDN.
export const FONT_PRESETS: Record<string, string> = {
    Modern: "ui-sans-serif, system-ui, 'Segoe UI', Roboto, sans-serif",
    Editorial: "Georgia, 'Times New Roman', Times, serif",
    Technical: "ui-monospace, 'Cascadia Code', Consolas, 'Courier New', monospace",
    'Baloo 2': "'Baloo 2', ui-sans-serif, system-ui, sans-serif",
    Nunito: "'Nunito', ui-sans-serif, system-ui, sans-serif",
    Poppins: "'Poppins', ui-sans-serif, system-ui, sans-serif",
    Fredoka: "'Fredoka', ui-sans-serif, system-ui, sans-serif",
    Playfair: "'Playfair Display', Georgia, serif",
    'Space Grotesk': "'Space Grotesk', ui-sans-serif, system-ui, sans-serif",
};

const scheme = (overrides: Record<string, string>): Record<string, string> => ({
    ...DEFAULT_TOKENS,
    ...overrides,
});

// Full colour schemes. Applying one replaces the whole palette, so every swatch and
// the whole canvas update, not just the primary accent.
export const PRESETS: Record<string, Record<string, string>> = {
    Blue: DEFAULT_TOKENS,
    Violet: scheme({
        '--primary': '262 83% 58%',
        '--ring': '262 83% 58%',
        '--accent': '262 60% 95%',
        '--accent-foreground': '262 45% 30%',
    }),
    Emerald: scheme({
        '--primary': '160 84% 39%',
        '--ring': '160 84% 39%',
        '--accent': '160 55% 94%',
        '--accent-foreground': '160 50% 22%',
    }),
    Rose: scheme({
        '--primary': '347 77% 50%',
        '--ring': '347 77% 50%',
        '--accent': '347 70% 95%',
        '--accent-foreground': '347 50% 32%',
    }),
    Amber: scheme({
        '--primary': '38 92% 50%',
        '--primary-foreground': '38 70% 12%',
        '--ring': '38 92% 50%',
        '--accent': '38 90% 94%',
        '--accent-foreground': '38 60% 25%',
    }),
    Slate: scheme({
        '--primary': '215 28% 25%',
        '--ring': '215 28% 25%',
        '--background': '210 20% 98%',
        '--secondary': '215 20% 92%',
        '--muted': '215 20% 92%',
        '--muted-foreground': '215 16% 40%',
        '--accent': '215 20% 90%',
        '--accent-foreground': '215 25% 22%',
        '--border': '215 20% 86%',
    }),
    Ocean: scheme({
        '--primary': '199 89% 42%',
        '--ring': '199 89% 42%',
        '--background': '200 60% 99%',
        '--card': '200 60% 99%',
        '--secondary': '199 45% 93%',
        '--secondary-foreground': '200 50% 18%',
        '--muted': '199 45% 93%',
        '--muted-foreground': '200 25% 42%',
        '--accent': '199 55% 90%',
        '--accent-foreground': '200 50% 18%',
        '--border': '199 35% 85%',
        '--input': '199 35% 85%',
    }),
    Ivory: scheme({
        '--primary': '25 70% 42%',
        '--ring': '25 70% 42%',
        '--background': '40 33% 98%',
        '--foreground': '24 30% 14%',
        '--card': '40 33% 99%',
        '--card-foreground': '24 30% 14%',
        '--secondary': '36 30% 92%',
        '--secondary-foreground': '24 30% 18%',
        '--muted': '36 30% 92%',
        '--muted-foreground': '30 15% 42%',
        '--accent': '36 40% 89%',
        '--accent-foreground': '24 30% 18%',
        '--border': '36 25% 84%',
        '--input': '36 25% 84%',
        '--radius': '0.75rem',
    }),
    Graphite: scheme({
        '--primary': '220 9% 18%',
        '--ring': '220 9% 18%',
        '--background': '0 0% 99%',
        '--secondary': '220 9% 93%',
        '--secondary-foreground': '220 9% 15%',
        '--muted': '220 9% 93%',
        '--muted-foreground': '220 6% 40%',
        '--accent': '220 9% 89%',
        '--accent-foreground': '220 9% 15%',
        '--border': '220 9% 84%',
        '--input': '220 9% 84%',
        '--radius': '0.375rem',
    }),
    Coral: scheme({
        '--primary': '11 82% 55%',
        '--ring': '11 82% 55%',
        '--background': '20 40% 99%',
        '--secondary': '15 45% 94%',
        '--secondary-foreground': '11 45% 22%',
        '--muted': '15 45% 94%',
        '--muted-foreground': '15 20% 45%',
        '--accent': '11 65% 92%',
        '--accent-foreground': '11 45% 22%',
        '--border': '15 30% 86%',
        '--input': '15 30% 86%',
        '--radius': '0.75rem',
    }),
};

/** Dark preview palette: the standard dark tokens, keeping the project's brand
 *  accent, radius, and typography. */
export function darkPalette(tokens: Record<string, string>): Record<string, string> {
    return {
        ...DARK_TOKENS,
        '--primary': tokens['--primary'] ?? DARK_TOKENS['--primary'],
        '--ring': tokens['--ring'] ?? DARK_TOKENS['--ring'],
        '--radius': tokens['--radius'] ?? DARK_TOKENS['--radius'],
        '--font-sans': tokens['--font-sans'] ?? DARK_TOKENS['--font-sans'],
    };
}
