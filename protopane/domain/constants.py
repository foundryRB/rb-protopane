from __future__ import annotations

# Default shadcn light-theme token values. Mirrors the frontend's src/index.css :root,
# so a new project opens on-brand-neutral until the customer's theme is applied.
DEFAULT_THEME_TOKENS: dict[str, str] = {
    "--background": "0 0% 100%",
    "--foreground": "222 47% 11%",
    "--card": "0 0% 100%",
    "--card-foreground": "222 47% 11%",
    "--primary": "217 91% 60%",
    "--primary-foreground": "0 0% 100%",
    "--secondary": "210 40% 96%",
    "--secondary-foreground": "222 47% 11%",
    "--muted": "210 40% 96%",
    "--muted-foreground": "215 16% 47%",
    "--accent": "210 40% 94%",
    "--accent-foreground": "222 47% 11%",
    "--destructive": "0 72% 51%",
    "--destructive-foreground": "0 0% 100%",
    "--border": "214 32% 88%",
    "--input": "214 32% 88%",
    "--ring": "217 91% 60%",
    "--radius": "0.5rem",
    "--font-sans": "ui-sans-serif, system-ui, 'Segoe UI', Roboto, sans-serif",
}

# Slug of the screen every new project starts with.
DEFAULT_SCREEN_SLUG = "home"
DEFAULT_SCREEN_NAME = "Home"
