import type { Editor } from 'grapesjs';

import type { Block } from '@/api/types';

// The palette registers the instance's served block vocabulary (GET /api/blocks):
// the backend owns the markup, so the SPA palette, the REST API, and MCP agents all
// build screens from the same token-backed set. `preview` (defaulting to the html)
// renders a themed thumbnail, so dragging shows the real component, reskinned live.
export function registerBlocks(editor: Editor, blocks: Block[]): void {
    const bm = editor.BlockManager;
    for (const b of blocks) {
        bm.add(b.slug, {
            label: b.label,
            category: b.category,
            media: `<div class="pp-prev">${b.preview ?? b.html}</div>`,
            content: b.html,
        });
    }
}
