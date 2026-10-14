import { useEffect, useRef, useState } from 'react';

import { api } from '@/api/client';
import type { ProjectSummary, Scheme } from '@/api/types';
import { Button } from '@/components/ui/button';
import { COLOR_FIELDS, FONT_PRESETS, PRESETS, hexToHsl, hslToHex } from '@/lib/theme';

interface ThemePanelProps {
    slug: string;
    tokens: Record<string, string>;
    setToken: (name: string, value: string) => void;
    applyScheme: (tokens: Record<string, string>) => void;
    schemes: Scheme[];
    onSaveScheme: (name: string) => void;
    onDeleteScheme: (schemeSlug: string) => void;
    onBrowseDesignSystems: () => void;
    dark: boolean;
    setDark: (next: boolean) => void;
}

/** Parse a token set out of an exported theme: a `:root { --x: y; }` block or a JSON map. */
function parseThemeTokens(text: string): Record<string, string> {
    const trimmed = text.trim();
    if (trimmed.startsWith('{')) {
        try {
            const obj = JSON.parse(trimmed) as Record<string, unknown>;
            const out: Record<string, string> = {};
            for (const [name, value] of Object.entries(obj)) {
                if (name.startsWith('--') && typeof value === 'string') out[name] = value;
            }
            return out;
        } catch {
            // not JSON; fall through to CSS parsing
        }
    }
    const out: Record<string, string> = {};
    const declaration = /(--[\w-]+)\s*:\s*([^;]+);/g;
    let match: RegExpExecArray | null;
    while ((match = declaration.exec(text)) !== null) {
        out[match[1]] = match[2].trim();
    }
    return out;
}

