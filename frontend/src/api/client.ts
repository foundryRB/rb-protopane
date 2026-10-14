import type {
    Block,
    DesignSystem,
    Project,
    ProjectSummary,
    Template,
    TemplateSummary,
} from './types';

const BASE = '/api';

async function unwrap<T>(res: Response): Promise<T> {
    if (!res.ok) {
        let detail = `${res.status} ${res.statusText}`;
        try {
            const body = (await res.json()) as { detail?: string };
            detail = body.detail ?? detail;
        } catch {
            // non-JSON error body; keep the status text
        }
        throw new Error(detail);
    }
    return res.json() as Promise<T>;
}

const jsonInit = (method: string, body: unknown): RequestInit => ({
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
});

export const api = {
    getConfig: () => fetch(`${BASE}/config`).then((r) => unwrap<{ chatEnabled: boolean }>(r)),

    getAgentCredential: () =>
        fetch(`${BASE}/agent-credential`).then((r) => unwrap<{ credential: string }>(r)),

    listProjects: (includeArchived = false) =>
        fetch(`${BASE}/projects${includeArchived ? '?include_archived=true' : ''}`).then((r) =>
            unwrap<ProjectSummary[]>(r),
        ),

    createProject: (name: string, template?: string) =>
        fetch(`${BASE}/projects`, jsonInit('POST', { name, template })).then((r) =>
            unwrap<Project>(r),
        ),

    getProject: (slug: string) => fetch(`${BASE}/projects/${slug}`).then((r) => unwrap<Project>(r)),

    deleteProject: async (slug: string) => {
        const res = await fetch(`${BASE}/projects/${slug}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(`Failed to delete ${slug}: ${res.status}`);
    },

    renameProject: (slug: string, changes: { newSlug?: string; newName?: string }) =>
        fetch(
            `${BASE}/projects/${slug}/rename`,
            jsonInit('POST', { new_slug: changes.newSlug, new_name: changes.newName }),
        ).then((r) => unwrap<Project>(r)),

    archiveProject: (slug: string) =>
        fetch(`${BASE}/projects/${slug}/archive`, { method: 'POST' }).then((r) =>
            unwrap<Project>(r),
        ),

    unarchiveProject: (slug: string) =>
        fetch(`${BASE}/projects/${slug}/unarchive`, { method: 'POST' }).then((r) =>
            unwrap<Project>(r),
        ),

    saveTheme: (slug: string, tokens: Record<string, string>) =>
        fetch(`${BASE}/projects/${slug}/theme`, jsonInit('PUT', { tokens })).then((r) =>
            unwrap<Project>(r),
        ),

    saveScheme: (slug: string, schemeSlug: string, name: string, tokens: Record<string, string>) =>
        fetch(
            `${BASE}/projects/${slug}/schemes/${schemeSlug}`,
            jsonInit('PUT', { name, tokens }),
        ).then((r) => unwrap<Project>(r)),

    deleteScheme: (slug: string, schemeSlug: string) =>
        fetch(`${BASE}/projects/${slug}/schemes/${schemeSlug}`, { method: 'DELETE' }).then((r) =>
            unwrap<Project>(r),
        ),

    saveScreen: (slug: string, screenSlug: string, name: string, html: string, css: string) =>
        fetch(
            `${BASE}/projects/${slug}/screens/${screenSlug}`,
            jsonInit('PUT', { name, html, css }),
        ).then((r) => unwrap<Project>(r)),

    deleteScreen: (slug: string, screenSlug: string) =>
        fetch(`${BASE}/projects/${slug}/screens/${screenSlug}`, { method: 'DELETE' }).then((r) =>
            unwrap<Project>(r),
        ),

    listTemplates: () => fetch(`${BASE}/templates`).then((r) => unwrap<TemplateSummary[]>(r)),

    getTemplate: (slug: string) =>
        fetch(`${BASE}/templates/${slug}`).then((r) => unwrap<Template>(r)),

    saveTemplate: (name: string, html: string) =>
        fetch(`${BASE}/templates`, jsonInit('POST', { name, html })).then((r) =>
            unwrap<Template>(r),
        ),

    deleteTemplate: async (slug: string) => {
        const res = await fetch(`${BASE}/templates/${slug}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(`Failed to delete template ${slug}: ${res.status}`);
    },

    listBlocks: () => fetch(`${BASE}/blocks`).then((r) => unwrap<Block[]>(r)),

    listDesignSystems: () =>
        fetch(`${BASE}/design-systems`).then((r) => unwrap<DesignSystem[]>(r)),
};
