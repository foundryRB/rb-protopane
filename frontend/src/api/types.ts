// Types mirroring the backend DTOs (protopane/adapters/inbound/http/dtos.py).
// Hand-typed for now; a follow-up can generate these from the FastAPI OpenAPI spec.
export interface ProjectSummary {
    slug: string;
    name: string;
    screen_count: number;
    archived: boolean;
}

export interface Screen {
    slug: string;
    name: string;
    html: string;
    css: string;
}

export interface Theme {
    tokens: Record<string, string>;
}

export interface Scheme {
    slug: string;
    name: string;
    tokens: Record<string, string>;
}

export interface Project {
    slug: string;
    name: string;
    archived: boolean;
    theme: Theme;
    screens: Screen[];
    schemes: Scheme[];
}

export interface TemplateSummary {
    slug: string;
    name: string;
    builtin: boolean;
}

export interface Template {
    slug: string;
    name: string;
    html: string;
    builtin: boolean;
}

export interface Block {
    slug: string;
    label: string;
    category: string;
    html: string;
    preview: string | null;
}

export interface DesignSystem {
    slug: string;
    name: string;
    category: string;
    tokens: Record<string, string>;
    guidance: string;
    source: string;
}
