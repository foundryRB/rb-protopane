import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '@/api/client';
import type { ProjectSummary, TemplateSummary } from '@/api/types';
import { Appearance } from '@/views/Appearance';
import { Logo } from '@/components/Brand';
import { Lockup } from '@/components/Lockup';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

function ConnectAgent() {
    const [copied, setCopied] = useState(false);
    const [credential, setCredential] = useState<string | null>(null);

    // Fill this site's real HTTP Basic credential into the one-liner, fetched from
    // /api/agent-credential (reachable only by an already-authenticated caller). If
    // it is unavailable (unconfigured -> 503), fall back to the placeholder so the
    // command shape is still copyable.
    useEffect(() => {
        let cancelled = false;
        api.getAgentCredential()
            .then((r) => {
                if (!cancelled) setCredential(r.credential);
            })
            .catch(() => {
                if (!cancelled) setCredential(null);
            });
        return () => {
            cancelled = true;
        };
    }, []);

    const basic = credential ?? '<credential>';
    const command =
        `claude mcp add --scope user --transport http protopane ${window.location.origin}/mcp ` +
        `--header "Authorization: Basic ${basic}"`;

    async function copy() {
        await navigator.clipboard.writeText(command);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    }

    return (
        <Card className="mt-8 p-4" data-testid="connect-agent">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <div className="text-sm font-medium">Connect an agent (MCP)</div>
                    <p className="mt-1 text-xs text-muted-foreground">
                        This instance serves its project tools over the Model Context Protocol. An
                        agent can create projects, refine themes, and author screens here.
                    </p>
                </div>
                <Button type="button" size="sm" variant="outline" onClick={copy}>
                    {copied ? 'Copied' : 'Copy command'}
                </Button>
            </div>
            <code className="mt-3 block overflow-x-auto whitespace-nowrap rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
                {command}
            </code>
        </Card>
    );
}

