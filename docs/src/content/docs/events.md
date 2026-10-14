---
title: Events
id: DOC-PROTOPANE-003
type: Reference
status: Active
updated: "2026-08-22"
summary: "The facts protopane states on the platform event bus: one row per type under the prototyping domain it owns, with the subject and the pointers each carries. The consumer's contract, held equal to the publisher by a test."
---

protopane owns the `prototyping` domain on the platform's event bus by its own grant (the platform's `onboard-events` guide), and states one fact per act that changes a project. This page is the contract a consumer reads: the types, what each is about, and what `data` carries. It is held equal to the publisher's constants by the test suite (`tests/test_event_publishing.py`), so a row here is a type the hub emits and nothing else is.

Every event is a CloudEvent with `source` `/foundry/protopane` and `datacontenttype` `application/json`. Each carries the project slug and the identity of the screen, scheme, or theme it is about, never a screen's markup or a theme's token values: the instance stays the store, and a consumer fetches from it by slug. Publishing is one-way (`REF-Events` section 6): a publish that cannot be delivered is dropped and logged, and no save or export depends on the broker, which `INT-PP-B35` attests for every act below.

The bus fact is distinct from the live-view signal. A save still fans out to the editors watching that one project over SSE (the refresh signal of `REF-Realtime`); the event below is the platform-wide statement that the save happened, for readers that were never watching.

## The types

| Type | `subject` | Published when | `data` |
|---|---|---|---|
| `com.foundry.prototyping.project.created` | the project slug | a project is created, from a template or the starter screen | `project`, `template` (slug or null) |
| `com.foundry.prototyping.theme.saved` | the project slug | a project's theme tokens are saved | `project`, `design_system` (slug or null), `tokens` (count) |
| `com.foundry.prototyping.scheme.saved` | the project slug | a colour scheme is created or updated | `project`, `scheme` |
| `com.foundry.prototyping.scheme.deleted` | the project slug | a colour scheme is removed | `project`, `scheme` |
| `com.foundry.prototyping.screen.saved` | the project slug | a screen is created or updated | `project`, `screen` |
| `com.foundry.prototyping.screen.deleted` | the project slug | a screen is removed | `project`, `screen` |
| `com.foundry.prototyping.project.exported` | the project slug | a project's theme and screens are exported for handoff | `project`, `screens` (count) |
| `com.foundry.prototyping.project.renamed` | the new slug | a project's slug or display name changes | `project`, `previous`, `name_changed` |
| `com.foundry.prototyping.project.archived` | the project slug | a project leaves the active listing | `project` |
| `com.foundry.prototyping.project.unarchived` | the project slug | a project returns to the active listing | `project` |
| `com.foundry.prototyping.project.deleted` | the project slug | a project is removed | `project` |

## What is not stated

Reads (listing, fetching a project, listing blocks, templates, or design systems) change nothing and state nothing. The template library is a hub asset rather than a project, so saving or deleting a template states nothing. A save the token discipline refuses persisted nothing, so nothing is stated for it.

Adding a type is one change to this page and to `protopane/application/events.py` together; the test refuses either alone.
