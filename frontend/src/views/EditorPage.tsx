import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import type { Editor as GrapesEditor } from 'grapesjs';

import { api } from '@/api/client';
import type { Project, Screen, TemplateSummary } from '@/api/types';
import { Lockup } from '@/components/Lockup';
import { Button } from '@/components/ui/button';
import { ChatPanel } from '@/ChatPanel';
import { DesignSystemsPanel } from '@/DesignSystemsPanel';
import { Editor } from '@/Editor';
import { ThemePanel } from '@/ThemePanel';
import { DEFAULT_TOKENS, applyTokens, darkPalette, slugify } from '@/lib/theme';

export function EditorPage() {
    const { slug = '' } = useParams();
    const [project, setProject] = useState<Project | null>(null);
    const [tokens, setTokens] = useState<Record<string, string>>(DEFAULT_TOKENS);
    const [dark, setDark] = useState(false);
    const [editorReady, setEditorReady] = useState(false);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [templateSaved, setTemplateSaved] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [chatEnabled, setChatEnabled] = useState(false);
    const [galleryOpen, setGalleryOpen] = useState(false);
    const [templates, setTemplates] = useState<TemplateSummary[]>([]);
    // The pages of the project. The canvas holds the live HTML for the active page; the
    // other pages keep their last-captured HTML here until saved.
    const [screens, setScreens] = useState<Screen[]>([]);
    const [activeIndex, setActiveIndex] = useState(0);
    const editorRef = useRef<GrapesEditor | null>(null);
    const paletteRef = useRef<Record<string, string>>(tokens);
    const agentActiveRef = useRef(false);
    const loadedRef = useRef(false);
    const savedTimeoutRef = useRef<number | null>(null);
    // The last-known-persisted content per page (by slug), for the refresh dirty-check.
    // Keyed off the round-tripped html/css the editor itself produces (GrapesJS re-serializes
    // on load, so comparing against the raw server string would always read as "dirty").
    const baselineRef = useRef<Map<string, Screen>>(new Map());

    // The effective palette: the saved light theme, or a dark preview built from it.
    const palette = useMemo(() => (dark ? darkPalette(tokens) : tokens), [tokens, dark]);

    useEffect(() => {
        loadedRef.current = false;
        api.getProject(slug)
            .then((loaded) => {
                setProject(loaded);
                setTokens({ ...DEFAULT_TOKENS, ...loaded.theme.tokens });
                setScreens(
                    loaded.screens.length
                        ? loaded.screens
                        : [{ slug: 'home', name: 'Home', html: '', css: '' }],
                );
                setActiveIndex(0);
            })
            .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load project'));
    }, [slug]);

    // Apply the prototype palette whenever it changes or the editor mounts.
    useEffect(() => {
        paletteRef.current = palette;
        applyTokens(editorRef.current, palette);
    }, [palette, editorReady]);

    // Load a page's markup and its rules into the canvas, on an empty rule set so no page's
    // rules carry into the page loaded after it. The rules the markup carries itself stay:
    // GrapesJS turns each style attribute into an id rule filed under the selected device's
    // media, and an inline style applies at every width, so the markup loads in device preview
    // mode, which files those rules unconditioned. The page's saved rules go in after them.
    // getCss() leads with the editor's protected base CSS, which the canvas applies on its own;
    // that prefix stays out of the rules, so loading and saving a page writes the same CSS back.
    const loadScreen = useCallback((target: Pick<Screen, 'html' | 'css'> | undefined) => {
        const editor = editorRef.current;
        if (!editor) return;
        const config = editor.getConfig();
        const css = target?.css ?? '';
        const base = config.protectedCss ?? '';
        const previewMode = config.devicePreviewMode;
        editor.Css.clear();
        config.devicePreviewMode = true;
        try {
            editor.setComponents(target?.html ?? '');
        } finally {
            config.devicePreviewMode = previewMode;
        }
        editor.addStyle(base && css.startsWith(base) ? css.slice(base.length) : css);
    }, []);

    // Snapshot the round-tripped content of the page just loaded into the canvas as its
    // dirty-check baseline: GrapesJS re-serializes the markup and rules it loads, so the
    // baseline must be read back from the editor rather than the raw server strings, or every
    // page would read as "dirty" the moment it is loaded, even with no edits.
    const primeBaseline = useCallback((target: Screen | undefined) => {
        if (!target) return;
        const editor = editorRef.current;
        if (!editor) return;
        baselineRef.current.set(target.slug, {
            ...target,
            html: editor.getHtml(),
            css: editor.getCss() ?? '',
        });
    }, []);

    // Load the active page into the canvas once, when both the editor and pages are ready.
    useEffect(() => {
        if (editorReady && !loadedRef.current && screens.length > 0) {
            loadedRef.current = true;
            baselineRef.current = new Map(screens.map((s) => [s.slug, s]));
            const target = screens[activeIndex];
            loadScreen(target);
            primeBaseline(target);
        }
    }, [editorReady, screens, activeIndex, loadScreen, primeBaseline]);

    // Capture the live canvas back into the active page (before switching, adding, or saving).
    const captureActive = useCallback((): Screen[] => {
        const editor = editorRef.current;
        if (!editor || screens.length === 0) return screens;
        const next = screens.slice();
        const current = next[activeIndex];
        if (current) {
            next[activeIndex] = { ...current, html: editor.getHtml(), css: editor.getCss() ?? '' };
        }
        return next;
    }, [screens, activeIndex]);

    const switchTo = useCallback(
        (index: number) => {
            if (index === activeIndex) return;
            const captured = captureActive();
            setScreens(captured);
            setActiveIndex(index);
            const target = captured[index];
            loadScreen(target);
            primeBaseline(target);
        },
        [activeIndex, captureActive, loadScreen, primeBaseline],
    );

    const addPage = useCallback(() => {
        const captured = captureActive();
        const slugs = new Set(captured.map((s) => s.slug));
        let n = captured.length + 1;
        while (slugs.has(`page-${n}`)) n++;
        const page: Screen = {
            slug: `page-${n}`,
            name: `Page ${n}`,
            html: '<section class="p-8"></section>',
            css: '',
        };
        setScreens([...captured, page]);
        setActiveIndex(captured.length);
        loadScreen(page);
    }, [captureActive, loadScreen]);

    const renamePage = useCallback(
        (index: number) => {
            const target = screens[index];
            if (!target) return;
            const name = window.prompt('Page name', target.name)?.trim();
            if (name) {
                setScreens((current) => current.map((s, i) => (i === index ? { ...s, name } : s)));
            }
        },
        [screens],
    );

    const deletePage = useCallback(
        (index: number) => {
            if (screens.length <= 1) return;
            const target = screens[index];
            if (!target || !window.confirm(`Delete page "${target.name}"?`)) return;
            const captured = captureActive().filter((_, i) => i !== index);
            const nextActive = Math.min(
                index < activeIndex ? activeIndex - 1 : activeIndex,
                captured.length - 1,
            );
            setScreens(captured);
            setActiveIndex(nextActive);
            const nextTarget = captured[nextActive];
            loadScreen(nextTarget);
            primeBaseline(nextTarget);
            // A page that was never saved has nothing server-side; ignore that 404.
            api.deleteScreen(slug, target.slug).catch(() => {});
        },
        [screens, activeIndex, captureActive, slug, loadScreen, primeBaseline],
    );

    const [device, setDeviceState] = useState('Desktop');
    const setDevice = useCallback((name: string) => {
        setDeviceState(name);
        editorRef.current?.setDevice(name);
    }, []);

    // Refetch the project so the canvas + theme reflect a server-side change (agent edits).
    const reloadFromServer = useCallback(async () => {
        const loaded = await api.getProject(slug);
        setTokens({ ...DEFAULT_TOKENS, ...loaded.theme.tokens });
        setProject(loaded);
        setScreens(loaded.screens);
        baselineRef.current = new Map(loaded.screens.map((s) => [s.slug, s]));
        const target = loaded.screens[activeIndex] ?? loaded.screens[0];
        if (target) loadScreen(target);
        primeBaseline(target);
    }, [slug, activeIndex, loadScreen, primeBaseline]);

    // Clear the pending "Saved" cue reset if the page unmounts mid-timeout.
    useEffect(() => {
        return () => {
            if (savedTimeoutRef.current !== null) window.clearTimeout(savedTimeoutRef.current);
        };
    }, []);

    // Discover whether the local design chat is enabled (it is off on the hosted hub).
    useEffect(() => {
        api.getConfig()
            .then((c) => setChatEnabled(c.chatEnabled))
            .catch(() => setChatEnabled(false));
    }, []);

    // Templates the operator can drop onto the current page while working (undo restores).
    useEffect(() => {
        api.listTemplates()
            .then(setTemplates)
            .catch(() => setTemplates([]));
    }, []);

    // Live reload: when the agent saves, the server emits a change event; refresh the canvas.
    useEffect(() => {
        if (!editorReady) return;
        const events = new EventSource(`/api/projects/${slug}/events`);
        events.addEventListener('change', () => {
            if (agentActiveRef.current) void reloadFromServer();
        });
        return () => events.close();
    }, [slug, editorReady, reloadFromServer]);

    const setToken = useCallback((name: string, value: string) => {
        setTokens((current) => ({ ...current, [name]: value }));
    }, []);

    // Apply a full colour scheme (preset): replace the whole palette so every swatch
    // updates. Colour schemes carry no typographic opinion, so the chosen font stays.
    const applyScheme = useCallback((next: Record<string, string>) => {
        setTokens((current) => ({
            ...next,
            '--font-sans': next['--font-sans'] ?? current['--font-sans'],
        }));
    }, []);

    // Save the current palette as a named scheme on this project, so it becomes a
    // one-click button for the rest of the session (and future ones).
    const saveScheme = useCallback(
        async (name: string) => {
            try {
                setProject(await api.saveScheme(slug, slugify(name), name, tokens));
            } catch (e) {
                setError(e instanceof Error ? e.message : 'Save scheme failed');
            }
        },
        [slug, tokens],
    );

    // Apply a design system as the project's theme: reskin the canvas live (the same
    // mechanism as a scheme switch) and persist it through the theme-save call.
    const applyDesignSystem = useCallback(
        async (dsTokens: Record<string, string>) => {
            applyScheme(dsTokens);
            try {
                setProject(await api.saveTheme(slug, dsTokens));
            } catch (e) {
                setError(e instanceof Error ? e.message : 'Apply design system failed');
            }
        },
        [slug, applyScheme],
    );

    // Keep a design system as a named project scheme, through the same call the schemes UI uses.
    const saveDesignSystemScheme = useCallback(
        async (name: string, dsTokens: Record<string, string>) => {
            try {
                setProject(await api.saveScheme(slug, slugify(name), name, dsTokens));
            } catch (e) {
                setError(e instanceof Error ? e.message : 'Save scheme failed');
            }
        },
        [slug],
    );

    const deleteScheme = useCallback(
        async (schemeSlug: string) => {
            try {
                setProject(await api.deleteScheme(slug, schemeSlug));
            } catch (e) {
                setError(e instanceof Error ? e.message : 'Delete scheme failed');
            }
        },
        [slug],
    );

    // Replace the current page's content with a template; the operator can undo or save. A
    // template is markup only, so the rules of the content it replaces go with that content.
    const applyTemplate = useCallback(
        async (templateSlug: string) => {
            if (!templateSlug) return;
            const template = await api.getTemplate(templateSlug);
            loadScreen({ html: template.html, css: '' });
        },
        [loadScreen],
    );

    const onReady = useCallback((editor: GrapesEditor) => {
        editorRef.current = editor;
        // Test hook: expose the editor so e2e tests can drive canvas edits.
        if (import.meta.env.DEV) {
            const w = window as unknown as { __protopaneEditor?: GrapesEditor };
            w.__protopaneEditor = editor;
        }
        // The canvas iframe loads async; re-apply the palette whenever it (re)loads.
        editor.on('canvas:frame:load', () => applyTokens(editor, paletteRef.current));
        setEditorReady(true);
    }, []);

    async function save() {
        if (!project) return;
        setSaving(true);
        setSaved(false);
        setError(null);
        if (savedTimeoutRef.current !== null) {
            window.clearTimeout(savedTimeoutRef.current);
            savedTimeoutRef.current = null;
        }
        try {
            const captured = captureActive();
            setScreens(captured);
            // Save the light theme (the brand), not the dark preview, then every page.
            await api.saveTheme(slug, tokens);
            for (const screen of captured) {
                await api.saveScreen(slug, screen.slug, screen.name, screen.html, screen.css);
            }
            baselineRef.current = new Map(captured.map((s) => [s.slug, s]));
            setSaved(true);
            savedTimeoutRef.current = window.setTimeout(() => setSaved(false), 2000);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Save failed');
        } finally {
            setSaving(false);
        }
    }

    async function refresh() {
        if (!project) return;
        // Refresh overwrites every page from the server; gate it like deletePage's other
        // destructive action when any page - not just the active one - has in-progress edits
        // it would silently drop. switchTo/addPage/deletePage all capture a left-behind page's
        // live edits into local `screens` state without persisting them, so every captured page
        // must be checked against its own last-known-persisted baseline, not just the active one.
        const captured = captureActive();
        const dirty = captured.some((s) => {
            const base = baselineRef.current.get(s.slug);
            return !base || s.html !== base.html || s.css !== base.css;
        });
        if (dirty && !window.confirm('Refresh will discard unsaved changes. Continue?')) {
            return;
        }
        setRefreshing(true);
        setError(null);
        try {
            await reloadFromServer();
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Refresh failed');
        } finally {
            setRefreshing(false);
        }
    }

    async function saveAsTemplate() {
        if (!project) return;
        setError(null);
        try {
            await api.saveTemplate(project.name, editorRef.current?.getHtml() ?? '');
            setTemplateSaved(true);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Save as template failed');
        }
    }

    return (
        <div className="app-editor flex h-screen flex-col">
            <header className="flex items-center gap-3 border-b bg-card px-4 py-2 text-sm text-foreground">
                {/* The wordmark anchors the editor. */}
                <Link to="/" className="flex items-center gap-2 hover:opacity-80">
                    <span className="dark:hidden"><Lockup mode="light" height={32} /></span>
                    <span className="hidden dark:block"><Lockup mode="dark" height={32} /></span>
                    <span className="font-semibold tracking-tight">protopane</span>
                </Link>
                <span className="text-muted-foreground">/</span>
                <span className="font-medium">{project?.name ?? slug}</span>
                <span className="rounded-full border px-2 py-0.5 text-xs text-muted-foreground">
                    Prototype
                </span>
                {error && <span className="text-destructive">{error}</span>}
                <div className="ml-auto flex gap-2">
                    {templates.length > 0 && (
                        <select
                            value=""
                            onChange={(e) => {
                                void applyTemplate(e.target.value);
                                e.target.value = '';
                            }}
                            disabled={!editorReady}
                            title="Replace the current page with a template"
                            className="rounded-md border border-input bg-background px-2 text-sm"
                        >
                            <option value="">Apply template...</option>
                            {templates.map((t) => (
                                <option key={t.slug} value={t.slug}>
                                    {t.name}
                                </option>
                            ))}
                        </select>
                    )}
                    <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => editorRef.current?.runCommand('core:undo')}
                        disabled={!editorReady}
                    >
                        Undo
                    </Button>
                    <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => editorRef.current?.runCommand('core:redo')}
                        disabled={!editorReady}
                    >
                        Redo
                    </Button>
                    <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={saveAsTemplate}
                        disabled={!project}
                    >
                        {templateSaved ? 'Saved as template' : 'Save as template'}
                    </Button>
                    <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={refresh}
                        disabled={refreshing || !project}
                        title="Reload the latest saved theme and pages from the server"
                    >
                        {refreshing ? 'Refreshing...' : 'Refresh'}
                    </Button>
                    <Button type="button" size="sm" onClick={save} disabled={saving || !project}>
                        {saving ? 'Saving...' : saved ? 'Saved ✓' : 'Save'}
                    </Button>
                </div>
            </header>
            <div className="flex min-h-0 flex-1">
                <aside className="w-72 shrink-0 border-r bg-background">
                    <ThemePanel
                        slug={slug}
                        tokens={tokens}
                        setToken={setToken}
                        applyScheme={applyScheme}
                        schemes={project?.schemes ?? []}
                        onSaveScheme={saveScheme}
                        onDeleteScheme={deleteScheme}
                        onBrowseDesignSystems={() => setGalleryOpen(true)}
                        dark={dark}
                        setDark={setDark}
                    />
                </aside>
                <main className="flex min-w-0 flex-1 flex-col">
                    <div className="flex items-center gap-1 overflow-x-auto border-b bg-card px-2 py-1">
                        {screens.map((screen, index) => (
                            <span
                                key={screen.slug}
                                className={
                                    'flex shrink-0 items-center rounded-md transition-colors ' +
                                    (index === activeIndex
                                        ? 'bg-accent font-medium text-foreground'
                                        : 'text-muted-foreground hover:text-foreground')
                                }
                            >
                                <button
                                    type="button"
                                    onClick={() => switchTo(index)}
                                    onDoubleClick={() => renamePage(index)}
                                    title="Double-click to rename"
                                    className="px-3 py-1 text-sm"
                                >
                                    {screen.name}
                                </button>
                                {index === activeIndex && screens.length > 1 && (
                                    <button
                                        type="button"
                                        onClick={() => deletePage(index)}
                                        title="Delete this page"
                                        aria-label={`Delete page ${screen.name}`}
                                        className="pr-2 text-muted-foreground hover:text-destructive"
                                    >
                                        &times;
                                    </button>
                                )}
                            </span>
                        ))}
                        <button
                            type="button"
                            onClick={addPage}
                            disabled={!editorReady}
                            title="Add a page"
                            className="shrink-0 rounded-md px-2 py-1 text-sm text-muted-foreground hover:text-foreground"
                        >
                            + Page
                        </button>
                        <div className="ml-auto flex shrink-0 items-center gap-1 rounded-lg bg-muted p-0.5 text-xs">
                            {['Desktop', 'Tablet', 'Mobile'].map((name) => (
                                <button
                                    key={name}
                                    type="button"
                                    onClick={() => setDevice(name)}
                                    disabled={!editorReady}
                                    title={`Preview at ${name.toLowerCase()} width`}
                                    className={
                                        'rounded-md px-2 py-1 transition-colors ' +
                                        (device === name
                                            ? 'bg-background font-medium text-foreground shadow-sm'
                                            : 'text-muted-foreground hover:text-foreground')
                                    }
                                >
                                    {name}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="min-h-0 flex-1">
                        <Editor onReady={onReady} />
                    </div>
                </main>
                {chatEnabled && (
                    <aside className="w-80 shrink-0 border-l bg-background">
                        <ChatPanel
                            slug={slug}
                            onBeforeSend={save}
                            onAgentActive={(active) => {
                                agentActiveRef.current = active;
                            }}
                        />
                    </aside>
                )}
            </div>
            {galleryOpen && (
                <DesignSystemsPanel
                    onClose={() => setGalleryOpen(false)}
                    onApplyTheme={applyDesignSystem}
                    onSaveScheme={saveDesignSystemScheme}
                />
            )}
        </div>
    );
}