export function ProjectListPage() {
    const [projects, setProjects] = useState<ProjectSummary[]>([]);
    const [templates, setTemplates] = useState<TemplateSummary[]>([]);
    const [name, setName] = useState('');
    const [template, setTemplate] = useState('');
    const [renamingSlug, setRenamingSlug] = useState<string | null>(null);
    const [renameDraft, setRenameDraft] = useState('');
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        api.listProjects(true)
            .then(setProjects)
            .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load projects'));
        api.listTemplates()
            .then(setTemplates)
            .catch(() => setTemplates([]));
    }, []);

    async function create() {
        try {
            const project = await api.createProject(
                name.trim() || 'Untitled',
                template || undefined,
            );
            navigate(`/p/${project.slug}`);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Create failed');
        }
    }

    async function remove(slug: string) {
        await api.deleteProject(slug);
        setProjects((current) => current.filter((p) => p.slug !== slug));
    }

    function startRename(project: ProjectSummary) {
        setRenamingSlug(project.slug);
        setRenameDraft(project.name);
    }

    async function commitRename(slug: string) {
        try {
            const renamed = await api.renameProject(slug, { newName: renameDraft });
            setProjects((current) =>
                current.map((p) => (p.slug === slug ? { ...p, name: renamed.name } : p)),
            );
            setRenamingSlug(null);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Rename failed');
        }
    }

    async function setArchived(slug: string, archived: boolean) {
        try {
            await (archived ? api.archiveProject(slug) : api.unarchiveProject(slug));
            setProjects((current) =>
                current.map((p) => (p.slug === slug ? { ...p, archived } : p)),
            );
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Archive failed');
        }
    }

    async function removeTemplate(slug: string) {
        await api.deleteTemplate(slug);
        setTemplates((current) => current.filter((t) => t.slug !== slug));
        setTemplate((current) => (current === slug ? '' : current));
    }

    const savedTemplates = templates.filter((t) => !t.builtin);
    const active = projects.filter((p) => !p.archived);
    const archived = projects.filter((p) => p.archived);

    return (
        <div className="min-h-screen text-foreground">
            <header className="border-b bg-card/40">
                <div className="app-frame app-header">
                    {/* The corporate identity, with the product name alongside. */}
                    <span className="dark:hidden"><Lockup mode="light" height={36} /></span>
                    <span className="hidden dark:block"><Lockup mode="dark" height={36} /></span>
                    <div className="flex flex-col leading-tight">
                        <span className="text-base font-semibold tracking-tight">protopane</span>
                        <span className="text-xs text-muted-foreground">Design studio</span>
                    </div>
                    <div className="ml-auto flex flex-wrap items-center justify-end gap-4">
                        {active.length > 0 && (
                            <span className="text-xs text-muted-foreground">
                                {active.length} project{active.length === 1 ? '' : 's'}
                                {archived.length > 0 ? ` (+${archived.length} archived)` : ''}
                            </span>
                        )}
                        <Appearance />
                    </div>
                </div>
            </header>

            <main className="app-frame app-main">
                <Card className="mb-8 p-4">
                    <div className="mb-3 text-sm font-medium">Start a new prototype</div>
                    <div className="flex flex-wrap items-end gap-3">
                        <div className="flex flex-col gap-1">
                            <span className="text-xs text-muted-foreground">Project name</span>
                            <Input
                                placeholder="New project name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') void create();
                                }}
                                className="w-64"
                            />
                        </div>
                        <div className="flex flex-col gap-1">
                            <span className="text-xs text-muted-foreground">Start from</span>
                            <select
                                aria-label="Template"
                                value={template}
                                onChange={(e) => setTemplate(e.target.value)}
                                className="h-9 rounded-md border border-input bg-background px-2 text-sm"
                            >
                                <option value="">Blank</option>
                                {templates.map((t) => (
                                    <option key={t.slug} value={t.slug}>
                                        {t.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <Button type="button" onClick={create}>
                            New project
                        </Button>
                    </div>
                    {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
                    {savedTemplates.length > 0 && (
                        <div className="mt-4 border-t pt-3">
                            <div className="mb-2 text-xs text-muted-foreground">
                                Saved templates (built-ins are permanent)
                            </div>
                            <div className="flex flex-wrap gap-1.5">
                                {savedTemplates.map((t) => (
                                    <span
                                        key={t.slug}
                                        className="inline-flex items-center gap-1 rounded-full border bg-secondary px-2.5 py-0.5 text-xs text-secondary-foreground"
                                    >
                                        {t.name}
                                        <button
                                            type="button"
                                            onClick={() => void removeTemplate(t.slug)}
                                            title={`Delete template ${t.name}`}
                                            aria-label={`Delete template ${t.name}`}
                                            className="text-muted-foreground hover:text-destructive"
                                        >
                                            &times;
                                        </button>
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                </Card>

                {active.length === 0 ? (
                    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-center">
                        <Logo className="h-12 w-12 opacity-70" />
                        <p className="mt-4 text-sm font-medium">No prototypes yet</p>
                        <p className="mt-1 text-xs text-muted-foreground">
                            Create your first project above to start designing.
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        {active.map((p) => (
                            <Card
                                key={p.slug}
                                data-slug={p.slug}
                                className="overflow-hidden transition-shadow hover:shadow-md"
                            >
                                <div className="h-1.5 bg-primary/80" />
                                <div className="flex flex-col gap-3 p-4">
                                    {renamingSlug === p.slug ? (
                                        <div className="flex items-center gap-2">
                                            <Input
                                                aria-label={`New name for ${p.slug}`}
                                                value={renameDraft}
                                                autoFocus
                                                onChange={(e) => setRenameDraft(e.target.value)}
                                                onKeyDown={(e) => {
                                                    if (e.key === 'Enter')
                                                        void commitRename(p.slug);
                                                    if (e.key === 'Escape') setRenamingSlug(null);
                                                }}
                                                className="h-8"
                                            />
                                            <Button
                                                type="button"
                                                size="sm"
                                                onClick={() => commitRename(p.slug)}
                                            >
                                                Save name
                                            </Button>
                                        </div>
                                    ) : (
                                        <div>
                                            <div className="font-medium">{p.name}</div>
                                            <div className="text-xs text-muted-foreground">
                                                {p.screen_count} screen
                                                {p.screen_count === 1 ? '' : 's'}
                                            </div>
                                        </div>
                                    )}
                                    <div className="flex gap-2">
                                        <Button
                                            type="button"
                                            size="sm"
                                            onClick={() => navigate(`/p/${p.slug}`)}
                                        >
                                            Open
                                        </Button>
                                        <Button
                                            type="button"
                                            size="sm"
                                            variant="ghost"
                                            onClick={() => startRename(p)}
                                            className="text-muted-foreground"
                                        >
                                            Rename
                                        </Button>
                                        <Button
                                            type="button"
                                            size="sm"
                                            variant="ghost"
                                            onClick={() => setArchived(p.slug, true)}
                                            className="text-muted-foreground"
                                        >
                                            Archive
                                        </Button>
                                        <Button
                                            type="button"
                                            size="sm"
                                            variant="ghost"
                                            onClick={() => remove(p.slug)}
                                            className="text-muted-foreground hover:text-destructive"
                                        >
                                            Delete
                                        </Button>
                                    </div>
                                </div>
                            </Card>
                        ))}
                    </div>
                )}

                {archived.length > 0 && (
                    <section className="mt-10" data-testid="archived-projects">
                        <h2 className="mb-3 text-sm font-medium text-muted-foreground">
                            Archived ({archived.length})
                        </h2>
                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                            {archived.map((p) => (
                                <Card
                                    key={p.slug}
                                    data-slug={p.slug}
                                    className="overflow-hidden opacity-70"
                                >
                                    <div className="h-1.5 bg-muted" />
                                    <div className="flex flex-col gap-3 p-4">
                                        <div>
                                            <div className="font-medium">{p.name}</div>
                                            <div className="text-xs text-muted-foreground">
                                                {p.screen_count} screen
                                                {p.screen_count === 1 ? '' : 's'} &middot; archived
                                            </div>
                                        </div>
                                        <div className="flex gap-2">
                                            <Button
                                                type="button"
                                                size="sm"
                                                variant="outline"
                                                onClick={() => setArchived(p.slug, false)}
                                            >
                                                Unarchive
                                            </Button>
                                            <Button
                                                type="button"
                                                size="sm"
                                                variant="ghost"
                                                onClick={() => remove(p.slug)}
                                                className="text-muted-foreground hover:text-destructive"
                                            >
                                                Delete
                                            </Button>
                                        </div>
                                    </div>
                                </Card>
                            ))}
                        </div>
                    </section>
                )}

                <ConnectAgent />
            </main>
        </div>
    );
}