export function ThemePanel({
    slug,
    tokens,
    setToken,
    applyScheme,
    schemes,
    onSaveScheme,
    onDeleteScheme,
    onBrowseDesignSystems,
    dark,
    setDark,
}: ThemePanelProps) {
    const [projects, setProjects] = useState<ProjectSummary[]>([]);
    const [schemeName, setSchemeName] = useState('');
    const fileRef = useRef<HTMLInputElement | null>(null);

    useEffect(() => {
        api.listProjects()
            .then(setProjects)
            .catch(() => setProjects([]));
    }, []);

    function exportTheme(): void {
        const lines = Object.entries(tokens).map(([name, value]) => `  ${name}: ${value};`);
        const css = `:root {\n${lines.join('\n')}\n}\n`;
        const url = URL.createObjectURL(new Blob([css], { type: 'text/css' }));
        const a = document.createElement('a');
        a.href = url;
        a.download = `${slug || 'theme'}-theme.css`;
        a.click();
        URL.revokeObjectURL(url);
    }

    async function importTheme(file: File): Promise<void> {
        const parsed = parseThemeTokens(await file.text());
        if (Object.keys(parsed).length > 0) applyScheme({ ...tokens, ...parsed });
    }

    async function copyFrom(otherSlug: string): Promise<void> {
        if (!otherSlug) return;
        const project = await api.getProject(otherSlug);
        applyScheme({ ...tokens, ...project.theme.tokens });
    }

    const radius = parseFloat(tokens['--radius'] ?? '0.5');
    const others = projects.filter((p) => p.slug !== slug);

    return (
        <div className="flex h-full flex-col overflow-y-auto text-sm text-foreground">
            <div className="border-b px-4 py-3">
                <div className="font-semibold">Theme</div>
                <div className="text-xs text-muted-foreground">Reskins the canvas live.</div>
            </div>

            <div className="flex flex-col gap-5 p-4">
                <section>
                    <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                        Schemes
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                        {Object.entries(PRESETS).map(([name, palette]) => (
                            <button
                                key={name}
                                type="button"
                                onClick={() => applyScheme(palette)}
                                className="inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs transition-colors hover:bg-accent"
                            >
                                <span
                                    className="h-2.5 w-2.5 rounded-full"
                                    style={{ backgroundColor: `hsl(${palette['--primary']})` }}
                                />
                                {name}
                            </button>
                        ))}
                    </div>
                    <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={onBrowseDesignSystems}
                        className="mt-2 w-full"
                    >
                        Browse design systems
                    </Button>
                </section>

                <section className="border-t pt-4">
                    <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                        Project schemes
                    </div>
                    {schemes.length > 0 ? (
                        <div className="mb-2 flex flex-wrap gap-1.5">
                            {schemes.map((s) => (
                                <span
                                    key={s.slug}
                                    className="inline-flex items-center gap-1 rounded-md border py-1 pl-2.5 pr-1 text-xs"
                                >
                                    <button
                                        type="button"
                                        onClick={() => applyScheme(s.tokens)}
                                        title={`Apply ${s.name}`}
                                        className="inline-flex items-center gap-1.5 hover:text-foreground"
                                    >
                                        <span
                                            className="h-2.5 w-2.5 rounded-full"
                                            style={{ backgroundColor: `hsl(${s.tokens['--primary']})` }}
                                        />
                                        {s.name}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => onDeleteScheme(s.slug)}
                                        aria-label={`Delete ${s.name}`}
                                        title={`Delete ${s.name}`}
                                        className="px-1 text-muted-foreground hover:text-destructive"
                                    >
                                        &times;
                                    </button>
                                </span>
                            ))}
                        </div>
                    ) : (
                        <div className="mb-2 text-xs text-muted-foreground">
                            Save the current palette as a reusable scheme for this project.
                        </div>
                    )}
                    <div className="flex gap-1.5">
                        <input
                            type="text"
                            value={schemeName}
                            onChange={(e) => setSchemeName(e.target.value)}
                            placeholder="New scheme name"
                            className="min-w-0 flex-1 rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                        />
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => {
                                const name = schemeName.trim();
                                if (name) {
                                    onSaveScheme(name);
                                    setSchemeName('');
                                }
                            }}
                        >
                            Save scheme
                        </Button>
                    </div>
                </section>

                {others.length > 0 && (
                    <section className="border-t pt-4">
                        <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                            Copy theme from
                        </div>
                        <select
                            value=""
                            onChange={(e) => void copyFrom(e.target.value)}
                            className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                        >
                            <option value="">Select a project...</option>
                            {others.map((p) => (
                                <option key={p.slug} value={p.slug}>
                                    {p.name}
                                </option>
                            ))}
                        </select>
                    </section>
                )}

                <section className="border-t pt-4">
                    <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                        Colours
                    </div>
                    <div className="flex flex-col gap-1.5">
                        {COLOR_FIELDS.map((field) => {
                            const hex = hslToHex(tokens[field.name] ?? '0 0% 0%');
                            return (
                                <label key={field.name} className="flex items-center gap-2">
                                    <span>{field.label}</span>
                                    <span className="ml-auto flex items-center gap-2">
                                        <span className="font-mono text-[11px] text-muted-foreground">
                                            {hex}
                                        </span>
                                        <input
                                            type="color"
                                            value={hex}
                                            onChange={(e) => setToken(field.name, hexToHsl(e.target.value))}
                                            className="h-7 w-10 cursor-pointer rounded border bg-transparent"
                                        />
                                    </span>
                                </label>
                            );
                        })}
                    </div>
                </section>

                <section className="border-t pt-4">
                    <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                        Typography
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                        {Object.entries(FONT_PRESETS).map(([name, stack]) => (
                            <button
                                key={name}
                                type="button"
                                onClick={() => setToken('--font-sans', stack)}
                                style={{ fontFamily: stack }}
                                className={
                                    'inline-flex items-center rounded-md border px-2.5 py-1 text-xs ' +
                                    'transition-colors hover:bg-accent ' +
                                    (tokens['--font-sans'] === stack
                                        ? 'border-link bg-accent text-foreground'
                                        : '')
                                }
                            >
                                {name}
                            </button>
                        ))}
                    </div>
                </section>

                <section className="border-t pt-4">
                    <div className="mb-2 flex items-center justify-between text-xs font-medium uppercase tracking-wide text-muted-foreground">
                        <span>Radius</span>
                        <span className="font-mono normal-case">{radius.toFixed(2)}rem</span>
                    </div>
                    <input
                        type="range"
                        min={0}
                        max={1.5}
                        step={0.05}
                        value={radius}
                        onChange={(e) => setToken('--radius', `${e.target.value}rem`)}
                        className="w-full"
                    />
                </section>

                <section className="border-t pt-4">
                    <label className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            checked={dark}
                            onChange={(e) => setDark(e.target.checked)}
                        />
                        Dark mode
                    </label>
                </section>
            </div>

            <div className="mt-auto flex gap-2 border-t p-4">
                <Button type="button" onClick={exportTheme} variant="outline" className="flex-1">
                    Export
                </Button>
                <Button
                    type="button"
                    onClick={() => fileRef.current?.click()}
                    variant="outline"
                    className="flex-1"
                >
                    Import
                </Button>
                <input
                    ref={fileRef}
                    type="file"
                    accept=".css,.json,text/css,application/json"
                    className="hidden"
                    onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) void importTheme(file);
                        e.target.value = '';
                    }}
                />
            </div>
        </div>
    );
}
