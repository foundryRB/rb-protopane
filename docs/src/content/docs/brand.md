---
title: Visual identity
id: DOC-BRAND-001
type: Reference
status: Active
updated: "2026-09-13"
summary: The Vodafone Portugal Digital identity in the studio; each prototype keeps its own design system.
---

ProtoPane's studio wears the Vodafone Portugal Digital identity: the lockup as the one mark in its headers, the brand's red as the primary and the ambient field's colour, a near-black stage in dark and paper in light, the brand face for text. Each prototype carries its selected design system inside the canvas and in exported tokens and markup.

## Appearance ownership

| Surface | Source |
| --- | --- |
| Studio palette, typography and spacing | `frontend/src/index.css`, `frontend/tailwind.config.js` |
| Header lockup | `frontend/src/components/Lockup.tsx` |
| The mark on its own, and the browser mark | `frontend/src/components/Brand.tsx`, `frontend/public/favicon.svg` |
| Continuous side fields and particles | `frontend/src/views/AmbientField.tsx` |
| Persisted Light/Dark studio preference | `frontend/src/views/Appearance.tsx`, `frontend/index.html` |
| Prototype token application | `frontend/src/lib/theme.ts`, applied to the canvas iframe |
| Editor controls | `frontend/src/grapes-overrides.css` |

The project list uses a 1120px frame with responsive gutters. Ambient fields and rising, fading particles run in both appearances, pause on hidden pages, stop for reduced motion and are hidden for printing. The editor's canvas and controls use their full working area with opaque surfaces.

The project theme and its dark preview belong to the prototype. Changing a prototype palette preserves the studio's PSA controls. Saved and exported themes retain the customer's tokens, typography and guidance.
