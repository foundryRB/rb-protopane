import { useEffect, useRef } from 'react';
import grapesjs, { type Editor as GrapesEditor } from 'grapesjs';
import * as presetWebpageNs from 'grapesjs-preset-webpage';
import 'grapesjs/dist/css/grapes.min.css';
import '@/grapes-overrides.css';

import { api } from '@/api/client';
import { registerBlocks } from '@/blocks';

// grapesjs-preset-webpage is double-wrapped ({ default: { default: fn } }) once the
// bundler interops its CommonJS, so unwrap nested `default` keys to the plugin fn.
function unwrapDefault(mod: unknown): unknown {
    let cur = mod;
    while (cur && typeof cur === 'object' && 'default' in cur) {
        cur = (cur as { default: unknown }).default;
    }
    return cur;
}
const presetWebpage = unwrapDefault(presetWebpageNs) as (
    editor: GrapesEditor,
    opts: object,
) => void;

// The canvas iframe loads a self-hosted Tailwind runtime + our token config +
// the token stylesheet, so dropped shadcn markup renders themed. It also loads a
// curated Google-hosted webfont sheet so the customer sees real brand type when
// they pick a webfont preset: the one online dependency the canvas takes, and a
// deliberate trade for typography fidelity in the session. The system-stack
// presets still render with no network, and the exported theme is unaffected.
const FONT_CSS =
    'https://fonts.googleapis.com/css2?family=Baloo+2:wght@400;700&family=Fredoka:wght@400;600&family=Nunito:wght@400;700&family=Playfair+Display:wght@400;700&family=Poppins:wght@400;600&family=Space+Grotesk:wght@400;700&display=swap';
const CANVAS = {
    scripts: ['/vendor/tailwind-play.js', '/canvas/tw-config.js'],
    styles: ['/canvas/theme.css', FONT_CSS],
};

// Style-manager sectors deliberately carry no color properties: colors come from
// the design tokens (the theme panel), never from per-element styling, so every
// screen stays reskinnable and passes the backend's token-discipline gate.
const STYLE_SECTORS = [
    {
        name: 'Spacing',
        open: false,
        buildProps: ['width', 'height', 'min-height', 'margin', 'padding'],
    },
    {
        name: 'Layout',
        open: false,
        buildProps: ['display', 'flex-direction', 'justify-content', 'align-items', 'gap'],
    },
    {
        name: 'Typography',
        open: false,
        buildProps: ['font-size', 'font-weight', 'letter-spacing', 'line-height', 'text-align'],
    },
    {
        name: 'Corners',
        open: false,
        buildProps: ['border-radius'],
    },
];

// The device preview reads mobile-first, on the house phone line (Tailwind's `sm`, 640px),
// the way the utility classes in the markup read. Mobile is a 390px canvas whose style edits
// write unconditioned rules: the phone layout. Tablet (a 768px canvas) and Desktop (the full
// canvas width) both write under `@media (min-width: 640px)`. The editor opens on Desktop.
const DEVICES = [
    { id: 'desktop', name: 'Desktop', width: '', widthMedia: '640px' },
    { id: 'tablet', name: 'Tablet', width: '768px', widthMedia: '640px' },
    { id: 'mobile', name: 'Mobile', width: '390px', widthMedia: '' },
];

export function Editor({ onReady }: { onReady: (editor: GrapesEditor) => void }) {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const editorRef = useRef<GrapesEditor | null>(null);

    useEffect(() => {
        if (!containerRef.current || editorRef.current) return;
        const editor = grapesjs.init({
            container: containerRef.current,
            height: '100%',
            storageManager: false,
            fromElement: false,
            canvas: CANVAS,
            styleManager: { sectors: STYLE_SECTORS },
            mediaCondition: 'min-width',
            deviceManager: { default: 'desktop', devices: DEVICES },
            plugins: [(ed: GrapesEditor) => presetWebpage(ed, {})],
        });
        // The webpage preset ships its own device panel (three icons above the canvas)
        // whose phone icon selects GrapesJS's default 'Mobile portrait', a device the
        // DEVICES list above does not define. The switcher in EditorPage is the one
        // device control, so the preset's panel is removed.
        editor.Panels.removePanel('devices-c');
        api.listBlocks()
            .then((blocks) => registerBlocks(editor, blocks))
            .catch(() => {
                // Palette stays empty when the API is unreachable; the canvas still works.
            });
        editorRef.current = editor;
        onReady(editor);
        return () => {
            editor.destroy();
            editorRef.current = null;
        };
    }, [onReady]);

    return <div ref={containerRef} className="h-full" />;
}
