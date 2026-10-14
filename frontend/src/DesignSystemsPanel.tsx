import { useEffect, useState } from 'react';

import { api } from '@/api/client';
import type { DesignSystem } from '@/api/types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

interface DesignSystemsPanelProps {
    /** Close the gallery overlay. */
    onClose: () => void;
    /** Apply a system's tokens as the project's theme (reskins the canvas live). */
    onApplyTheme: (tokens: Record<string, string>) => void;
    /** Save a system as a named, reusable project scheme. */
    onSaveScheme: (name: string, tokens: Record<string, string>) => void;
}

// The swatches that preview a system at a glance, drawn straight from its tokens.
const SWATCHES: { name: string; label: string }[] = [
    { name: '--background', label: 'Background' },
    { name: '--foreground', label: 'Text' },
    { name: '--primary', label: 'Primary' },
    { name: '--accent', label: 'Accent' },
    { name: '--border', label: 'Border' },
];

function matches(system: DesignSystem, query: string): boolean {
    const q = query.trim().toLowerCase();
    if (!q) return true;
    return system.name.toLowerCase().includes(q) || system.category.toLowerCase().includes(q);
}

/**
 * Browse the read-only design-system library and seed the project from it: apply a
 * reference palette as the live theme, or keep it as a named project scheme. The tokens
 * are the same canonical set a theme carries, so both actions drive the existing save flows.
 */
export function DesignSystemsPanel({ onClose, onApplyTheme, onSaveScheme }: DesignSystemsPanelProps) {
    const [systems, setSystems] = useState<DesignSystem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [query, setQuery] = useState('');
    const [expanded, setExpanded] = useState<string | null>(null);
    const [saved, setSaved] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        api.listDesignSystems()
            .then((list) => {
                if (!cancelled) setSystems(list);
            })
            .catch((e) => {
                if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load systems');
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });
        return () => {
            cancelled = true;
        };
    }, []);

    // Escape closes the overlay, matching a dialog's expected keyboard affordance.
    useEffect(() => {
        function onKey(e: KeyboardEvent): void {
            if (e.key === 'Escape') onClose();
        }
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [onClose]);

    const filtered = systems.filter((s) => matches(s, query));

    function apply(system: DesignSystem): void {
        onApplyTheme(system.tokens);
        onClose();
    }

    function save(system: DesignSystem): void {
        onSaveScheme(system.name, system.tokens);
        setSaved(system.slug);
        setTimeout(() => setSaved((current) => (current === system.slug ? null : current)), 2000);
    }

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/40 p-4"
            onClick={onClose}
        >
            <div
                role="dialog"
                aria-modal="true"
                aria-label="Design systems"
                className="flex max-h-[85vh] w-full max-w-4xl flex-col rounded-lg border bg-background text-foreground shadow-lg"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex flex-col gap-3 border-b p-4">
                    <div className="flex items-start justify-between gap-3">
                        <div>
                            <div className="font-semibold">Design systems</div>
                            <div className="text-xs text-muted-foreground">
                                Browse reference palettes and seed this project from one.
                            </div>
                        </div>
                        <Button type="button" size="sm" variant="ghost" onClick={onClose}>
                            Close
                        </Button>
                    </div>
                    <Input
                        type="search"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search design systems"
                        aria-label="Search design systems"
                    />
                </div>

                <div className="min-h-0 flex-1 overflow-y-auto p-4">
                    {loading ? (
                        <div className="text-sm text-muted-foreground">Loading systems...</div>
                    ) : error ? (
                        <div className="text-sm text-destructive">{error}</div>
                    ) : filtered.length === 0 ? (
                        <div className="text-sm text-muted-foreground">
                            No systems match &ldquo;{query}&rdquo;.
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                            {filtered.map((system) => (
                                <Card key={system.slug} data-system={system.slug} className="p-4">
                                    <div className="flex flex-col gap-3">
                                        <div className="flex items-start justify-between gap-2">
                                            <div className="min-w-0">
                                                <div className="truncate font-medium">
                                                    {system.name}
                                                </div>
                                                <div className="truncate text-xs text-muted-foreground">
                                                    {system.source}
                                                </div>
                                            </div>
                                            <Badge variant="secondary" className="shrink-0">
                                                {system.category}
                                            </Badge>
                                        </div>

                                        <div className="flex gap-1.5">
                                            {SWATCHES.map((swatch) => (
                                                <span
                                                    key={swatch.name}
                                                    data-swatch={swatch.name}
                                                    title={swatch.label}
                                                    className="h-7 w-7 rounded border"
                                                    style={{
                                                        background: `hsl(${system.tokens[swatch.name] ?? '0 0% 85%'})`,
                                                    }}
                                                />
                                            ))}
                                        </div>

                                        <div className="flex flex-wrap gap-2">
                                            <Button
                                                type="button"
                                                size="sm"
                                                onClick={() => apply(system)}
                                            >
                                                Apply as theme
                                            </Button>
                                            <Button
                                                type="button"
                                                size="sm"
                                                variant="outline"
                                                onClick={() => save(system)}
                                            >
                                                {saved === system.slug ? 'Saved' : 'Save as scheme'}
                                            </Button>
                                            {system.guidance && (
                                                <Button
                                                    type="button"
                                                    size="sm"
                                                    variant="ghost"
                                                    onClick={() =>
                                                        setExpanded((current) =>
                                                            current === system.slug
                                                                ? null
                                                                : system.slug,
                                                        )
                                                    }
                                                    className="text-muted-foreground"
                                                >
                                                    {expanded === system.slug
                                                        ? 'Hide guidance'
                                                        : 'Guidance'}
                                                </Button>
                                            )}
                                        </div>

                                        {expanded === system.slug && system.guidance && (
                                            <pre className="max-h-48 overflow-y-auto whitespace-pre-wrap rounded-md bg-muted p-3 font-sans text-xs text-muted-foreground">
                                                {system.guidance}
                                            </pre>
                                        )}
                                    </div>
                                </Card>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
